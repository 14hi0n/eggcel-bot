import asyncio
from collections.abc import Callable, Mapping
from pathlib import Path

from PIL import Image

from services.animation_renderer import AnimationRenderer
from services.gemini_caption_generator import CaptionGenerator, MemeCaption
from services.meme_prompt_builder import MemePromptBuilder

OverlayRenderer = Callable[[tuple[int, int], str | None, str], Image.Image]


class AnimationService:
    def __init__(
        self,
        renderer: AnimationRenderer,
        caption_gererator: CaptionGenerator,
        overlay_renderer: OverlayRenderer,
        prompt_builder: MemePromptBuilder,
        max_duration: float = 30,
    ) -> None:
        if not 0 < max_duration < float("inf"):
            raise ValueError("Maximum duration must be positive and finite")

        self._renderer = renderer
        self._caption_gererator = caption_gererator
        self._overlay_renderer = overlay_renderer
        self._prompt_builder = prompt_builder
        self._max_duration = max_duration

    async def create_meme(
        self,
        *,
        source: Path,
        workdir: Path,
        duration: float,
        caption: MemeCaption | None = None,
        template_values: Mapping[str, str | None],
    ) -> Path:
        if not 0 < duration <= self._max_duration:
            raise ValueError("Animation duration is outside the allowed range")

        preview = workdir / "preview.png"
        overlay = workdir / "overlay.png"
        result = workdir / "result.mp4"

        await self._renderer.extract_middle_frame(source, preview)

        with Image.open(preview) as image:
            await asyncio.to_thread(image.load)

            if caption is None:
                # Eсли подпись не задана, значит нужно генерировать через нейронку.
                prompt = self._prompt_builder.build(template_values=template_values)
                caption = await self._caption_gererator(
                    image,
                    prompt,
                )

            # На основе превью получаем размер видео чтобы сделать оверлей
            size = image.size

            await asyncio.to_thread(self._save_overlay, size, caption, overlay)
            await self._renderer.render(source, overlay, result)

        if not result.is_file() or result.stat().st_size == 0:
            raise RuntimeError("Animation rendering no output")

        return result

    def _save_overlay(
        self,
        size: tuple[int, int],
        caption: MemeCaption,
        target: Path,
    ) -> None:
        with self._overlay_renderer(
            size,
            caption.top_text,
            caption.bottom_text,
        ) as layer:
            layer.save(target, format="PNG")
