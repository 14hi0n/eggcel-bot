import logging


def setup_logging() -> None:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        "bot.log",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    for name in (
        "handlers",
        "services",
        "database",
    ):
        logging.getLogger(name).setLevel(logging.DEBUG)
