import asyncio
import io
import logging
import random

from PIL import Image
from telegram import Update
from telegram.ext import ContextTypes

from config import Config
from services.meme_renderer import compress_for_telegram, render_meme_text
from services.text_generator import generate_meme_caption

logger = logging.getLogger(__name__)


async def _process_photo(update: Update) -> None:
    """
    Processes the photo and generates a meme with the given text.
    """
    if not update.message or not update.message.photo:
        return

    # get the photo with the highest resolution
    photo_file = await update.message.photo[-1].get_file()

    # downloads the file to the buffer
    photo_bytes = await photo_file.download_as_bytearray()
    input_image = Image.open(io.BytesIO(photo_bytes))

    meme_bytes = await asyncio.to_thread(
        _process_meme,
        input_image,
    )

    await update.message.reply_photo(photo=meme_bytes)


def _process_meme(image: Image.Image) -> bytes:
    """
    Processes the image and generates a meme with the given text.
    """
    meme_data = generate_meme_caption(image)
    top_text = meme_data.top_text
    bottom_text = meme_data.bottom_text

    rendered = render_meme_text(image, top_text, bottom_text)
    return compress_for_telegram(rendered)


async def handle_public_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    It edits photos and generates memes with text.
    """

    if not update.message or not update.message.photo:
        return

    if random.random() >= Config.MEME_PROBABILITY:
        logger.info("Skipping photo message from user %s", update.message.from_user.id)
        return

    if (
        Config.ALLOWED_CHAT_IDS
        and update.message.chat_id not in Config.ALLOWED_CHAT_IDS
    ):
        logger.info(
            "Unauthorized public photo message from user %s",
            update.message.from_user.id,
        )
        return

    logger.info("Received photo message from user %s", update.message.from_user.id)

    await _process_photo(update)


async def handle_private_photo(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    It edits photos and generates memes with text.
    """

    if not update.message or not update.message.photo:
        return

    if Config.ADMIN_IDS and update.message.from_user.id not in Config.ADMIN_IDS:
        logger.info(
            "Unauthorized private photo message from user %s",
            update.message.from_user.id,
        )
        return

    logger.info(
        "Received private photo message from user %s", update.message.from_user.id
    )

    await _process_photo(update)
