import io

from PIL import Image, ImageDraw, ImageFont

from services.font_service import get_font_path

FONT_SIZE_RATIO = 0.16

TEXT_MAX_WIDTH_RATIO = 0.92
TEXT_MAX_HEIGHT_RATIO = 0.30

TEXT_TOP_PADDING_RATIO = 0.01
TEXT_BOTTOM_PADDING_RATIO = 0.01

TEXT_STROKE_RATIO = 0.04

LINE_GAP_PX = 0


def to_square(image: Image.Image) -> Image.Image:
    """Resizes the image to a square.

    Args:
        image (Image.Image): Image to resize.

    Returns:
        Image.Image: Resized square image.
    """
    side = min(image.size)
    return image.resize((side, side), Image.LANCZOS)


def wrap_text(
    text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw
) -> list[str]:
    """Returns a list of text lines that fit within max_width using the given font.

    Used to properly wrap text into multiple lines when it does not fit
    within the specified width.

    Args:
        text (str): Text to wrap.
        font (ImageFont.FreeTypeFont): Font used for measuring text width.
        max_width (int): Maximum allowed width for the text.
        draw (ImageDraw.ImageDraw): Drawing object used for text measurement.

    Returns:
        list[str]: List of wrapped text lines that fit within max_width.
    """
    words = text.split()
    if not words:
        return []

    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        if draw.textlength(test_line, font=font) <= max_width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def fit_text(
    text: str,
    max_w: int,
    max_h: int,
    start_size: int,
    draw: ImageDraw.ImageDraw,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Returns a font and wrapped lines that fit within max_w and max_h.

    Used to automatically adjust the font size to fit the text
    inside the available image area.

    Args:
        text (str): Text to fit.
        max_w (int): Maximum allowed text width.
        max_h (int): Maximum allowed text height.
        start_size (int): Initial font size.
        draw (ImageDraw.ImageDraw): Drawing object used for measurements.

    Returns:
        tuple[ImageFont.FreeTypeFont, list[str]]:
            A tuple containing the fitted font and wrapped text lines.
    """
    size = start_size
    font_path = str(get_font_path())

    while size > 10:
        font = ImageFont.truetype(font_path, size)
        lines = wrap_text(text, font, max_w, draw)

        # line_height = _get_line_height(font, lines)
        # total_height = len(lines) * line_height
        _, total_height = _get_text_layout(font, lines)

        if total_height <= max_h:
            return font, lines

        size -= 4

    font = ImageFont.truetype(font_path, 10)
    return font, wrap_text(text, font, max_w, draw)


def draw_text_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    img_w: int,
    start_y: int,
    is_top: bool,
) -> None:
    """Draws text lines on the image starting from the given Y coordinate.

    Args:
        draw (ImageDraw.ImageDraw): Drawing object used to render text.
        lines (list[str]): Lines of text to draw.
        font (ImageFont.FreeTypeFont): Font used for rendering text.
        img_w (int): Image width.
        start_y (int): Starting Y coordinate for drawing text.
        is_top (bool): If True, text is drawn from top to bottom.
            Otherwise, text is drawn from bottom to top.
    """
    offsets, total_height = _get_text_layout(font, lines)
    stroke_width = _get_stroke_width(font)
    block_top = start_y if is_top else start_y - total_height

    for line, offset in zip(lines, offsets, strict=True):
        draw.text(
            (img_w / 2, block_top + offset),
            line,
            font=font,
            fill="white",
            stroke_width=stroke_width,
            stroke_fill="black",
            anchor="ms",
        )


def render_meme_text(
    image: Image.Image,
    top_text: str | None,
    bottom_text: str,
    square: bool = False,
) -> Image.Image:
    image = image.convert("RGB")

    if square:
        image = to_square(image)

    with render_text_overlay(image.size, top_text, bottom_text) as overlay:
        image.paste(overlay, (0, 0), mask=overlay)

    return image


def render_text_overlay(
    size: tuple[int, int],
    top_text: str | None,
    bottom_text: str,
) -> Image.Image:
    """
    Возвращает прозрачное RGBA изображение с подписью.
    """
    w, h = size
    if w <= 0 or h <= 0:
        raise ValueError("Overlay dimensions must be positive")

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    ref_dim = min(w, h)

    max_w = int(w * TEXT_MAX_WIDTH_RATIO)
    max_h = int(ref_dim * TEXT_MAX_HEIGHT_RATIO)

    top_padding = int(h * TEXT_TOP_PADDING_RATIO)
    bottom_padding = int(h * TEXT_TOP_PADDING_RATIO)

    start_size = max(int(ref_dim * FONT_SIZE_RATIO), 16)

    captions = (
        (top_text, top_padding, True),
        (bottom_text, h - bottom_padding, False),
    )

    for text, start_y, is_top in captions:
        if not text:
            continue

        font, lines = fit_text(text.upper(), max_w, max_h, start_size, draw)
        draw_text_lines(
            draw,
            lines,
            font,
            w,
            start_y=start_y,
            is_top=is_top,
        )

    return overlay


def compress_for_telegram(image: Image.Image) -> bytes:
    """Compresses an image for sending to Telegram.

    Args:
        image (Image.Image): Image to compress.

    Returns:
        bytes: Compressed JPEG image as bytes.
    """
    image = image.convert("RGB")
    image.thumbnail((1600, 1600), Image.LANCZOS)

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)

    return buf.getvalue()


def _get_text_layout(
    font: ImageFont.FreeTypeFont,
    lines: list[str],
) -> tuple[list[float], float]:
    if not lines:
        return [], 0.0

    stroke = _get_stroke_width(font)
    boxes = [font.getbbox(line, anchor="ms", stroke_width=stroke) for line in lines]

    # Один шаг для всего блока, без пересечения границ соседних строк.
    step = max(
        (
            upper[3] - lower[1] + LINE_GAP_PX
            for upper, lower in zip(boxes[:-1], boxes[1:], strict=True)
        ),
        default=0.0,
    )

    top = min(i * step + box[1] for i, box in enumerate(boxes))
    bottom = max(i * step + box[3] for i, box in enumerate(boxes))
    offsets = [i * step - top for i in range(len(lines))]

    return offsets, bottom - top


def _get_stroke_width(font: ImageFont.FreeTypeFont) -> int:
    return max(1, round(font.size * TEXT_STROKE_RATIO))
