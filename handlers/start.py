from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Отправь мне картинку с описанием чтобы сделать из нее мем.\n\n"
        "А еще можешь добавь меня в чат, чтобы я делал мемы из рандомных картинок."
    )
    await update.message.reply_text(text)
