import logging
import random
from datetime import timedelta
from pathlib import Path

from anyio import Path as AsyncPath, TemporaryDirectory
from telegram import Update
from telegram.ext import ContextTypes

from config import settings
from database.manager import DatabaseManager
from database.models.chat import ChatStatus
from database.repositories.chat import ChatRepository
from helpers.telegram import get_prompt_template_values
from keyboards.approve import approve_chat_keyboard
from services.admin_notifier import AdminNotifier
from services.animation_service import AnimationService
from services.chat_service import ChatService
from services.exceptions.gemini import GeminiError
from services.gemini_caption_generator import MemeCaption
from texts.messages import AdminMessages
from utils.parse import parse_user_caption

logger = logging.getLogger(__name__)

_MAX_INPUT_FILE_SIZE = 20_000_000
_MAX_OUTPUT_FILE_SIZE = 50_000_000
_MAX_DURATION_SECONDS = 30
_WRITE_TIMEOUT = 60


async def _render_and_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    caption: MemeCaption | None,
) -> None:
    """
    Универсальный хелпер для рендеринга анимации для публичного и приватного хандлера.
    """

    message = update.message

    if message is None or message.animation is None:
        return

    animation = message.animation
    chat_id = message.chat.id
    message_id = message.message_id
    mode = "ai" if caption is None else "custom"
    template_values = get_prompt_template_values(message) if caption is None else {}

    is_private = message.chat.type == "private"
    file_size = animation.file_size

    duration = animation.duration
    # duration может быть int или timedelta,
    # по этому нужно привести их к единому типа float.
    seconds = (
        duration.total_seconds() if isinstance(duration, timedelta) else float(duration)
    )

    if seconds <= 0 or seconds > _MAX_DURATION_SECONDS:
        logger.debug(
            "Skipping animation: chat_id: %s message_id: %s duration: %.3fs limit: %ss",
            chat_id,
            message_id,
            seconds,
            _MAX_DURATION_SECONDS,
        )
        if is_private:
            # Отправляет сообщение только в привате.
            await message.reply_text(f"Нужна анимация до {_MAX_DURATION_SECONDS} сек")
        return

    # Теоеграм иногда заранее сообщает размер файла.
    # file_size имеет тип int | None.
    #
    # Если размер известен и больше лимита,
    # нет смысла его скачивать.
    if file_size is not None and file_size > _MAX_INPUT_FILE_SIZE:
        logger.debug(
            "Skipping oversized animation: chat_id=%s message_id=%s bytes=%s limit=%s",
            chat_id,
            message_id,
            file_size,
            _MAX_INPUT_FILE_SIZE,
        )
        if is_private:
            await message.reply_text("Слишком большой вес анимации")
        return

    service: AnimationService = context.bot_data["animation_service"]

    logger.info(
        "Processing animation: chat_id=%s message_id=%s mode=%s duration=%.3fs",
        chat_id,
        message_id,
        mode,
        seconds,
    )

    try:
        # Создаем временную директорию.
        #
        # После выхода из async with она будет автоматически удалена.
        async with TemporaryDirectory(prefix="meme-animation-") as directory:
            workdir = Path(directory)
            # Путь куда сохраняем исходную анимацию.
            source = workdir / "source"

            # Скачиваем файл
            telegram_file = await animation.get_file()
            data_bytes = await telegram_file.download_as_bytearray()

            logger.debug(
                "Downloaded animation: chat_id=%s message_id=%s bytes=%s",
                chat_id,
                message_id,
                len(data_bytes),
            )

            # Даже если телега не сообщила точный размер файла
            # после скачивания мы можем вычислить его.
            if len(data_bytes) > _MAX_INPUT_FILE_SIZE:
                logger.debug(
                    "Downloaded animation exceeds limit: "
                    "chat_id=%s message_id=%s bytes=%s",
                    chat_id,
                    message_id,
                    len(data_bytes),
                )
                if is_private:
                    await message.reply_text("Файл больше 20мб")
                return

            # Записываем баты во временный файл.
            # Используется AsyncPath чтобы запись не блокировала event loop.
            await AsyncPath(source).write_bytes(data_bytes)

            # Освобожлаем пямят.
            del data_bytes

            logger.info(
                "Generating animation meme: chat_id=%s message_id=%s mode=%s",
                chat_id,
                message_id,
                mode,
            )
            # Если caption None то генерирует подпись через Gemini.
            # Генерирует видео и сохраняет в source.
            # Возвращается путь к итоговому видео.
            result = await service.create_meme(
                source=source,
                workdir=workdir,
                duration=seconds,
                caption=caption,
                template_values=template_values,
            )

            # Проверяет размер видео ПЕРЕД отправкой
            result_size = (await AsyncPath(result).stat()).st_size

            if result_size > _MAX_OUTPUT_FILE_SIZE:
                logger.warning(
                    "Animation output exceeds limit: chat_id=%s message_id=%s "
                    "bytes=%s limit=%s",
                    chat_id,
                    message_id,
                    result_size,
                    _MAX_OUTPUT_FILE_SIZE,
                )
                if is_private:
                    await message.reply_text(
                        "Результат получился слишокм большим для отправки"
                    )
                return

            # Читаем mp4 файл в память
            video = await AsyncPath(result).read_bytes()

            logger.debug(
                "Sending animation meme: chat_id=%s message_id=%s bytes=%s",
                chat_id,
                message_id,
                result_size,
            )
            # А теперь отправляем обратно в ТГ
            await message.reply_animation(
                animation=video,
                filename="meme.mp4",
                write_timeout=_WRITE_TIMEOUT,
            )
    except GeminiError as exc:
        logger.warning(
            "Animation caption generation failed: chat_id=%s message_id=%s error=%s",
            chat_id,
            message_id,
            type(exc).__name__,
            exc_info=True,
        )

        if is_private:
            await message.reply_text("Не удалось сгенерить подпись")

        notifier = AdminNotifier(context.bot, settings.admin_ids)
        await notifier.send(
            text=AdminMessages.error(
                exc,
                update=update,
                title=f"Ошибка Gemini: {type(exc).__name__}",
            )
        )

        return
    except OSError, RuntimeError, TimeoutError, ValueError:
        logger.exception(
            "Animation processing failed: chat_id=%s message_id=%s mode=%s",
            chat_id,
            message_id,
            mode,
        )

        if is_private:
            await message.reply_text("Не удалось обработать анимацию")

        return

    logger.info(
        "Sent animation meme: chat_id=%s message_id=%s mode=%s bytes=%s",
        chat_id,
        message_id,
        mode,
        result_size,
    )


async def handle_public_animation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Обработчик для приватного чата с ботом.
    """

    message, chat = update.message, update.effective_chat

    if message is None or chat is None or message.animation is None:
        return

    db: DatabaseManager = context.bot_data["db"]

    async with db.session_factory() as session, session.begin():
        repo = ChatRepository(session)
        service = ChatService(repo)

        result = await service.register_chat(
            chat_id=chat.id,
            chat_type=chat.type,
            chat_title=chat.title,
            tag_name=chat.username,
        )

        is_created = result.is_created
        is_approved = result.chat.status == ChatStatus.approved

    # Если чат появился впервые,
    # нужно отправить админу запрос на модерацию.
    if is_created:
        notifier = AdminNotifier(context.bot, settings.admin_ids)
        await notifier.send(
            text=AdminMessages.chat_request(chat),
            reply_markup=approve_chat_keyboard(chat.id),
        )
        return

    if not is_approved:
        return

    if random.random() >= settings.meme_probability:
        return

    # Без caption для генерции через gemini
    await _render_and_reply(
        update,
        context,
        caption=None,
    )


async def handle_private_animation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Обработчик для публичных чатов.
    """

    message, user = update.message, update.effective_user

    if message is None or user is None or message.animation is None:
        return

    caption: MemeCaption | None = None

    # Если юзер прислал caption вместе с гиф
    if message.caption:
        try:
            # Разбираем caption юзера
            top_text, bottom_text = parse_user_caption(message.caption)
        except ValueError:
            await message.reply_text("Не удалось разобрать текст")
            return

        caption = MemeCaption(top_text=top_text, bottom_text=bottom_text)

    # если нет caption и юзер НЕ админ, запрещаем генерацию
    elif user.id not in settings.admin_ids:
        await message.reply_text("Пришли анимацию с текстом")
        return

    # Для админа caption может остаться None
    # Тогда AnimationService сможет сгенерить мем через Gemini
    await _render_and_reply(update, context, caption)
