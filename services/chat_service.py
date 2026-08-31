from dataclasses import dataclass

from database.models.chat import Chat, ChatStatus
from database.repositories.chat import ChatRepository

from .exceptions.chat_service import ChatNotFoundError


@dataclass(slots=True)
class ChatResult:
    chat: Chat
    is_created: bool


class ChatService:
    def __init__(self, chat_repo: ChatRepository):
        self.chat_repo = chat_repo

    def _sync_metadata(
        self,
        chat: Chat,
        *,
        chat_type: str,
        chat_title: str | None,
        tag_name: str | None,
    ) -> None:
        chat.chat_type = chat_type
        chat.chat_title = chat_title
        chat.tag_name = tag_name

    async def get_or_create(
        self,
        chat_id: int,
        chat_type: str,
        chat_title: str | None,
        tag_name: str | None,
        initial_status: ChatStatus = ChatStatus.pending,
    ) -> ChatResult:
        """Возвращает чат. Если не существует - создает и возвращает.

        Args:
            chat_id (int): Уникальный ID чата.
            chat_type (str): Тип чата.
            chat_title (str): Имя канала.
            tag_name (str): Уникальное имя канала.
            В контексте Bot API именуется - username
            initial_status (ChatStatus | None): Статус одобрения.

        Returns:
            ChatResult: _description_
        """
        chat = await self.chat_repo.get_by_chat_id(chat_id)

        if chat is not None:
            self._sync_metadata(
                chat,
                chat_type=chat_type,
                chat_title=chat_title,
                tag_name=tag_name,
            )

            return ChatResult(chat=chat, is_created=False)

        chat = await self.chat_repo.create(
            chat_id=chat_id,
            chat_type=chat_type,
            chat_title=chat_title,
            tag_name=tag_name,
            status=initial_status,
        )

        return ChatResult(chat=chat, is_created=True)

    async def approve(self, chat_id: int) -> Chat | None:
        """Одобрить чат.

        Args:
            chat_id (int):  ID чата.

        Raises:
            ChatNotFoundError: Если чат не существует в БД.

        Returns:
            Chat: Обьект чата из БД.
        """
        chat = await self.chat_repo.get_by_chat_id(chat_id=chat_id)

        if chat is None:
            raise ChatNotFoundError(chat_id)

        if chat.status == ChatStatus.approved:
            return chat

        return await self.chat_repo.set_status(
            chat_id=chat_id,
            status=ChatStatus.approved,
        )

    async def reject(self, chat_id: int) -> Chat | None:
        """Отклонить чат.

        Args:
            chat_id (int):  ID чата.

        Raises:
            ChatNotFoundError: Если чат не существует в БД.

        Returns:
            Chat: Обьект чата из БД.
        """
        chat = await self.chat_repo.get_by_chat_id(chat_id=chat_id)

        if chat is None:
            raise ChatNotFoundError(chat_id)

        if chat.status == ChatStatus.rejected:
            return chat

        return await self.chat_repo.set_status(
            chat_id=chat_id,
            status=ChatStatus.rejected,
        )

    async def set_status(self, *, chat_id: int, status: ChatStatus) -> Chat:
        chat = await self.chat_repo.set_status(chat_id=chat_id, status=status)

        if chat is None:
            raise ChatNotFoundError(chat_id)

        if chat.status == status:
            return chat

        return chat

    async def add_approved(
        self,
        *,
        chat_id: int,
        chat_type: str,
        chat_title: str | None,
        tag_name: str | None,
    ) -> ChatResult:
        result = await self.get_or_create(
            chat_id=chat_id,
            chat_type=chat_type,
            chat_title=chat_title,
            tag_name=tag_name,
            initial_status=ChatStatus.approved,
        )

        if not result.is_created:
            await self.set_status(
                chat_id=chat_id,
                status=ChatStatus.approved,
            )

        return result
