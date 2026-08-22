import logging
import random

from PIL import Image
from telegram import Update
from telegram.ext import ContextTypes

from config import settings
from database.manager import DatabaseManager
from database.repositories.chat import ChatRepository, ChatStatus
from services.exceptions.gemini import (
    GeminiError,
    GeminiInputBlockedError,
    GeminiNSFWError,
    GeminiOutputBlockedError,
    GeminiUnavailableError,
)
from services.meme_service import create_meme
from services.text_generator import generate_meme_caption
from utils.notifications import notify_admins
from utils.parse import parse_meme_caption
from utils.telegram import download_photo

logger = logging.getLogger(__name__)


def _build_admin_context(update: Update) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    return (
        f"Chat: {chat.title or chat.full_name or 'Private chat'}\n"
        f"Chat ID: {chat.id}\n"
        f"Chat type: {chat.type}\n"
        f"User: {user.full_name if user else 'Unknown'}\n"
        f"Username: @{user.username if user and user.username else '???'}\n"
        f"User ID: {user.id if user else '???'}\n"
        f"Message ID: {message.message_id if message else '???'}"
    )


async def _create_ai_meme(
    update: Update,
    content: ContextTypes.DEFAULT_TYPE,
    image: Image.Image,
) -> bytes | None:
    """
    Processes the image and generates a meme with the given text.
    """
    admin_context = _build_admin_context(update)

    try:
        meme_data = await generate_meme_caption(image)

    except GeminiUnavailableError as exc:
        logger.warning(
            "Gemini unavailable: chat_id=%s user_id=%s error=%s",
            update.effective_chat.id,
            update.effective_user.id if update.effective_user else None,
            exc,
        )
        await notify_admins(
            bot=content.bot,
            text=(
                f"Gemini API выдал ошибку 503, вероятно перегруз серверов"
                f"\n\n{admin_context}\n\n{exc}"
            ),
        )
        return None

    except GeminiInputBlockedError as exc:
        logger.warning(
            "Gemini input blocked: chat_id=%s user_id=%s error=%s",
            update.effective_chat.id,
            update.effective_user.id if update.effective_user else None,
            exc,
        )
        await notify_admins(
            bot=content.bot,
            text=(f"Gemini заблокировал INPUT\n\n{admin_context}\n\n{exc}"),
        )
        return None
    except GeminiOutputBlockedError as exc:
        logger.warning(
            "Gemini output blocked: chat_id=%s user_id=%s error=%s",
            update.effective_chat.id,
            update.effective_user.id if update.effective_user else None,
            exc,
        )
        await notify_admins(
            bot=content.bot,
            text=f"Gemini заблокировал OUTPUT\n\n{admin_context}\n\n{exc}",
        )
        return None

    except GeminiNSFWError as exc:
        logger.warning(
            "Gemini NSFW Error: chat_id=%s user_id=%s error=%s",
            update.effective_chat.id,
            update.effective_user.id if update.effective_user else None,
            exc,
        )
        await notify_admins(
            bot=content.bot,
            text=f"Gemini обнаружил NSFW\n\n{admin_context}",
        )
        return None

    except GeminiError as exc:
        logger.exception(
            "Gemini error: chat_id=%s user_id=%s error=%s",
            update.effective_chat.id,
            update.effective_user.id if update.effective_user else None,
            exc,
        )
        await notify_admins(
            bot=content.bot,
            text=f"Gemini error\n\n{admin_context}\n\n{exc}",
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
    if not update.message or not update.message.photo:
        return

    chat_id = update.effective_chat.id

    if random.random() >= settings.meme_probability:
        logger.debug("Skipping photo message from chat %s", chat_id)
        return

    db: DatabaseManager = context.bot_data["db"]

    async with db.session_factory() as session:
        chat = await ChatRepository(session).get_by_chat_id(chat_id)

    if chat is None or chat.status != ChatStatus.approved:
        logger.debug("The chat_id %s hasn't been approved. Skip it", chat_id)
        return

    logger.info("Received photo message from chat %s", chat_id)

    image = await download_photo(update)
    logger.info("Generating a meme for the chat %s", chat_id)
    meme_image_bytes = await _create_ai_meme(update, context, image)

    if meme_image_bytes is None:
        return

    await update.message.reply_photo(photo=meme_image_bytes)
    logger.info("Sent an AI meme to the chat %s", chat_id)


async def handle_private_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.message

    if not message or not message.photo:
        return

    user_id = update.message.from_user.id
    caption = message.caption

    logger.info("Received private photo message from user: %s", user_id)

    if not caption and user_id not in settings.admin_ids:
        await message.reply_text("Добавь текст к изображению")
        return

    if user_id in settings.admin_ids:
        image = await download_photo(update)
        meme_image_bytes = await _create_ai_meme(update, context, image)
        await update.message.reply_photo(photo=meme_image_bytes)
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

    image = await download_photo(update)
    logger.info("Generating a meme for the user %s", user_id)
    meme_image_bytes = await create_meme(image, top_text, bottom_text)

    await update.message.reply_photo(photo=meme_image_bytes)
    logger.info("Sent a custom meme back to the user: %s", user_id)
