def parse_meme_caption(caption: str) -> tuple[str | None, str]:
    lines = [line.strip() for line in caption.splitlines() if line.strip()]

    if not lines:
        raise ValueError("Caption is empty")

    if len(lines) == 1:
        return None, lines[0]

    return lines[0], lines[1]
