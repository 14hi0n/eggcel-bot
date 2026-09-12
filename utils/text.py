def normalize_impact_meme(text: str):
    """Удаляет лишнюю пунктуацию в конце предложений.

    Args:
        text (str): Текст.
    """

    text = text.strip()

    if text.endswith(("...", "…")):
        return text

    return text.rstrip(".,")
