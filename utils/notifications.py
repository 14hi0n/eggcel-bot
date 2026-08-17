import logging

from telegram import Bot

from config import Config

logger = logging.getLogger(__name__)


async def notify_admins(bot: Bot, text: str, reply_markup: str | None = None) -> None:
    for admin_id in Config.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=text,
                reply_markup=reply_markup,
            )
        except Exception:
            logger.exception("Unable to send a notification to the admin: %s", admin_id)
