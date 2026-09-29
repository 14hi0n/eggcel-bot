from telegram import Update
from telegram.ext import ContextTypes

from texts.static import AdminHelpMessages


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None:
        return

    await message.reply_text(AdminHelpMessages.help())
