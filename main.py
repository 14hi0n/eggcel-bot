import logging
import threading

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import settings
from database.manager import DatabaseManager
from handlers.add_chat import add_chat
from handlers.chat_approval import chat_moderate_callback, on_bot_added
from handlers.photo import handle_private_photo, handle_public_photo
from handlers.remove_chat import remove_chat
from handlers.start import start
from healch_server import run_health_server
from services.font_service import prepare_font
from utils.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    logger.info("Init application")

    await prepare_font()

    db = DatabaseManager(settings.database_url)
    await db.init()
    application.bot_data["db"] = db


async def post_shutdown(application: Application) -> None:
    db: DatabaseManager = application.bot_data["db"]
    await db.close()


def main() -> None:
    if settings.enable_health_server == "1":
        logger.debug(
            "ENABLE_HEALTH_SERVER is enabled; Starting a thread with run_health_server"
        )
        threading.Thread(
            target=run_health_server,
            daemon=True,
        ).start()

    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    application.add_handler(
        CommandHandler("start", start, filters=filters.ChatType.PRIVATE)
    )
    # application.add_handler(CommandHandler("activate", on_activate))
    application.add_handler(CommandHandler("add", add_chat))
    application.add_handler(CommandHandler("remove", remove_chat))

    application.add_handler(
        ChatMemberHandler(on_bot_added, ChatMemberHandler.MY_CHAT_MEMBER)
    )
    application.add_handler(
        MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, handle_public_photo)
    )
    application.add_handler(
        MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_private_photo)
    )

    application.add_handler(
        CallbackQueryHandler(chat_moderate_callback, pattern=r"^chat:(approve|reject):")
    )

    if settings.webhook_url:
        logger.info("Launching bot with webhook")
        application.run_webhook(
            listen="0.0.0.0",
            port=settings.webhook_port,
            webhook_url=f"{settings.webhook_url}/{settings.webhook_path}",
        )
    else:
        logger.info("Launching bot with polling")
        application.run_polling()


if __name__ == "__main__":
    main()
