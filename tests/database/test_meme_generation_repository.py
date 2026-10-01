from datetime import UTC, datetime, timedelta, timezone

from database.repositories.meme_generation import _to_database_datetime


def test_converts_aware_datetime_to_naive_utc() -> None:
    baku_timezone = timezone(timedelta(hours=4))

    result = _to_database_datetime(
        datetime(2026, 10, 1, 4, tzinfo=baku_timezone)
    )

    assert result == datetime(2026, 10, 1)
    assert result.tzinfo is None


def test_preserves_naive_database_datetime() -> None:
    value = datetime(2026, 10, 1)

    assert _to_database_datetime(value) is value


def test_preserves_utc_wall_time() -> None:
    result = _to_database_datetime(datetime(2026, 10, 1, tzinfo=UTC))

    assert result == datetime(2026, 10, 1)
