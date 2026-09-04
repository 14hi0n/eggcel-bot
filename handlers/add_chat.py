import logging

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from database.manager import DatabaseManager
from database.repositories.chat import ChatRepository
from services.chat_service import ChatActionOutcome, ChatService

logger = logging.getLogger(__name__)


async def add_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    user = update.effective_user
    message = update.message

    if user is None or message is None:
        return

    if not context.args:
        await message.reply_text("Используй: /add <chat_id>")
        return

    try:
        chat_id = int(context.args[0])
    except ValueError:
        await message.reply_text("chat_id должен быть числом")
        return

    try:
        tg_chat = await context.bot.get_chat(chat_id)
    except TelegramError as e:
        await message.reply_text(f"Не удалось получить чат: {e}")
        return

    db: DatabaseManager = context.bot_data["db"]

    async with db.session_factory() as session, session.begin():
        chat_repo = ChatRepository(session)
        chat_service = ChatService(chat_repo)

        result = await chat_service.enable_chat(
            chat_id=tg_chat.id,
            chat_type=tg_chat.type,
            chat_title=tg_chat.title,
            tag_name=tg_chat.username,
        )

    chat_id = result.chat.chat_id

    match result.outcome:
        case ChatActionOutcome.CREATED:
            text = f"Чат добавлен и одобрен: {chat_id}"

        case ChatActionOutcome.CHANGED:
            text = f"Чат одобрен: {chat_id}"

        case ChatActionOutcome.UNCHANGED:
            text = f"Чат уже одобрен: {chat_id}"

        case _:
            raise RuntimeError(f"Unexpected add-chat outcome: {result.outcome}")

    await message.reply_text(text)
