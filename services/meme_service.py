import asyncio

from PIL import Image

from services.meme_renderer import compress_for_telegram, render_meme_text


async def create_meme(
    image: Image.Image,
    top_text: str | None,
    bottom_text: str,
) -> bytes:
    return await asyncio.to_thread(
        _render_and_compress,
        image,
        top_text,
        bottom_text,
    )


def _render_and_compress(
    image: Image.Image,
    top_text: str | None,
    bottom_text: str,
) -> bytes:
    rendered_image = render_meme_text(
        image,
        top_text,
        bottom_text,
    )

    return compress_for_telegram(rendered_image)
