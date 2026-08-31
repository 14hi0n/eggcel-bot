import logging
from logging.handlers import RotatingFileHandler


def setup_logging(*, log_to_file: bool) -> None:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    handlers: list[logging.Handler] = [console_handler]

    if log_to_file:
        file_handler = RotatingFileHandler(
            "bot.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )

        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(
        level=logging.WARNING,
        handlers=handlers,
        force=True,
    )

    for name in ("__main__", "main", "handlers", "services", "database"):
        logging.getLogger(name).setLevel(logging.DEBUG)

    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logging.getLogger("telegram.ext.Application").setLevel(logging.INFO)
