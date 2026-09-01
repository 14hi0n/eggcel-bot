import logging
from collections.abc import Sequence

from telegram import Bot, InlineKeyboardMarkup
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class AdminNotifier:
    def __init__(self, bot: Bot, admin_ids: Sequence[int]) -> None:
        self._bot = bot
        self._admin_ids = admin_ids

    async def send(
        self,
        *,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        """
        Разослать уведомления всем админам.
        """
        for admin_id in self._admin_ids:
            try:
                await self._bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    reply_markup=reply_markup,
                )
            except TelegramError as exc:
                logger.warning(
                    "Filed to notify admin %s: %s",
                    admin_id,
                    exc,
                )
