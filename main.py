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

from config import Config
from database.manager import DatabaseManager
from handlers.chat_approval import chat_moderate_callback, on_activate, on_bot_added
from handlers.photo import handle_private_photo, handle_public_photo
from handlers.start import start

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def post_init(application: Application) -> None:
    db = DatabaseManager(Config.DATABASE_URL)
    await db.init()
    application.bot_data["db"] = db


async def post_shutdown(application: Application) -> None:
    db: DatabaseManager = application.bot_data["db"]
    await db.close()


def main() -> None:

    application = (
        ApplicationBuilder()
        .token(Config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    application.add_handler(
        CommandHandler("start", start, filters=filters.ChatType.PRIVATE)
    )
    application.add_handler(CommandHandler("activate", on_activate))

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

    application.run_polling()


if __name__ == "__main__":
    main()
