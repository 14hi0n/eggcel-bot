import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import Config
from handlers.photo import handle_private_photo, handle_public_photo
from handlers.start import start

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def main() -> None:
    application = ApplicationBuilder().token(Config.TELEGRAM_BOT_TOKEN).build()

    application.add_handler(
        MessageHandler(filters.PHOTO & filters.ChatType.GROUPS, handle_public_photo)
    )
    application.add_handler(
        MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, handle_private_photo)
    )
    application.add_handler(CommandHandler("start", start))

    application.run_polling()


if __name__ == "__main__":
    main()
