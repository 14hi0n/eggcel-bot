import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from telegram import User

from services.chat_moderation_service import ChatModerationService


def test_collects_chat_moderation_details() -> None:
    asyncio.run(_test_collects_chat_moderation_details())


async def _test_collects_chat_moderation_details() -> None:
    owner = User(id=2, first_name="Owner", is_bot=False, username="owner")
    added_by = User(
        id=1,
        first_name="Inviter",
        is_bot=False,
        username="inviter",
    )
    photo_file = SimpleNamespace(
        download_as_bytearray=AsyncMock(return_value=bytearray(b"photo"))
    )
    full_chat = SimpleNamespace(
        id=-100123,
        title="Full Chat",
        type="supergroup",
        username="full_chat",
        description="Description",
        is_forum=True,
        has_protected_content=False,
        pinned_message=SimpleNamespace(text="Pinned", caption=None),
        invite_link=None,
        photo=SimpleNamespace(big_file_id="photo-id"),
    )
    bot = SimpleNamespace(
        id=999,
        get_chat=AsyncMock(return_value=full_chat),
        get_chat_member_count=AsyncMock(return_value=42),
        get_chat_administrators=AsyncMock(
            return_value=[SimpleNamespace(status="creator", user=owner)]
        ),
        get_chat_member=AsyncMock(
            return_value=SimpleNamespace(status="administrator")
        ),
        get_file=AsyncMock(return_value=photo_file),
    )

    service = ChatModerationService(bot)  # type: ignore[arg-type]
    details = await service.get_details(
        telegram_chat_id=-100123,
        fallback_title="Fallback",
        fallback_chat_type="group",
        fallback_username=None,
        added_by=added_by,
    )

    assert details.title == "Full Chat"
    assert details.member_count == 42
    assert details.owner is not None
    assert details.owner.telegram_id == 2
    assert details.added_by is not None
    assert details.added_by.telegram_id == 1
    assert details.bot_status == "administrator"
    assert details.pinned_message_preview == "Pinned"
    assert details.chat_url == "https://t.me/full_chat"
    assert details.photo == b"photo"
