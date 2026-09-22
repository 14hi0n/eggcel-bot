import logging

from telegram import Update
from telegram.ext import ContextTypes

from database.manager import DatabaseManager
from database.repositories.user import UserRepository
from services.user_service import UserService

logger = logging.getLogger(__name__)


async def track_private_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    tg_user, chat = update.effective_user, update.effective_chat

    if tg_user is None or tg_user.is_bot or chat is None:
        return

    db: DatabaseManager = context.bot_data["db"]

    async with db.session_factory() as session, session.begin():
        service = UserService(UserRepository(session))

        user = await service.register_or_update(
            telegram_id=tg_user.id,
            fullname=tg_user.full_name,
            username=tg_user.username,
        )

    logger.debug(
        "User activity recorded telegram_id=%s user_id=%s",
        tg_user.id,
        user.id,
    )
