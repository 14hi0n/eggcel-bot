from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.meme_generation import (
    GenerationMode,
    GenerationStatus,
    MediaType,
    MemeGeneration,
)


@dataclass(frozen=True, slots=True)
class GenerationStatistics:
    total: int
    by_status: dict[GenerationStatus, int]
    by_mode: dict[GenerationMode, int]
    by_media_type: dict[MediaType, int]


class MemeGenerationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self,
        generation_id: int,
    ) -> MemeGeneration | None:
        return await self.session.get(MemeGeneration, generation_id)

    async def create(
        self,
        *,
        chat_id: int,
        user_id: int | None,
        telegram_message_id: int,
        mode: GenerationMode,
        media_type: MediaType,
    ) -> MemeGeneration:
        generation = MemeGeneration(
            chat_id=chat_id,
            user_id=user_id,
            telegram_message_id=telegram_message_id,
            mode=mode,
            media_type=media_type,
            status=GenerationStatus.processing,
        )

        self.session.add(generation)
        await self.session.flush()

        return generation

    async def finish(
        self,
        *,
        generation_id: int,
        status: GenerationStatus,
        error_code: str | None = None,
    ) -> bool:
        statement = (
            update(MemeGeneration)
            .where(
                MemeGeneration.id == generation_id,
                MemeGeneration.status == GenerationStatus.processing,
            )
            .values(
                status=status,
                error_code=error_code,
                finished_at=datetime.now(UTC),
            )
            .returning(MemeGeneration.id)
        )

        result = await self.session.execute(statement)
        return result.scalar_one_or_none() is not None

    async def get_statistics(
        self,
        *,
        chat_id: int | None = None,
        user_id: int | None = None,
    ) -> GenerationStatistics:
        conditions = []

        if chat_id is not None:
            conditions.append(MemeGeneration.chat_id == chat_id)

        if user_id is not None:
            conditions.append(MemeGeneration.user_id == user_id)

        total = await self.session.scalar(
            select(func.count(MemeGeneration.id)).where(*conditions)
        )

        status_result = await self.session.execute(
            select(
                MemeGeneration.status,
                func.count(MemeGeneration.id),
            )
            .where(*conditions)
            .group_by(MemeGeneration.status)
        )
        mode_result = await self.session.execute(
            select(
                MemeGeneration.mode,
                func.count(MemeGeneration.id),
            )
            .where(*conditions)
            .group_by(MemeGeneration.mode)
        )
        media_type_result = await self.session.execute(
            select(
                MemeGeneration.media_type,
                func.count(MemeGeneration.id),
            )
            .where(*conditions)
            .group_by(MemeGeneration.media_type)
        )

        return GenerationStatistics(
            total=int(total or 0),
            by_status={
                status: int(count)
                for status, count in status_result.tuples().all()
            },
            by_mode={
                mode: int(count) for mode, count in mode_result.tuples().all()
            },
            by_media_type={
                media_type: int(count)
                for media_type, count in media_type_result.tuples().all()
            },
        )
