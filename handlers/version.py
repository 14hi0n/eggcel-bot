from telegram import Update
from telegram.ext import ContextTypes

from build_version import APP_VERSION


async def show_version(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message

    if message is None:
        return

    await message.reply_text(f"Bot v{APP_VERSION}")
