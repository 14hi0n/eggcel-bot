from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "Просто добавь меня в чат.\nКак только разраб одобрит - начну делать мемы."
    await update.message.reply_text(text)
