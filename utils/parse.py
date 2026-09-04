def parse_user_caption(caption: str) -> tuple[str | None, str]:
    """Разделяет пользовательскую подпись на верхний и нижний текст.

    Args:
        caption (str): Подпись, которую нужно разделить.

    Raises:
        ValueError: Если подпись пустая или содержит больше двух текстовых блоков.

    Returns:
        tuple[str | None, str]: Верхний и нижний текст.
        Если текст без переноса строки, верхний текст будет None.
    """

    if not caption.strip():
        raise ValueError("Caption is empty")

    lines = [line.strip() for line in caption.splitlines() if line.strip()]

    if not lines:
        raise ValueError("Caption is empty")

    if len(lines) > 2:
        raise ValueError("Caption must contain at most two text blocks")

    if len(lines) == 1:
        return None, lines[0]

    return lines[0], lines[1]


def parse_caption_with_marker(
    caption: str, split_marker: str
) -> tuple[str | None, str]:
    """Разделяет подпись на верхний и нижний текст по маркеру.

    Если маркера нет, вся подпись считается нижним текстом.
    Маркер можно использовать только один раз. При его наличии текст
    с обеих сторон должен быть непустым.

    Args:
        caption (str): Подпись, которую нужно разделить.
        split_marker (str): Маркер, разделяющий верхний и нижний текст.

    Raises:
        ValueError: Если подпись или маркер пустые, маркер встречается
        несколько раз либо одна из частей подписи пуста.

    Returns:
        tuple[str | None, str]: Верхний и нижний текст. Если маркера нет,
        верхний текст будет равен None.
    """

    if not caption.strip():
        raise ValueError("Caption is empty")

    if not split_marker:
        raise ValueError("Split marker is empty.")

    top, marker, bottom = caption.partition(split_marker)

    if not marker:
        return None, top.strip()

    if split_marker in bottom or not top.strip() or not bottom.strip():
        raise ValueError("Invalid caption split marker")

    return top.strip(), bottom.strip()
