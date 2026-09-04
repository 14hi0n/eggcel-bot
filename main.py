import logging

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
from handlers.error import error_handler
from handlers.pending_chats import show_pending_chats
from handlers.photo import handle_private_photo, handle_public_photo
from handlers.remove_chat import remove_chat
from handlers.start import start
from handlers.version import show_version
from helpers.startup import log_startup_summary
from services.font_service import get_font_path, prepare_font
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    await prepare_font()

    db = DatabaseManager(settings.database_url)
    application.bot_data["db"] = db
    await db.init()

    log_startup_summary(font_path=get_font_path())

    logger.info("Application initialization completed")


async def post_shutdown(application: Application) -> None:
    db: DatabaseManager = application.bot_data["db"]

    if db is not None:
        await db.close()

    logger.info("%s BOT STOPPED %s", "=" * 10, "=" * 10)


def main() -> None:
    setup_logging(
        log_to_file=settings.log_to_file,
        console_level=settings.log_level,
    )

    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    admin_filter = filters.User(user_id=settings.admin_ids)

    application.add_error_handler(error_handler)
    application.add_handler(
        CommandHandler("start", start, filters=filters.ChatType.PRIVATE)
    )
    application.add_handler(
        CommandHandler(
            "add",
            add_chat,
            filters=admin_filter,
        )
    )
    application.add_handler(
        CommandHandler(
            "remove",
            remove_chat,
            filters=admin_filter,
        )
    )
    application.add_handler(
        CommandHandler(
            "pending",
            show_pending_chats,
            filters=admin_filter,
        )
    )
    application.add_handler(
        CommandHandler(
            ("version", "ver"),
            show_version,
            filters=admin_filter,
        )
    )

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
        CallbackQueryHandler(
            chat_moderate_callback,
            pattern=r"^chat:(approved|rejected):",
        )
    )

    if settings.webhook_url:
        application.run_webhook(
            listen="0.0.0.0",
            port=settings.webhook_port,
            url_path=settings.webhook_path,
            webhook_url=f"{settings.webhook_url}/{settings.webhook_path}",
        )
    else:
        application.run_polling()


if __name__ == "__main__":
    main()
