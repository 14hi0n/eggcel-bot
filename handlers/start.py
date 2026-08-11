from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Добавь меня в чат и вызови бота командой /activate@eggcel_bot\n"
        "Когда разраб одобрит, тогда я начну делать мемы"
    )

    await update.message.reply_text(text)
