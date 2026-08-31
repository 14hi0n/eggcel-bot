import logging

from telegram.error import NetworkError
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(_: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error

    if error is None:
        return

    if isinstance(error, TimeoutError):
        logger.warning("Telegram request timed out")
        return

    if isinstance(error, NetworkError):
        logger.warning("Telegram network error: %s", error)
        return

    logger.error(
        "Unhandled error: %s",
        error,
        exc_info=(type(error), error, error.__traceback__),
    )
