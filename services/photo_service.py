import asyncio
from collections.abc import Mapping

from PIL import Image

from config import settings
from services.gemini_caption_generator import CaptionGenerator, MemeCaption
from services.meme_prompt_builder import MemePromptBuilder
from services.meme_renderer import compress_for_telegram, render_meme_text


class PhotoService:
    def __init__(
        self,
        prompt_builder: MemePromptBuilder,
        caption_generator: CaptionGenerator,
    ) -> None:
        self._prompt_builder = prompt_builder
        self._caption_generator = caption_generator

    async def create_meme(
        self,
        *,
        image: Image.Image,
        template_values: Mapping[str, str | None],
        caption: MemeCaption | None = None,
    ) -> bytes:
        if caption is None:
            # Если от юзера нет caption
            # значит нужно генериь текст мема через нейронку
            prompt = self._prompt_builder.build(template_values=template_values)
            caption = await self._caption_generator(image, prompt)

        return await asyncio.to_thread(
            self._render_and_compress,
            image,
            caption,
        )

    @staticmethod
    def _render_and_compress(
        image: Image.Image,
        caption: MemeCaption,
    ) -> bytes:
        with render_meme_text(
            image=image,
            top_text=caption.top_text,
            bottom_text=caption.bottom_text,
            square=settings.meme_square,
        ) as rendered_image:
            return compress_for_telegram(rendered_image)
