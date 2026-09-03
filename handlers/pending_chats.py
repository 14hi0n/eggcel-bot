from telegram import Update
from telegram.ext import ContextTypes

from database.manager import DatabaseManager
from database.repositories.chat import ChatRepository
from keyboards.approve import approve_chat_keyboard
from texts.messages import AdminMessages


async def show_pending_chats(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.effective_message

    if message is None:
        return

    db: DatabaseManager = context.bot_data["db"]

    async with db.session_factory() as session:
        repo = ChatRepository(session)
        chats = await repo.list_pending()

    if not chats:
        await message.reply_text("Нет чатов")
        return

    await message.reply_text(f"Ожидают модерации: {len(chats)}")

    max_items = 5

    for chat in chats[:max_items]:
        await message.reply_text(
            text=AdminMessages.pending_chat(chat),
            reply_markup=approve_chat_keyboard(chat.chat_id),
        )

    if len(chats) > max_items:
        await message.reply_text(f"Показаны первые {max_items} из {len(chats)}")
