from html import escape

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

    @classmethod
    def error(
        cls,
        error: BaseException | None = None,
        *,
        details: ChatModerationDetails | None = None,
        update: Update | None = None,
        title: str,
    ) -> str:
        lines = [
            escape(title),
            "",
        ]

        if error is not None:
            error_text = f"{type(error).__name__}: {error}"
            lines.append(escape(cls._truncate(error_text, 300)))

        if details is not None:
            lines.extend(("", *cls._chat_lines(details, include_pinned=False)))

        if update is not None:
            chat = update.effective_chat
            user = update.effective_user

            if details is None and chat is not None:
                lines.append(f"Chat ID: <code>{chat.id}</code>")

            if user is not None:
                initiator = ModerationUser.from_telegram(user)
                lines.extend(
                    ("", f"Инициатор: {cls._render_user(initiator)}")
                )

        return cls._limit("\n".join(lines))

    @classmethod
    def _render(
        cls,
        heading: str,
        details: ChatModerationDetails,
    ) -> str:
        lines = [heading, "", *cls._chat_lines(details, include_pinned=True)]
        return cls._limit("\n".join(lines))

    @classmethod
    def _chat_lines(
        cls,
        details: ChatModerationDetails,
        *,
        include_pinned: bool,
    ) -> list[str]:
        member_count = (
            str(details.member_count)
            if details.member_count is not None
            else "неизвестно"
        )
        lines = [
            f"Название: {escape(details.title or 'без названия')}",
            f"ID: <code>{details.telegram_chat_id}</code>",
            f"Тип: {escape(details.chat_type)}",
            f"Участников: {member_count}",
            (
                f"Username: @{escape(details.username)}"
                if details.username is not None
                else "Username: закрытый чат"
            ),
        ]

        if details.description is not None:
            lines.extend(("", "Описание:", escape(details.description)))

        if details.added_by is not None:
            lines.extend(("", f"Бота добавил: {cls._render_user(details.added_by)}"))

        if details.owner is not None:
            lines.append(f"Владелец: {cls._render_user(details.owner)}")

        if details.bot_status is not None:
            lines.append(f"Статус бота: {escape(details.bot_status)}")

        flags = []
        if details.is_forum:
            flags.append("форум")
        if details.has_protected_content:
            flags.append("защищённый контент")
        if flags:
            lines.append(f"Особенности: {', '.join(flags)}")

        if include_pinned and details.pinned_message_preview is not None:
            lines.extend(
                (
                    "",
                    "Закреплённое сообщение:",
                    escape(details.pinned_message_preview),
                )
            )

        return lines

    @staticmethod
    def _render_user(user: ModerationUser) -> str:
        username = (
            f"@{escape(user.username)}, " if user.username is not None else ""
        )
        return (
            f"{username}{escape(user.full_name)} "
            f"(ID: <code>{user.telegram_id}</code>)"
        )

    @staticmethod
    def _truncate(value: str, limit: int) -> str:
        if len(value) <= limit:
            return value

        return f"{value[: limit - 3]}..."

    @classmethod
    def _limit(cls, text: str) -> str:
        return cls._truncate(text, _MESSAGE_LIMIT)
