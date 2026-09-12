from sqlalchemy.ext.asyncio import AsyncSession

from database.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        telegram_id: int,
        fullname: str,
        username: str,
        private_watermark_enabled: bool | None = None,
        is_banned: bool | None = None,
    ) -> User:
        user = User()

        self.session.add(user)
        await self.session.flush()

        return user
