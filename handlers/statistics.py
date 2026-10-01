import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Sequence, TypeAlias

from telegram import Update
from telegram.ext import ContextTypes

from services.exceptions.meme_generation import (
    GenerationChatNotFoundError,
    GenerationUserNotFoundError,
)
from services.meme_generation_service import MemeGenerationService
from texts.statistics import GenerationStatisticsMessages


@dataclass(frozen=True, slots=True)
class StatisticsPeriod:
    start_at: datetime
    end_at: datetime
    label: str


@dataclass(frozen=True, slots=True)
class OverallStatistics:
    period: StatisticsPeriod | None = None


@dataclass(frozen=True, slots=True)
class UserStatistics:
    telegram_user_id: int
    period: StatisticsPeriod | None = None


@dataclass(frozen=True, slots=True)
class ChatStatistics:
    telegram_chat_id: int
    period: StatisticsPeriod | None = None


StatisticQuery: TypeAlias = OverallStatistics | UserStatistics | ChatStatistics

_DAY_PATTERN = re.compile(r"\d{2}/\d{2}/\d{4}")
_MONTH_PATTERN = re.compile(r"\d{2}/\d{4}")
_YEAR_PATTERN = re.compile(r"\d{4}")


def parse_statistics_period(
    value: str,
    *,
    now: datetime | None = None,
) -> StatisticsPeriod | None:
    if value.casefold() == "today":
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            current = current.replace(tzinfo=UTC)
        current = current.astimezone(UTC)
        start_at = datetime(
            current.year,
            current.month,
            current.day,
            tzinfo=UTC,
        )
        return StatisticsPeriod(
            start_at=start_at,
            end_at=start_at + timedelta(days=1),
            label=f"{start_at:%m/%d/%Y} (UTC)",
        )

    try:
        if _DAY_PATTERN.fullmatch(value):
            start_at = datetime.strptime(value, "%m/%d/%Y").replace(tzinfo=UTC)
            end_at = start_at + timedelta(days=1)
        elif _MONTH_PATTERN.fullmatch(value):
            start_at = datetime.strptime(value, "%m/%Y").replace(tzinfo=UTC)
            if start_at.month == 12:
                end_at = datetime(start_at.year + 1, 1, 1, tzinfo=UTC)
            else:
                end_at = datetime(
                    start_at.year,
                    start_at.month + 1,
                    1,
                    tzinfo=UTC,
                )
        elif _YEAR_PATTERN.fullmatch(value):
            start_at = datetime.strptime(value, "%Y").replace(tzinfo=UTC)
            end_at = datetime(start_at.year + 1, 1, 1, tzinfo=UTC)
        else:
            return None
    except (OverflowError, ValueError):
        return None

    return StatisticsPeriod(
        start_at=start_at,
        end_at=end_at,
        label=f"{value} (UTC)",
    )


def parse_statistics_query(
    arguments: Sequence[str],
    *,
    now: datetime | None = None,
) -> StatisticQuery | None:
    match arguments:
        case []:
            # если пустой - значит запросили общую стату
            return OverallStatistics()
        case [raw_period]:
            period = parse_statistics_period(raw_period, now=now)
            return OverallStatistics(period=period) if period is not None else None
        case [scope, raw_id] | [scope, raw_id, _] if scope.casefold() in {
            "user",
            "chat",
        }:
            try:
                entity_id = int(raw_id)
            except ValueError:
                return None

            period = None
            if len(arguments) == 3:
                period = parse_statistics_period(arguments[2], now=now)
                if period is None:
                    return None

            if scope.casefold() == "user":
                return UserStatistics(
                    telegram_user_id=entity_id,
                    period=period,
                )

            return ChatStatistics(
                telegram_chat_id=entity_id,
                period=period,
            )
        case _:
            return None


async def show_generation_statistics(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message

    if message is None:
        return

    query = parse_statistics_query(context.args or [])

    if query is None:
        await message.reply_text(GenerationStatisticsMessages.usage())
        return

    service: MemeGenerationService = context.bot_data["meme_generation_service"]

    try:
        match query:
            case OverallStatistics(period=period):
                stats = await service.get_overall_statistics(
                    start_at=period.start_at if period is not None else None,
                    end_at=period.end_at if period is not None else None,
                )
                text = GenerationStatisticsMessages.overall(
                    stats,
                    period_label=period.label if period is not None else None,
                )
            case UserStatistics(telegram_user_id=user_id, period=period):
                stats = await service.get_user_statistics(
                    user_id,
                    start_at=period.start_at if period is not None else None,
                    end_at=period.end_at if period is not None else None,
                )
                text = GenerationStatisticsMessages.for_user(
                    stats,
                    user_id,
                    period_label=period.label if period is not None else None,
                )
            case ChatStatistics(telegram_chat_id=chat_id, period=period):
                stats = await service.get_chat_statistics(
                    chat_id,
                    start_at=period.start_at if period is not None else None,
                    end_at=period.end_at if period is not None else None,
                )
                text = GenerationStatisticsMessages.for_chat(
                    stats,
                    chat_id,
                    period_label=period.label if period is not None else None,
                )

            case _:
                raise RuntimeError("Unknown error")
    except GenerationUserNotFoundError as exc:
        text = GenerationStatisticsMessages.user_not_found(
            telegram_user_id=exc.telegram_user_id
        )
    except GenerationChatNotFoundError as exc:
        text = GenerationStatisticsMessages.chat_not_found(
            telegram_chat_id=exc.telegram_chat_id
        )

    await message.reply_text(text)
