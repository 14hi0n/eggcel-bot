from datetime import UTC, datetime

import pytest

from handlers.statistics import (
    ChatStatistics,
    OverallStatistics,
    StatisticsPeriod,
    UserStatistics,
    parse_statistics_period,
    parse_statistics_query,
)


@pytest.mark.parametrize(
    ("value", "start_at", "end_at"),
    (
        (
            "02/29/2024",
            datetime(2024, 2, 29, tzinfo=UTC),
            datetime(2024, 3, 1, tzinfo=UTC),
        ),
        (
            "12/2025",
            datetime(2025, 12, 1, tzinfo=UTC),
            datetime(2026, 1, 1, tzinfo=UTC),
        ),
        (
            "2025",
            datetime(2025, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 1, tzinfo=UTC),
        ),
    ),
)
def test_parse_statistics_period(
    value: str,
    start_at: datetime,
    end_at: datetime,
) -> None:
    period = parse_statistics_period(value)

    assert period == StatisticsPeriod(
        start_at=start_at,
        end_at=end_at,
        label=f"{value} (UTC)",
    )


def test_today_uses_current_utc_date() -> None:
    period = parse_statistics_period(
        "ToDaY",
        now=datetime(2026, 10, 1, 23, 30, tzinfo=UTC),
    )

    assert period == StatisticsPeriod(
        start_at=datetime(2026, 10, 1, tzinfo=UTC),
        end_at=datetime(2026, 10, 2, tzinfo=UTC),
        label="10/01/2026 (UTC)",
    )


@pytest.mark.parametrize(
    "value",
    (
        "02/29/2025",
        "13/2025",
        "2025/01/01",
        "1/1/2025",
        "1000/2025",
        "unknown",
    ),
)
def test_rejects_invalid_statistics_period(value: str) -> None:
    assert parse_statistics_period(value) is None


def test_parse_statistics_query_with_optional_period() -> None:
    now = datetime(2026, 10, 1, 12, tzinfo=UTC)
    today = StatisticsPeriod(
        start_at=datetime(2026, 10, 1, tzinfo=UTC),
        end_at=datetime(2026, 10, 2, tzinfo=UTC),
        label="10/01/2026 (UTC)",
    )

    assert parse_statistics_query([]) == OverallStatistics()
    assert parse_statistics_query(["today"], now=now) == OverallStatistics(today)
    assert parse_statistics_query(["user", "123"]) == UserStatistics(123)
    assert parse_statistics_query(
        ["user", "123", "today"], now=now
    ) == UserStatistics(123, today)
    assert parse_statistics_query(
        ["chat", "-100123", "today"], now=now
    ) == ChatStatistics(-100123, today)


@pytest.mark.parametrize(
    "arguments",
    (
        ["invalid"],
        ["user", "not-an-id"],
        ["chat", "-100123", "invalid"],
        ["user", "123", "today", "extra"],
    ),
)
def test_rejects_invalid_statistics_query(arguments: list[str]) -> None:
    assert parse_statistics_query(arguments) is None
