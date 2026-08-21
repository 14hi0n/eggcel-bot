from telegram import Update
from telegram.ext import ContextTypes

from config import settings
from database.manager import DatabaseManager
from database.models.chat import ChatStatus
from database.repositories.chat import ChatRepository


async def remove_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in settings.admin_ids:
        return

    if not context.args:
        await update.message.reply_text("Используй: /remove <chat_id>")
        return

    try:
        chat_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("chat_id должен быть числом")
        return

    db: DatabaseManager = context.bot_data["db"]
    async with db.session_factory() as session:
        async with session.begin():
            chat = await ChatRepository(session).set_status(
                chat_id, ChatStatus.rejected
            )

    if chat is None:
        await update.message.reply_text("Такого chat_id нет в базе")
        return

    await update.message.reply_text(f"Отключено: {chat.display_name}")
