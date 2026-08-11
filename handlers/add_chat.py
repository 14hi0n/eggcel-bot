import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from config import Config
from database.manager import DatabaseManager
from database.repositories.chat import ChatRepository

logger = logging.getLogger(__name__)


async def add_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in Config.ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("Используй: /add <chat_id>")
        return

    try:
        chat_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("chat_id должен быть числом")
        return

    try:
        tg_chat = await context.bot.get_chat(chat_id)
    except TelegramError as e:
        await update.message.reply_text(f"Не удалось получить чат: {e}")
        return

    db: DatabaseManager = context.bot_data["db"]
    async with db.session_factory() as session:
        async with session.begin():
            chat = await ChatRepository(session).add_approved(
                chat_id=tg_chat.id,
                chat_type=tg_chat.type,
                display_name=tg_chat.title,
                tag_name=tg_chat.username,
            )

    await update.message.reply_text(f"Добавлено как approved: {chat.display_name}")
