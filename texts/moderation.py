from telegram import Chat, Update

from database.models.chat import Chat as DatabaseChat


class AdminChatModerationMessages:
    @staticmethod
    def chat_request(chat: Chat) -> str:
        lines = [
            "Запрос на активацию",
            "",
            f"ID: {chat.id}\n",
            f"Title: {chat.title or '???'}\n",
            "Desc: todo",
            f"Type: {chat.type}",
        ]

        if chat.username is not None:
            lines.append(f"Username: @{chat.username}")

        return "\n".join(lines)

    @staticmethod
    def pending_chat(chat: DatabaseChat) -> str:
        lines = [
            "Ожидает модерации",
            "",
            f"ID: {chat.chat_id}",
            f"Title: {chat.chat_title or '???'}\n",
            "Desc: todo",
            f"Type: {chat.chat_type}",
        ]

        if chat.tag_name is not None:
            lines.append(f"Username: @{chat.tag_name}")

        return "\n".join(lines)

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
                lines.append(f"Chat ID: {chat.id}")

            if user is not None:
                lines.append(f"User ID: {user.id}")

        return "\n".join(lines)
