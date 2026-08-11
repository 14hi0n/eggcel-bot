from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from .models.base import Base


class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url

        engine_kwargs = {
            "echo": False,
            "pool_pre_ping": True,
        }

        if database_url.startswith("postgresql+asyncpg://"):
            engine_kwargs["poolclass"] = NullPool

        self.engine: AsyncEngine = create_async_engine(
            database_url,
            **engine_kwargs,
        )

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def init(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        await self.engine.dispose()
