from telegram import Chat, Update, User
from telegram.ext import ContextTypes

from config import settings
from keyboards.approve import approve_chat_keyboard, open_chat_keyboard
from services.admin_notifier import AdminNotifier
from services.chat_moderation_service import ChatModerationService
from texts.moderation import AdminChatModerationMessages


async def notify_chat_moderation_request(
    context: ContextTypes.DEFAULT_TYPE,
    *,
    chat: Chat,
    added_by: User | None = None,
) -> None:
    moderation_service: ChatModerationService = context.bot_data[
        "chat_moderation_service"
    ]
    details = await moderation_service.get_details(
        telegram_chat_id=chat.id,
        fallback_title=chat.title,
        fallback_chat_type=chat.type,
        fallback_username=chat.username,
        added_by=added_by,
    )

    notifier = AdminNotifier(context.bot, settings.admin_ids)
    await notifier.send(
        text=AdminChatModerationMessages.chat_request(details),
        photo=details.photo,
        reply_markup=approve_chat_keyboard(
            chat.id,
            chat_url=details.chat_url,
        ),
    )


async def notify_chat_error(
    context: ContextTypes.DEFAULT_TYPE,
    *,
    update: Update,
    error: BaseException,
    title: str,
) -> None:
    chat = update.effective_chat
    details = None

    if chat is not None:
        moderation_service: ChatModerationService = context.bot_data[
            "chat_moderation_service"
        ]
        details = await moderation_service.get_details(
            telegram_chat_id=chat.id,
            fallback_title=chat.title,
            fallback_chat_type=chat.type,
            fallback_username=chat.username,
        )

    notifier = AdminNotifier(context.bot, settings.admin_ids)
    await notifier.send(
        text=AdminChatModerationMessages.error(
            error,
            details=details,
            update=update,
            title=title,
        ),
        photo=details.photo if details is not None else None,
        reply_markup=open_chat_keyboard(
            details.chat_url if details is not None else None
        ),
    )
