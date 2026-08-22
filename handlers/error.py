import logging

from telegram import Update
from telegram.error import NetworkError
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error

    if isinstance(error, TimeoutError):
        logger.warning("Telegram request time out")
        return

    if isinstance(error, NetworkError):
        logger.warning("Telegram network error: %s", error)
        return

    logger.error(
        "Unhundled error: %s",
        error,
        exc_info=(type(error), error, error.__traceback__),
    )
