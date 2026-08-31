import io
from typing import Sequence

from PIL import Image
from telegram import CallbackQuery, Message, PhotoSize, Update


async def download_photo(photos: Sequence[PhotoSize]) -> Image.Image:
    # get the photo with the highest resolution
    photo_file = await photos[-1].get_file()
    # downloads the file to the buffer
    photo_bytes = await photo_file.download_as_bytearray()

    return Image.open(io.BytesIO(photo_bytes))


def get_text_callback(update: Update) -> tuple[CallbackQuery, Message, str] | None:
    query = update.callback_query

    if query is None or query.data is None:
        return None

    message = query.message
    if not isinstance(message, Message):
        return None

    if message.text is None:
        return None

    return query, message, query.data
