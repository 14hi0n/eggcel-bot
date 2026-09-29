import logging
from collections.abc import Sequence

from telegram import Bot, InlineKeyboardMarkup
from telegram.constants import ParseMode
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
        photo: bytes | None = None,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> None:
        """
        Разослать уведомления всем админам.
        """
        for admin_id in self._admin_ids:
            try:
                if photo is not None:
                    await self._bot.send_photo(
                        chat_id=admin_id,
                        photo=photo,
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await self._bot.send_message(
                        chat_id=admin_id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=ParseMode.HTML,
                    )
            except TelegramError as exc:
                logger.warning(
                    "Failed to notify admin %s: %s",
                    admin_id,
                    exc,
                )
