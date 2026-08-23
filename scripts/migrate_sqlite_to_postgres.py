"""
Реализован только для того, чтобы перенести
уже существующие каналы с локальной с sqlite на postgres
"""

import asyncio
import os

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import create_async_engine

from database.models.chat import Chat

SQLITE_URL = os.environ["SOURCE_DB_URL"]
POSTGRES_URL = os.environ["TARGET_DB_URL"]


async def migrate() -> None:
    sqlite_engine = create_async_engine(SQLITE_URL)
    postgres_engine = create_async_engine(POSTGRES_URL)

    try:
        async with sqlite_engine.connect() as source:
            result = await source.execute(select(Chat.__table__))
            rows = result.mappings().all()

        print(f"Found {len(rows)} chats")

        if not rows:
            return

        async with postgres_engine.begin() as target:
            await target.execute(
                insert(Chat.__table__),
                rows,
            )

        print(f"Migrated {len(rows)} chats")

    finally:
        await sqlite_engine.dispose()
        await postgres_engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())
