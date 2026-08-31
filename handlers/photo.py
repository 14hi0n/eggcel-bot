import logging
import random

from PIL import Image
from telegram import Update
from telegram.ext import ContextTypes

from config import settings
from database.manager import DatabaseManager
from database.models.chat import ChatStatus
from database.repositories.chat import ChatRepository
from helpers.telegram import download_photo
from keyboards.approve import approve_chat_keyboard
from services.admin_notifications import AdminNotifier
from services.chat_service import ChatService
from services.exceptions.gemini import (
    GeminiError,
    GeminiInputBlockedError,
    GeminiNSFWError,
    GeminiOutputBlockedError,
    GeminiUnavailableError,
)
from services.meme_service import create_meme
from services.text_generator import generate_meme_caption
from texts.messages import AdminMessages
from utils.parse import parse_meme_caption

logger = logging.getLogger(__name__)


async def _create_ai_meme(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    image: Image.Image,
) -> bytes | None:
    """
    Processes the image and generates a meme with the given text.
    """
    chat = update.effective_chat
    user = update.effective_user

    if user is None or chat is None:
        return

    notifier = AdminNotifier(context.bot, settings.admin_ids)

    try:
        meme_data = await generate_meme_caption(image)

    except GeminiUnavailableError as exc:
        logger.warning(
            "Gemini unavailable: chat_id=%s user_id=%s error=%s",
            chat.id,
            user.id if user else None,
            exc,
        )

        error_text = AdminMessages.error(
            exc,
            update=update,
            title="Gemini API выдал ошибку 503, вероятно перегруз серверов",
        )
        await notifier.send(
            text=error_text,
        )

        return None

    except GeminiInputBlockedError as exc:
        logger.warning(
            "Gemini input blocked: chat_id=%s user_id=%s error=%s",
            chat.id,
            user.id if user else None,
            exc,
        )
        error_text = AdminMessages.error(
            exc,
            update=update,
            title="Gemini заблокировал INPUT",
        )
        await notifier.send(
            text=error_text,
        )

        return None

    except GeminiOutputBlockedError as exc:
        logger.warning(
            "Gemini output blocked: chat_id=%s user_id=%s error=%s",
            chat.id,
            user.id if user else None,
            exc,
        )
        error_text = AdminMessages.error(
            exc,
            update=update,
            title="Gemini заблокировал OUTPUT",
        )
        await notifier.send(
            text=error_text,
        )

        return None

    except GeminiNSFWError as exc:
        logger.warning(
            "Gemini NSFW Error: chat_id=%s user_id=%s error=%s",
            chat.id,
            user.id if user else None,
            exc,
        )

        error_text = AdminMessages.error(
            exc,
            update=update,
            title="Gemini обнаружил NSFW",
        )
        await notifier.send(
            text=error_text,
        )

        return None

    except GeminiError as exc:
        logger.exception(
            "Gemini error: chat_id=%s user_id=%s error=%s",
            chat.id,
            user.id if user else None,
            exc,
        )
        error_text = AdminMessages.error(
            exc,
            update=update,
            title="Gemini error",
        )
        await notifier.send(
            text=error_text,
        )

        return None

    if meme_data is None:
        logger.error(
            "Gemini meme data is None: chat_id=%s user_id=%s",
            chat.id,
            user.id if user else None,
        )
        error_text = AdminMessages.error(
            update=update,
            title="Gemini не смог сгенерить мем и вернул None",
        )
        await notifier.send(
            text=error_text,
        )
        return None

    return await create_meme(
        image,
        meme_data.top_text,
        meme_data.bottom_text,
    )


async def handle_public_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:

    message = update.message
    tg_chat = update.effective_chat

    if message is None or tg_chat is None or message.photo is None:
        return

    chat_id = tg_chat.id

    # ===================================================
    # Повторно проверяет наличие чата в БД и присылает админу
    # на модерацию, если чат новый.
    # На случай если обработчик on_bot_added пропустил добавление чата в БД.
    # Например, если бот был выключен в момент добавления чата.
    #
    # Возможно временный кусок.
    # ===================================================
    db: DatabaseManager = context.bot_data["db"]

    async with db.session_factory() as session, session.begin():
        repo = ChatRepository(session)
        service = ChatService(repo)

        chat = await service.get_or_create(
            chat_id=chat_id,
            chat_type=tg_chat.type,
            chat_title=tg_chat.title,
            tag_name=tg_chat.username,
        )

    if chat.is_created:
        logger.debug("New chat %s has been added to the DB", chat_id)

        notifier = AdminNotifier(context.bot, settings.admin_ids)
        requset_msg = AdminMessages.chat_request(tg_chat)

        await notifier.send(
            text=requset_msg,
            reply_markup=approve_chat_keyboard(tg_chat.id),
        )

        return

    if chat.chat.status != ChatStatus.approved:
        logger.debug("Chat %s was skipped without approval", chat_id)
        return
    # ===================================================
    # ===================================================
    # ===================================================

    if random.random() >= settings.meme_probability:
        logger.debug("Skipping photo message from chat %s", chat_id)
        return

    logger.info("Received photo message from chat %s", chat_id)

    image = await download_photo(message.photo)

    logger.info("Generating a meme for the chat %s", chat_id)
    meme_image_bytes = await _create_ai_meme(update, context, image)

    if meme_image_bytes is None:
        return

    await message.reply_photo(photo=meme_image_bytes)

    logger.info("Sent an AI meme to the chat %s", chat_id)


async def handle_private_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.message
    user = update.effective_user

    if message is None or message.photo is None or user is None:
        return

    user_id = user.id
    caption = message.caption

    logger.info("Received private photo message from user: %s", user_id)

    if not caption:
        if user_id in settings.admin_ids:
            logger.info("Generating AI meme for admin %s", user_id)
            image = await download_photo(message.photo)
            meme_image_bytes = await _create_ai_meme(update, context, image)

            if meme_image_bytes is None:
                logger.warning("Failed to generate an AI meme")
                return

            await message.reply_photo(photo=meme_image_bytes)
            logger.info("Sent an AI meme to admin %s", user_id)
            return

        await message.reply_text("Добавь текст к изображению")
        return

    try:
        top_text, bottom_text = parse_meme_caption(caption)

    except ValueError:
        logger.debug(
            "A user sent a caption that couldn't be parsed. User ID: %s Caption: %s",
            user_id,
            caption,
        )
        await message.reply_text("Не удалось разобрать текст")
        return

    image = await download_photo(message.photo)
    logger.info("Generating a meme for the user %s", user_id)
    meme_image_bytes = await create_meme(image, top_text, bottom_text)

    await message.reply_photo(photo=meme_image_bytes)
    logger.info("Sent a custom meme back to the user: %s", user_id)
