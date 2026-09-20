def normalize_impact_meme(text: str):
    """Нормализует текст от Gemini для impoct-мема.

    Args:
        text (str): Текст от Gemini.
    """

    text = text.strip().replace("—", "-").replace("ё", "е").upper()

    if text.endswith(("...", "…")):
        return text

    return text.rstrip(".,")
