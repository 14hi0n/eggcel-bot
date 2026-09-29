from telegram import Update

from services.chat_moderation_service import (
    ChatModerationDetails,
    ModerationUser,
)

_MESSAGE_LIMIT = 900


class AdminChatModerationMessages:
    @classmethod
    def chat_request(cls, details: ChatModerationDetails) -> str:
        return cls._render("Запрос на активацию", details)

    @classmethod
    def pending_chat(cls, details: ChatModerationDetails) -> str:
        return cls._render("Ожидает модерации", details)

    @staticmethod
    def error(
        error: BaseException | None = None,
        *,
        update: Update | None = None,
        title: str,
    ) -> str:
        lines = [
            f"{title}",
            "",
        ]

        if error is not None:
            lines.append(f"{type(error).__name__}: {error}")

        if update is not None:
            chat = update.effective_chat
            user = update.effective_user

            if chat is not None:
                lines.append(f"Chat ID: <code>{chat.id}</code>")

            if user is not None:
                lines.append(f"User ID: <code>{user.id}</code>")

        return "\n".join(lines)

    @classmethod
    def _render(
        cls,
        heading: str,
        details: ChatModerationDetails,
    ) -> str:
        member_count = (
            str(details.member_count)
            if details.member_count is not None
            else "неизвестно"
        )
        lines = [
            heading,
            "",
            f"Название: {details.title or 'без названия'}",
            f"ID: <code>{details.telegram_chat_id}</code>",
            f"Тип: {details.chat_type}",
            f"Участников: {member_count}",
            (
                f"Username: @{details.username}"
                if details.username is not None
                else "Username: закрытый чат"
            ),
        ]

        if details.description is not None:
            lines.extend(("", "Описание:", details.description))

        if details.added_by is not None:
            lines.extend(("", f"Бота добавил: {cls._render_user(details.added_by)}"))

        if details.owner is not None:
            lines.append(f"Владелец: {cls._render_user(details.owner)}")

        if details.bot_status is not None:
            lines.append(f"Статус бота: {details.bot_status}")

        flags = []
        if details.is_forum:
            flags.append("форум")
        if details.has_protected_content:
            flags.append("защищённый контент")
        if flags:
            lines.append(f"Особенности: {', '.join(flags)}")

        if details.pinned_message_preview is not None:
            lines.extend(
                ("", "Закреплённое сообщение:", details.pinned_message_preview)
            )

        text = "\n".join(lines)

        if len(text) <= _MESSAGE_LIMIT:
            return text

        return f"{text[: _MESSAGE_LIMIT - 3]}..."

    @staticmethod
    def _render_user(user: ModerationUser) -> str:
        username = f"@{user.username}, " if user.username is not None else ""
        return f"{username}{user.full_name} (ID: <code>{user.telegram_id}</code>)"
