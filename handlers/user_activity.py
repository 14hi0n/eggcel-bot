import logging

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ContextTypes

from database.manager import DatabaseManager
from database.models.chat import ChatStatus
from database.repositories.chat import ChatRepository
from database.repositories.user import UserRepository
from services.chat_service import ChatService
from services.user_service import UserService

logger = logging.getLogger(__name__)


async def track_user_activity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Регистрация юзера который взаимодействовал с ботом."""
    tg_user, chat = update.effective_user, update.effective_chat

    if tg_user is None or tg_user.is_bot or chat is None:
        return

    db: DatabaseManager = context.bot_data["db"]

    async with db.session_factory() as session, session.begin():
        user_service = UserService(UserRepository(session))

        user = await user_service.register_or_update(
            telegram_id=tg_user.id,
            fullname=tg_user.full_name,
            username=tg_user.username,
        )

        if chat.type == ChatType.PRIVATE:
            chat_service = ChatService(ChatRepository(session))
            await chat_service.register_chat(
                chat_id=chat.id,
                chat_type=chat.type,
                chat_title=chat.title,
                tag_name=chat.username,
                initial_status=ChatStatus.approved,
            )

    logger.debug(
        "User activity recorded telegram_id=%s user_id=%s",
        tg_user.id,
        user.id,
    )
