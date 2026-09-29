from dataclasses import dataclass
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
class OverallStatistics:
    pass


@dataclass(frozen=True, slots=True)
class UserStatistics:
    telegram_user_id: int


@dataclass(frozen=True, slots=True)
class ChatStatistics:
    telegram_chat_id: int


StatisticQuery: TypeAlias = OverallStatistics | UserStatistics | ChatStatistics


def parse_statistics_query(
    arguments: Sequence[str],
) -> StatisticQuery | None:
    match arguments:
        case []:
            # если пустой - значит запросили общую стату
            return OverallStatistics()
        case [scope, raw_id] if scope.casefold() == "user":
            # если запросили стату для user
            try:
                return UserStatistics(telegram_user_id=int(raw_id))
            except ValueError:
                return None
        case [scope, raw_id] if scope.casefold() == "chat":
            try:
                return ChatStatistics(telegram_chat_id=int(raw_id))
            except ValueError:
                return None
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
            case OverallStatistics():
                stats = await service.get_overall_statistics()
                text = GenerationStatisticsMessages.overall(stats)
            case UserStatistics(telegram_user_id=user_id):
                stats = await service.get_user_statistics(user_id)
                text = GenerationStatisticsMessages.for_user(
                    stats,
                    user_id,
                )
            case ChatStatistics(telegram_chat_id=chat_id):
                stats = await service.get_chat_statistics(chat_id)
                text = GenerationStatisticsMessages.for_chat(
                    stats,
                    chat_id,
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
