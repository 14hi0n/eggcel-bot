import logging

from telegram import Update
from telegram.ext import ContextTypes

from database.manager import DatabaseManager
from database.repositories.chat import ChatRepository
from services.chat_service import ChatActionOutcome, ChatService
from services.exceptions.chat_service import ChatNotFoundError

logger = logging.getLogger(__name__)


async def remove_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user = update.effective_user
    message = update.message

    if user is None or user.id is None or message is None:
        return

    if not context.args:
        await message.reply_text("Используй: /remove <chat_id>")
        return

    try:
        chat_id = int(context.args[0])
    except ValueError:
        await message.reply_text("chat_id должен быть числом")
        return

    db: DatabaseManager = context.bot_data["db"]

    try:
        async with db.session_factory() as session, session.begin():
            chat_repo = ChatRepository(session=session)
            chat_service = ChatService(chat_repo=chat_repo)

            result = await chat_service.disable_chat(chat_id=chat_id)

    except ChatNotFoundError:
        logger.warning("Chat %s was not found in the database", chat_id)
        await message.reply_text("Нет в базе")
        return

    match result.outcome:
        case ChatActionOutcome.CHANGED:
            text = f"Отключено: {chat_id}"

        case ChatActionOutcome.UNCHANGED:
            text = f"Чат уже отключен: {chat_id}"

        case _:
            raise RuntimeError(f"Unexpected remove-chat outcome: {result.outcome}")

    await message.reply_text(text)
