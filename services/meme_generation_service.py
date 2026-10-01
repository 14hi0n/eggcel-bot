import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.models.meme_generation import (
    GenerationMode,
    GenerationStatus,
    MediaType,
)
from database.repositories.chat import ChatRepository
from database.repositories.meme_generation import (
    GenerationStatistics,
    MemeGenerationRepository,
)
from database.repositories.user import UserRepository
from services.exceptions.gemini import (
    GeminiInputBlockedError,
    GeminiNSFWError,
    GeminiOutputBlockedError,
)
from services.exceptions.meme_generation import (
    GenerationChatNotFoundError,
    GenerationUserNotFoundError,
)

logger = logging.getLogger(__name__)


class MemeGenerationService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def start(
        self,
        *,
        telegram_chat_id: int,
        telegram_user_id: int | None,
        telegram_message_id: int,
        mode: GenerationMode,
        media_type: MediaType,
    ) -> int:
        async with self._session_factory() as session, session.begin():
            chat = await ChatRepository(session).get_by_chat_id(telegram_chat_id)

            if chat is None:
                raise GenerationChatNotFoundError(telegram_chat_id)

            user_id: int | None = None

            if telegram_user_id is not None:
                user = await UserRepository(session).get_by_telegram_id(
                    telegram_user_id
                )

                if user is None:
                    raise GenerationUserNotFoundError(telegram_user_id)

                user_id = user.id

            generation = await MemeGenerationRepository(session).create(
                chat_id=chat.id,
                user_id=user_id,
                telegram_message_id=telegram_message_id,
                mode=mode,
                media_type=media_type,
            )

            return generation.id

    async def mark_success(self, generation_id: int) -> bool:
        return await self._finish(
            generation_id=generation_id,
            status=GenerationStatus.success,
        )

    async def mark_error(
        self,
        generation_id: int,
        *,
        error_code: str,
    ) -> bool:
        return await self._finish(
            generation_id=generation_id,
            status=GenerationStatus.error,
            error_code=error_code,
        )

    async def mark_failure(
        self,
        generation_id: int,
        error: BaseException,
    ) -> bool:
        if isinstance(error, GeminiNSFWError):
            status = GenerationStatus.nsfw_rejected
            error_code = "gemini_nsfw"
        elif isinstance(error, GeminiInputBlockedError):
            status = GenerationStatus.blocked
            error_code = "gemini_input_blocked"
        elif isinstance(error, GeminiOutputBlockedError):
            status = GenerationStatus.blocked
            error_code = "gemini_output_blocked"
        else:
            status = GenerationStatus.error
            error_code = type(error).__name__[:64]

        return await self._finish(
            generation_id=generation_id,
            status=status,
            error_code=error_code,
        )

    async def get_overall_statistics(
        self,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> GenerationStatistics:
        """Собирает стату по всем генерациям в базе,
        без фильтров по юзеру и чату.

        Returns:
            GenerationStatistics: _description_
        """
        async with self._session_factory() as session:
            return await MemeGenerationRepository(session).get_statistics(
                start_at=start_at,
                end_at=end_at,
            )

    async def get_chat_statistics(
        self,
        telegram_chat_id: int,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> GenerationStatistics:
        async with self._session_factory() as session:
            chat = await ChatRepository(session).get_by_chat_id(telegram_chat_id)

            if chat is None:
                raise GenerationChatNotFoundError(telegram_chat_id)

            return await MemeGenerationRepository(session).get_statistics(
                chat_id=chat.id,
                start_at=start_at,
                end_at=end_at,
            )

    async def get_user_statistics(
        self,
        telegram_user_id: int,
        *,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> GenerationStatistics:
        async with self._session_factory() as session:
            user = await UserRepository(session).get_by_telegram_id(telegram_user_id)

            if user is None:
                raise GenerationUserNotFoundError(telegram_user_id)

            return await MemeGenerationRepository(session).get_statistics(
                user_id=user.id,
                start_at=start_at,
                end_at=end_at,
            )

    async def _finish(
        self,
        *,
        generation_id: int,
        status: GenerationStatus,
        error_code: str | None = None,
    ) -> bool:
        if status is GenerationStatus.processing:
            raise ValueError("A generation cannot finish with processing status")

        async with self._session_factory() as session, session.begin():
            updated = await MemeGenerationRepository(session).finish(
                generation_id=generation_id,
                status=status,
                error_code=error_code,
            )

        if not updated:
            logger.warning(
                "Generation was not finished because it does not exist or is no "
                "longer processing: generation_id=%s target_status=%s",
                generation_id,
                status.value,
            )

        return updated
