import asyncio
import logging
import random

from telegram import Update
from telegram.ext import ContextTypes

from config import settings
from database.manager import DatabaseManager
from database.models.chat import ChatStatus
from database.repositories.chat import ChatRepository
from helpers.telegram import download_photo, get_prompt_template_values
from keyboards.approve import approve_chat_keyboard
from services.admin_notifier import AdminNotifier
from services.chat_service import ChatService
from services.gemini_caption_generator import MemeCaption
from services.photo_service import PhotoService
from texts.messages import AdminMessages
from utils.parse import parse_user_caption

logger = logging.getLogger(__name__)


async def _render_and_replay(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    caption: MemeCaption | None,
) -> None:
    message = update.effective_message
    if message is None or not message.photo:
        return

    chat_id = message.chat_id
    message_id = message.message_id
    mode = "ai" if caption is None else "custom"
    chat_type = message.chat.type

    template_values = get_prompt_template_values(message)
    service: PhotoService = context.bot_data["photo_service"]

    logger.info(
        "Processing photo: chat_id=%s message_id=%s chat_type=%s mode=%s",
        chat_id,
        message_id,
        chat_type,
        mode,
    )

    try:
        image = await download_photo(message.photo)
        with image:
            await asyncio.to_thread(image.load)
            result = await service.create_meme(
                image=image,
                template_values=template_values,
                caption=caption,
            )
    except OSError, RuntimeError, TimeoutError, ValueError:
        logger.exception(
            "Photo processing failed: chat_id=%s message_id=%s chat_type=%s mode=%s",
            chat_id,
            message_id,
            chat_type,
            mode,
        )
        if chat_type == "private":
            await message.reply_text("Какая-то ошибка во время обработки")
        return

    await message.reply_photo(photo=result)
    logger.info(
        "Sent photo: chat_id=%s message_id=%s chat_type=%s mode=%s",
        chat_id,
        message_id,
        chat_type,
        mode,
    )


async def handle_public_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    message = update.message
    tg_chat = update.effective_chat
    if message is None or tg_chat is None or not message.photo:
        return

    chat_id = tg_chat.id

    db: DatabaseManager = context.bot_data["db"]
    async with db.session_factory() as session, session.begin():
        service = ChatService(ChatRepository(session))
        result = await service.register_chat(
            chat_id=chat_id,
            chat_type=tg_chat.type,
            chat_title=tg_chat.title,
            tag_name=tg_chat.username,
        )
        is_created = result.is_created
        is_approved = result.chat.status == ChatStatus.approved

    if is_created:
        logger.debug("New chat %s has been added to the DB", chat_id)

        notifier = AdminNotifier(context.bot, settings.admin_ids)
        await notifier.send(
            text=AdminMessages.chat_request(tg_chat),
            reply_markup=approve_chat_keyboard(tg_chat.id),
        )
        return

    if not is_approved:
        logger.debug("Chat %s was skipped without approval", chat_id)
        return

    if random.random() >= settings.meme_probability:
        logger.debug("Skipping photo message from chat %s", chat_id)
        return

    await _render_and_replay(update=update, context=context, caption=None)


async def handle_private_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message, user = update.message, update.effective_user

    if message is None or user is None or not message.photo:
        return

    caption: MemeCaption | None = None

    if message.caption:
        try:
            top_text, bottom_text = parse_user_caption(message.caption)
        except ValueError:
            await message.reply_text("Не удалось разобрать текст")
            return
        caption = MemeCaption(top_text=top_text, bottom_text=bottom_text)
    elif user.id not in settings.admin_ids:
        await message.reply_text("Тебе нужно указать подпись для этой картинки")
        return

    await _render_and_replay(update, context, caption=caption)
