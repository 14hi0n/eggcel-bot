from keyboards.approve import approve_chat_keyboard
from services.chat_moderation_service import (
    ChatModerationDetails,
    ModerationUser,
)
from texts.moderation import AdminChatModerationMessages


def _details(**overrides: object) -> ChatModerationDetails:
    values: dict[str, object] = {
        "telegram_chat_id": -100123,
        "title": "Test Chat",
        "chat_type": "supergroup",
        "username": "test_chat",
        "description": "Chat description",
        "member_count": 120,
        "added_by": ModerationUser(1, "Inviter", "inviter"),
        "owner": ModerationUser(2, "Owner", "owner"),
        "bot_status": "administrator",
        "is_forum": True,
        "has_protected_content": True,
        "pinned_message_preview": "Pinned message",
        "chat_url": "https://t.me/test_chat",
        "photo": b"photo",
    }
    values.update(overrides)
    return ChatModerationDetails(**values)  # type: ignore[arg-type]


def test_render_chat_moderation_request() -> None:
    text = AdminChatModerationMessages.chat_request(_details())

    assert "Название: Test Chat" in text
    assert "Участников: 120" in text
    assert "Бота добавил: @inviter, Inviter (ID: 1)" in text
    assert "Владелец: @owner, Owner (ID: 2)" in text
    assert "Особенности: форум, защищённый контент" in text
    assert "Закреплённое сообщение:\nPinned message" in text


def test_moderation_message_fits_photo_caption() -> None:
    text = AdminChatModerationMessages.chat_request(
        _details(
            title="T" * 300,
            description="D" * 500,
            pinned_message_preview="P" * 500,
        )
    )

    assert len(text) <= 900


def test_approve_keyboard_contains_chat_link_when_available() -> None:
    keyboard = approve_chat_keyboard(
        -100123,
        chat_url="https://t.me/test_chat",
    )

    assert keyboard.inline_keyboard[0][0].url == "https://t.me/test_chat"
    assert keyboard.inline_keyboard[1][0].callback_data == "chat:approved:-100123"


def test_approve_keyboard_omits_chat_link_when_unavailable() -> None:
    keyboard = approve_chat_keyboard(-100123)

    assert keyboard.inline_keyboard[0][0].callback_data == "chat:approved:-100123"
