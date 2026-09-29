from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from database.manager import DatabaseManager
from database.repositories.chat import ChatRepository
from keyboards.approve import approve_chat_keyboard
from services.chat_moderation_service import ChatModerationService
from texts.moderation import AdminChatModerationMessages


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
    moderation_service: ChatModerationService = context.bot_data[
        "chat_moderation_service"
    ]

    for chat in chats[:max_items]:
        details = await moderation_service.get_details(
            telegram_chat_id=chat.chat_id,
            fallback_title=chat.chat_title,
            fallback_chat_type=chat.chat_type,
            fallback_username=chat.tag_name,
        )
        text = AdminChatModerationMessages.pending_chat(details)
        reply_markup = approve_chat_keyboard(
            chat.chat_id,
            chat_url=details.chat_url,
        )

        if details.photo is not None:
            await message.reply_photo(
                photo=details.photo,
                caption=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
            )
        else:
            await message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML,
            )

    if len(chats) > max_items:
        await message.reply_text(f"Показаны первые {max_items} из {len(chats)}")
