import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)


class MemeStyleSelector:
    def __init__(self, path: Path, probability: float) -> None:
        self._path = path
        self._probability = probability
        self._styles = self._load_style() if probability > 0 else ()

    # def prepare(self) -> None:
    #     if self._probability == 0:
    #         self._styles = ()
    #         logger.info("Meme style are disabled")
    #         return

    #     self._styles = self._load_style()

    #     logger.info(
    #         "Loaded %d meme style from %s",
    #         len(self._styles),
    #         self._path,
    #     )

    def get_random_style(self) -> str | None:
        if self._probability == 0:
            return None

        if self._styles is None:
            raise RuntimeError("MemeStyleService is not prepared")

        if random.random() >= self._probability:
            return None

        style = random.choice(self._styles)
        logger.debug("Selected meme style: %s", style)

        return style

    def _load_style(self) -> tuple[str, ...]:
        styles = tuple(
            line
            for raw_line in self._path.read_text(encoding="utf-8").splitlines()
            if (line := raw_line.strip()) and not line.startswith("#")
        )

        if not styles:
            raise ValueError("No meme styles frond in %s", self._path)

        return styles
