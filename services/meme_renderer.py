import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "impact.ttf"
FONT_SIZE_RATIO = 0.10


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

    while size > 10:
        font = ImageFont.truetype(str(FONT_PATH), size)
        lines = wrap_text(text, font, max_w, draw)

        total_height = len(lines) * size * 1.1

        if total_height <= max_h:
            return font, lines

        size -= 4

    font = ImageFont.truetype(str(FONT_PATH), 10)
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
    line_height = int(font.size * 1.0)
    stroke_width = max(1, font.size // 15)

    lines_to_draw = lines if is_top else lines[::-1]
    y = start_y

    for line in lines_to_draw:
        anchor = "ma" if is_top else "mb"

        draw.text(
            (img_w / 2, y),
            line,
            font=font,
            fill="white",
            stroke_width=stroke_width,
            stroke_fill="black",
            anchor=anchor,
        )

        y += line_height if is_top else -line_height


def render_meme_text(image: Image.Image, top: str | None, bottom: str) -> Image.Image:
    """
    Main function for generating a meme with text overlay.

    Takes an image, top text, and bottom text, then returns
    the image with the meme-style text applied.

    Args:
        image (Image.Image): Original Pillow image.
        top (str | None): Text displayed at the top.
        bottom (str): Text displayed at the bottom.

    Returns:
        Image.Image: Image with meme text overlay.
    """
    image = image.convert("RGB")
    image = to_square(image)

    draw = ImageDraw.Draw(image)
    w, h = image.size

    max_w = int(w * 0.92)
    max_h = int(h * 0.40)
    padding = int(h * 0.02)

    start_size = max(int(h * FONT_SIZE_RATIO), 16)

    if top:
        font, lines = fit_text(top.upper(), max_w, max_h, start_size, draw)
        draw_text_lines(draw, lines, font, w, start_y=padding, is_top=True)

    font, lines = fit_text(bottom.upper(), max_w, max_h, start_size, draw)

    draw_text_lines(draw, lines, font, w, start_y=h - padding, is_top=False)

    return image


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
