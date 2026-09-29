import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.models.base import Base
from database.models.chat import Chat, ChatStatus
from database.models.meme_generation import (
    GenerationMode,
    GenerationStatus,
    MediaType,
)
from database.models.user import User
from services.exceptions.gemini import GeminiNSFWError
from services.meme_generation_service import MemeGenerationService


def test_tracks_generation_and_builds_statistics() -> None:
    asyncio.run(_test_tracks_generation_and_builds_statistics())


async def _test_tracks_generation_and_builds_statistics() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

        async with session_factory() as session, session.begin():
            session.add(
                Chat(
                    chat_id=100,
                    chat_type="private",
                    chat_title=None,
                    tag_name=None,
                    status=ChatStatus.approved,
                )
            )
            session.add(
                User(
                    telegram_id=100,
                    fullname="Test User",
                    username="test_user",
                )
            )

        service = MemeGenerationService(session_factory)
        generation_id = await service.start(
            telegram_chat_id=100,
            telegram_user_id=100,
            telegram_message_id=10,
            mode=GenerationMode.ai,
            media_type=MediaType.photo,
        )

        processing = await service.get_overall_statistics()
        assert processing.total == 1
        assert processing.by_status == {GenerationStatus.processing: 1}
        assert processing.by_mode == {GenerationMode.ai: 1}
        assert processing.by_media_type == {MediaType.photo: 1}

        updated = await service.mark_failure(
            generation_id,
            GeminiNSFWError("rejected"),
        )
        updated_twice = await service.mark_success(generation_id)

        assert updated is True
        assert updated_twice is False

        overall = await service.get_overall_statistics()
        by_chat = await service.get_chat_statistics(100)
        by_user = await service.get_user_statistics(100)

        for statistics in (overall, by_chat, by_user):
            assert statistics.total == 1
            assert statistics.by_status == {
                GenerationStatus.nsfw_rejected: 1
            }
    finally:
        await engine.dispose()
