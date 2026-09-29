from collections.abc import Mapping

from database.models.meme_generation import (
    GenerationMode,
    GenerationStatus,
    MediaType,
)
from database.repositories.meme_generation import GenerationStatistics


def _count[T](values: Mapping[T, int], key: T) -> int:
    return values.get(key, 0)


class GenerationStatisticsMessages:
    @staticmethod
    def usage() -> str:
        return "\n".join(
            (
                "Использование:",
                "/stat - общая статистика",
                "/stat user <user_id>",
                "/stat chat <chat_id>",
            )
        )

    @classmethod
    def overall(cls, statistics: GenerationStatistics) -> str:
        return cls._render(statistics, scope="все генерации")

    @classmethod
    def for_user(
        cls,
        statistics: GenerationStatistics,
        telegram_user_id: int,
    ) -> str:
        return cls._render(
            statistics,
            scope=f"пользователь {telegram_user_id}",
        )

    @classmethod
    def for_chat(
        cls,
        statistics: GenerationStatistics,
        telegram_chat_id: int,
    ) -> str:
        return cls._render(
            statistics,
            scope=f"чат {telegram_chat_id}",
        )

    @staticmethod
    def user_not_found(telegram_user_id: int) -> str:
        return f"Пользователь {telegram_user_id} не найден"

    @staticmethod
    def chat_not_found(telegram_chat_id: int) -> str:
        return f"Чат {telegram_chat_id} не найден"

    @staticmethod
    def _render(
        statistics: GenerationStatistics,
        *,
        scope: str,
    ) -> str:
        return "\n".join(
            (
                "Статистика генераций",
                f"Область: {scope}",
                "",
                f"Всего: {statistics.total}",
                f"Успешно: {_count(statistics.by_status, GenerationStatus.success)}",
                "В обработке: "
                f"{_count(statistics.by_status, GenerationStatus.processing)}",
                "Отклонено NSFW: "
                f"{_count(statistics.by_status, GenerationStatus.nsfw_rejected)}",
                "Заблокировано: "
                f"{_count(statistics.by_status, GenerationStatus.blocked)}",
                f"Ошибки: {_count(statistics.by_status, GenerationStatus.error)}",
                "",
                f"AI: {_count(statistics.by_mode, GenerationMode.ai)}",
                "Пользовательские: "
                f"{_count(statistics.by_mode, GenerationMode.custom)}",
                "",
                f"Фото: {_count(statistics.by_media_type, MediaType.photo)}",
                f"Анимации: {_count(statistics.by_media_type, MediaType.animation)}",
            )
        )
