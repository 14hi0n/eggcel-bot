from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Отправь мне фото с подписью, и я сделаю из него мем.\n\n"
        "Формат подписи:\n"
        "Верхний текст / Нижний текст\n"
        "или\n"
        "Верхний текст\\nНижний текст\n\n"
    )
