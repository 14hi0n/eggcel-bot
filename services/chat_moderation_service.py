import asyncio
import logging
from dataclasses import dataclass

from telegram import Bot, ChatFullInfo, Message, User
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

_DESCRIPTION_LIMIT = 350
_PINNED_MESSAGE_LIMIT = 200


@dataclass(frozen=True, slots=True)
class ModerationUser:
    telegram_id: int
    full_name: str
    username: str | None

    @classmethod
    def from_telegram(cls, user: User) -> "ModerationUser":
        return cls(
            telegram_id=user.id,
            full_name=user.full_name,
            username=user.username,
        )


@dataclass(frozen=True, slots=True)
class ChatModerationDetails:
    telegram_chat_id: int
    title: str | None
    chat_type: str
    username: str | None
    description: str | None
    member_count: int | None
    added_by: ModerationUser | None
    owner: ModerationUser | None
    bot_status: str | None
    is_forum: bool
    has_protected_content: bool
    pinned_message_preview: str | None
    chat_url: str | None
    photo: bytes | None


class ChatModerationService:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def get_details(
        self,
        *,
        telegram_chat_id: int,
        fallback_title: str | None,
        fallback_chat_type: str,
        fallback_username: str | None,
        added_by: User | None = None,
    ) -> ChatModerationDetails:
        full_chat = await self._get_chat(telegram_chat_id)

        member_count, owner, bot_status, photo = await asyncio.gather(
            self._get_member_count(telegram_chat_id),
            self._get_owner(telegram_chat_id),
            self._get_bot_status(telegram_chat_id),
            self._get_photo(full_chat),
        )

        title = full_chat.title if full_chat is not None else fallback_title
        chat_type = (
            full_chat.type if full_chat is not None else fallback_chat_type
        )
        username = (
            full_chat.username if full_chat is not None else fallback_username
        )

        description = None
        is_forum = False
        has_protected_content = False
        pinned_message_preview = None
        invite_link = None

        if full_chat is not None:
            description = self._truncate(
                full_chat.description,
                _DESCRIPTION_LIMIT,
            )
            is_forum = bool(full_chat.is_forum)
            has_protected_content = bool(full_chat.has_protected_content)
            pinned_message_preview = self._message_preview(
                full_chat.pinned_message
            )
            invite_link = full_chat.invite_link

        chat_url = self._chat_url(
            username=username,
            invite_link=invite_link,
        )

        return ChatModerationDetails(
            telegram_chat_id=telegram_chat_id,
            title=title,
            chat_type=chat_type,
            username=username,
            description=description,
            member_count=member_count,
            added_by=(
                ModerationUser.from_telegram(added_by)
                if added_by is not None
                else None
            ),
            owner=owner,
            bot_status=bot_status,
            is_forum=is_forum,
            has_protected_content=has_protected_content,
            pinned_message_preview=pinned_message_preview,
            chat_url=chat_url,
            photo=photo,
        )

    async def _get_chat(self, chat_id: int) -> ChatFullInfo | None:
        try:
            return await self._bot.get_chat(chat_id)
        except TelegramError as exc:
            logger.warning("Failed to get chat %s details: %s", chat_id, exc)
            return None

    async def _get_member_count(self, chat_id: int) -> int | None:
        try:
            return await self._bot.get_chat_member_count(chat_id)
        except TelegramError as exc:
            logger.warning("Failed to get chat %s member count: %s", chat_id, exc)
            return None

    async def _get_owner(self, chat_id: int) -> ModerationUser | None:
        try:
            administrators = await self._bot.get_chat_administrators(chat_id)
        except TelegramError as exc:
            logger.warning("Failed to get chat %s administrators: %s", chat_id, exc)
            return None

        owner = next(
            (
                administrator.user
                for administrator in administrators
                if administrator.status == ChatMemberStatus.OWNER
            ),
            None,
        )

        if owner is None:
            return None

        return ModerationUser.from_telegram(owner)

    async def _get_bot_status(self, chat_id: int) -> str | None:
        try:
            member = await self._bot.get_chat_member(chat_id, self._bot.id)
        except TelegramError as exc:
            logger.warning("Failed to get bot status in chat %s: %s", chat_id, exc)
            return None

        return member.status

    async def _get_photo(self, chat: ChatFullInfo | None) -> bytes | None:
        if chat is None or chat.photo is None:
            return None

        try:
            photo_file = await self._bot.get_file(chat.photo.big_file_id)
            photo = await photo_file.download_as_bytearray()
        except TelegramError as exc:
            logger.warning("Failed to download chat %s photo: %s", chat.id, exc)
            return None

        return bytes(photo)

    @classmethod
    def _message_preview(cls, message: Message | None) -> str | None:
        if message is None:
            return None

        text = message.text or message.caption
        return cls._truncate(text, _PINNED_MESSAGE_LIMIT)

    @staticmethod
    def _chat_url(
        *,
        username: str | None,
        invite_link: str | None,
    ) -> str | None:
        if username is not None:
            return f"https://t.me/{username}"

        if invite_link is not None and "…" not in invite_link:
            return invite_link

        return None

    @staticmethod
    def _truncate(value: str | None, limit: int) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if len(value) <= limit:
            return value

        return f"{value[: limit - 3]}..."
