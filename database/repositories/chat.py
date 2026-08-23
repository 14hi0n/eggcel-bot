from typing import Optional, Sequence, Tuple

from sqlalchemy import select
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
        chat_id: int,
        chat_type: str,
        chat_title: str,
        tag_name: str,
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

    async def create_or_reset_pending(
        self,
        chat_id: int,
        chat_type: str,
        chat_title: str,
        tag_name: str,
    ) -> Tuple[Chat, bool]:
        chat = await self.get_by_chat_id(chat_id)

        if chat is None:
            chat = Chat(
                chat_id=chat_id,
                chat_type=chat_type,
                chat_title=chat_title,
                tag_name=tag_name,
                status=ChatStatus.pending,
            )
            self.session.add(chat)
        else:
            chat.chat_type = chat_type
            chat.chat_title = chat_title
            chat.tag_name = tag_name
            chat.status = ChatStatus.pending

        await self.session.flush()

        return chat

    async def add_approved(self, chat_id: int) -> None:
        pass

    async def set_status(self, chat_id: int, status: ChatStatus) -> Optional[Chat]:
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
