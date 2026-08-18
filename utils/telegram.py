import io

from PIL import Image
from telegram import Update


async def download_photo(update: Update) -> Image.Image:
    # get the photo with the highest resolution
    photo_file = await update.message.photo[-1].get_file()
    # downloads the file to the buffer
    photo_bytes = await photo_file.download_as_bytearray()

    return Image.open(io.BytesIO(photo_bytes))
