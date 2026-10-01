from database.models.meme_generation import (
    GenerationMode,
    GenerationStatus,
    MediaType,
)
from database.repositories.meme_generation import GenerationStatistics
from texts.statistics import GenerationStatisticsMessages


def test_render_overall_generation_statistics() -> None:
    statistics = GenerationStatistics(
        total=8,
        by_status={
            GenerationStatus.success: 5,
            GenerationStatus.nsfw_rejected: 2,
            GenerationStatus.error: 1,
        },
        by_mode={
            GenerationMode.ai: 6,
            GenerationMode.custom: 2,
        },
        by_media_type={
            MediaType.photo: 7,
            MediaType.animation: 1,
        },
    )

    text = GenerationStatisticsMessages.overall(statistics)

    assert "Область: все генерации" in text
    assert "Период: всё время" in text
    assert "Всего: 8" in text
    assert "Успешно: 5" in text
    assert "В обработке: 0" in text
    assert "Отклонено NSFW: 2" in text
    assert "AI: 6" in text
    assert "Анимации: 1" in text


def test_render_statistics_period() -> None:
    statistics = GenerationStatistics(
        total=0,
        by_status={},
        by_mode={},
        by_media_type={},
    )

    text = GenerationStatisticsMessages.for_chat(
        statistics,
        -100200,
        period_label="09/2026 (UTC)",
    )

    assert "Область: чат -100200" in text
    assert "Период: 09/2026 (UTC)" in text


def test_render_not_found_messages() -> None:
    assert (
        GenerationStatisticsMessages.user_not_found(100)
        == "Пользователь 100 не найден"
    )
    assert (
        GenerationStatisticsMessages.chat_not_found(-100200)
        == "Чат -100200 не найден"
    )
