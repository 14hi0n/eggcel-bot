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


def get_prompt_template_values(message: Message) -> dict[str, str | None]:
    """Собирает и возвращает обьект необходимый для шаблонизатора.

    Args:
        message (Message): _description_

    Returns:
        dict[str, str | None]: _description_
    """

    user = message.from_user
    sender_chat = message.sender_chat
    chat = message.chat

    return {
        "user": user.full_name if user is not None else None,
        "username": user.username
        if user is not None and user.username is not None
        else None,
        "chat": chat.title,
        "chat_username": chat.username if chat.username is not None else None,
        "sender": sender_chat.title if sender_chat is not None else None,
        "sender_username": sender_chat.username
        if sender_chat is not None and sender_chat.username is not None
        else None,
    }
