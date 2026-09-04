from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from database.models.chat import Chat, ChatStatus
from database.repositories.chat import ChatRepository
from services.exceptions.chat_service import ChatNotFoundError


class ChatActionOutcome(str, Enum):
    CREATED = "created"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    ALREADY_RESOLVED = "already_resolved"


@dataclass(frozen=True, slots=True)
class ChatActionResult:
    chat: Chat
    outcome: ChatActionOutcome

    @property
    def is_created(self) -> bool:
        """
        Нужен для обратной совместимости,
        где использовалась проверка типа result.is_created
        """
        return self.outcome is ChatActionOutcome.CREATED


class ChatService:
    def __init__(self, chat_repo: ChatRepository):
        self.chat_repo = chat_repo

    @staticmethod
    def _sync_metadata(
        chat: Chat,
        *,
        chat_type: str,
        chat_title: str | None,
        tag_name: str | None,
    ) -> None:
        chat.chat_type = chat_type
        chat.chat_title = chat_title
        chat.tag_name = tag_name

    async def _get_or_create(
        self,
        *,
        chat_id: int,
        chat_type: str,
        chat_title: str | None,
        tag_name: str | None,
        initial_status: ChatStatus,
    ) -> tuple[Chat, bool]:
        """
        Возвращает чат или создает его.
        """
        chat = await self.chat_repo.get_by_chat_id(chat_id=chat_id)

        if chat is not None:
            self._sync_metadata(
                chat,
                chat_type=chat_type,
                chat_title=chat_title,
                tag_name=tag_name,
            )
            return chat, False

        chat = await self.chat_repo.create(
            chat_id=chat_id,
            chat_type=chat_type,
            chat_title=chat_title,
            tag_name=tag_name,
            status=initial_status,
        )

        return chat, True

    async def _set_status(
        self,
        *,
        chat: Chat,
        status: ChatStatus,
    ) -> ChatActionResult:
        # если статус тот же самый, то просто возвращает чат с экшеном uncanged.
        if chat.status == status:
            return ChatActionResult(chat, ChatActionOutcome.UNCHANGED)

        # обновляем статус чата
        update_chat = await self.chat_repo.set_status(
            chat_id=chat.chat_id,
            status=status,
        )

        # если по какой-то причине чат пропал
        if update_chat is None:
            raise ChatNotFoundError(chat.chat_id)

        return ChatActionResult(update_chat, ChatActionOutcome.CHANGED)

    async def register_chat(
        self,
        *,
        chat_id: int,
        chat_type: str,
        chat_title: str | None,
        tag_name: str | None,
        initial_status: ChatStatus = ChatStatus.pending,
    ) -> ChatActionResult:
        """
        Регистрирует чат, не меняя статус уже существующего.
        """
        chat, created = await self._get_or_create(
            chat_id=chat_id,
            chat_type=chat_type,
            chat_title=chat_title,
            tag_name=tag_name,
            initial_status=initial_status,
        )

        outcome = ChatActionOutcome.CREATED if created else ChatActionOutcome.UNCHANGED

        return ChatActionResult(chat, outcome)

    async def enable_chat(
        self,
        *,
        chat_id: int,
        chat_type: str,
        chat_title: str | None,
        tag_name: str | None,
    ) -> ChatActionResult:
        """
        Регистрирует чат, не меняя статус уже существующего.
        """
        chat, created = await self._get_or_create(
            chat_id=chat_id,
            chat_type=chat_type,
            chat_title=chat_title,
            tag_name=tag_name,
            initial_status=ChatStatus.approved,
        )

        if created:
            return ChatActionResult(chat, ChatActionOutcome.CREATED)

        return await self._set_status(chat=chat, status=ChatStatus.approved)

    async def disable_chat(
        self,
        *,
        chat_id: int,
    ) -> ChatActionResult:
        """
        Регистрирует чат, не меняя статус уже существующего.
        """
        chat = await self.chat_repo.get_by_chat_id(chat_id)

        if chat is None:
            raise ChatNotFoundError(chat_id)

        return await self._set_status(chat=chat, status=ChatStatus.rejected)

    async def moderate_pending(
        self,
        *,
        chat_id: int,
        new_status: ChatStatus,
    ) -> ChatActionResult:
        """
        Принимает решение только по чату со статусом pending.
        """

        # Новый статус должен быть только approved или rejected
        if new_status not in (ChatStatus.approved, ChatStatus.rejected):
            raise ValueError("Moderation status must be approved or rejected")

        # Фиксирует только первое решение админа.
        chat = await self.chat_repo.compare_and_set_status(
            chat_id=chat_id,
            expected_status=ChatStatus.pending,
            new_status=new_status,
        )

        # Может вернуть None если чата не существует либо expected_status не совпал.
        if chat is not None:
            return ChatActionResult(chat, ChatActionOutcome.CHANGED)

        chat = await self.chat_repo.get_by_chat_id(chat_id)

        # Отдельно проверяет существование чата, если expected_status не совпал.
        if chat is None:
            raise ChatNotFoundError(chat_id)

        return ChatActionResult(chat, ChatActionOutcome.ALREADY_RESOLVED)

    async def list_pending(self) -> Sequence[Chat]:
        return await self.chat_repo.list_pending()
