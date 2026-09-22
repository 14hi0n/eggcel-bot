from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(
        self,
        telegram_id: int,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        telegram_id: int,
        fullname: str,
        username: str | None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            fullname=fullname,
            username=username,
        )

        self.session.add(user)
        await self.session.flush()

        return user
