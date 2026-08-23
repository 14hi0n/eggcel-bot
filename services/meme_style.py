import logging
import random

from config import settings

_STYLES = [
    "Сделай эту подпись абсурдной и немного бессмысленной.",
    "Сделай эту подпись сухой и невозмутимой.",
    "Сделай эту подпись слегка агрессивной, но не своди её к простому оскорблению.",
    "Сделай эту подпись неожиданно доброй.",
    "Сделай эту подпись драматичной, будто произошло что-то очень серьёзное.",
    "Сделай эту подпись максимально тупой, но естественной.",
    "Сделай эту подпись слегка экзистенциальной.",
    "Сделай эту подпись агрессивной.",
]


logger = logging.getLogger(__name__)


def get_random_style() -> str | None:
    if random.random() >= settings.meme_style_probability:
        return None

    style = random.choice(_STYLES)
    logger.info("A random caption style has been selected: %s", style)
    return style
