from datetime import UTC, datetime

from database.models.user import User
from database.repositories.user import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register_or_update(
        self,
        *,
        telegram_id: int,
        fullname: str,
        username: str | None,
    ) -> User:
        user = await self.user_repo.get_by_telegram_id(telegram_id)

        if user is None:
            return await self.user_repo.create(
                telegram_id=telegram_id,
                fullname=fullname,
                username=username,
            )

        user.fullname = fullname
        user.username = username
        user.last_active_at = datetime.now(UTC)

        return user

    async def set_private_watermark_enabled(
        self,
        *,
        telegram_id: int,
        enabled: bool,
    ) -> User:
        user = await self._get_required(telegram_id)
        user.private_watermark_enabled = enabled
        return user

    async def set_banned(self, *, telegram_id: int, banned: bool) -> User:
        user = await self._get_required(telegram_id)
        user.is_banned = banned
        return user

    async def _get_required(self, telegram_id: int) -> User:
        user = await self.user_repo.get_by_telegram_id(telegram_id)

        if user is None:
            raise ValueError(f"User {telegram_id} is not registred")

        return user
