from typing import Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.chat import Chat, ChatStatus


class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_chat_id(self, chat_id: int) -> Optional[Chat]:
        result = await self.session.execute(
            select(Chat).where(Chat.chat_id == chat_id),
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        chat_id: int,
        chat_type: str,
        chat_title: str | None,
        tag_name: str | None,
        status: ChatStatus,
    ) -> Chat:
        chat = Chat(
            chat_id=chat_id,
            chat_type=chat_type,
            chat_title=chat_title,
            tag_name=tag_name,
            status=status,
        )

        self.session.add(chat)
        await self.session.flush()

        return chat

    async def set_status(self, chat_id: int, status: ChatStatus) -> Chat | None:
        chat = await self.get_by_chat_id(chat_id)

        if chat is None:
            return None

        chat.status = status
        await self.session.flush()

        return chat

    async def list_pending(self) -> Sequence[Chat]:
        return await self.list_by_status(ChatStatus.pending)

    async def list_by_status(self, status: ChatStatus) -> Sequence[Chat]:
        result = await self.session.execute(select(Chat).where(Chat.status == status))
        return result.scalars().all()

    async def compare_and_set_status(
        self,
        *,
        chat_id: int,
        expected_status: ChatStatus,
        new_status: ChatStatus,
    ) -> Chat | None:
        statement = (
            update(Chat)
            .where(
                Chat.chat_id == chat_id,
                Chat.status == expected_status,
            )
            .values(status=new_status)
            .returning(Chat)
        )

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
