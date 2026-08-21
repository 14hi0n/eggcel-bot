import logging
from pathlib import Path

import httpx

from config import settings

logger = logging.getLogger(__name__)

_font_path: Path | None = None
_HEADERS = {"User-Agent": "Mozilla/5.0"}
_DOWNLOADED_FONT_PATH = Path("assets/fonts/runtime/font.ttf")


async def prepare_font() -> None:
    global _font_path

    source = settings.font_source

    if source.startswith(("http://", "https://")):
        logger.info("Downloading font from URL")

        _DOWNLOADED_FONT_PATH.parent.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(
            follow_redirects=True,
            http2=False,
            timeout=30.0,
            headers=_HEADERS,
        ) as client:
            response = await client.get(source)
            response.raise_for_status()

        _DOWNLOADED_FONT_PATH.write_bytes(response.content)
        _font_path = _DOWNLOADED_FONT_PATH

        logger.info("Font downloaded to %s", _font_path)
    else:
        _font_path = Path(source)

    if not _font_path.is_file():
        raise FileNotFoundError(f"Font file does not exist: {_font_path}")

    logger.info("Font is ready: %s", _font_path)


def get_font_path() -> Path:
    if _font_path is None:
        raise RuntimeError("Font has not been prepared")

    return _font_path
