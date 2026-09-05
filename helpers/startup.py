import logging
from pathlib import Path

from build_version import APP_VERSION
from config import settings

logger = logging.getLogger(__name__)


def log_startup_summary(*, font_path: Path) -> None:
    values = (
        ("Version", APP_VERSION),
        ("Mode", "webhook" if settings.webhook_url else "polling"),
        ("Gemini model", settings.gemini_model),
        ("Prompt", settings.meme_prompt_path.resolve()),
        ("Font source", settings.font_source),
        ("Font file", font_path.resolve()),
        ("Meme probability", f"{settings.meme_probability:.0%}"),
        ("Meme style probability", f"{settings.meme_style_probability:.0%}"),
        ("Console log level", settings.log_level),
    )

    logger.info("%s BOT CONFIGURATION %s", "=" * 10, "=" * 10)

    for name, value in values:
        logger.info("%-22s %s", f"{name}:", value)

    logger.info("%s", "=" * 41)
