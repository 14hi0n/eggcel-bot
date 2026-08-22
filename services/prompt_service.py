from pathlib import Path

from anyio import Path as AsyncPath

from config import settings

_REQUIRED_PROMPT = (
    "Если на изображении содержится порнография или обнажённая натура, "
    "верни verdict='REJECTED' и reason='NSFW'. "
    "Не создавай в этом случае подпись. "
    "Во всех остальных случаях верни verdict='OK' и сгенерируй подпись."
)


class PromptLoader:
    def __init__(self, path: Path):
        self.path = AsyncPath(path)
        self._cached_text: str | None = None
        self._cached_mtime: float | None = None

    async def get(self) -> str:
        stat = await self.path.stat()

        if self._cached_text is None or stat.st_mtime != self._cached_mtime:
            self._cached_text = await self.path.read_text(encoding="utf-8")
            self._cached_mtime = stat.st_mtime_ns

        return self._cached_text


class MemeCaptionPrompt:
    def __init__(self, loader: PromptLoader):
        self.loader = loader

    async def get(self) -> str:
        row_prompt = await self.loader.get()
        return f"{row_prompt}\n\n{_REQUIRED_PROMPT}"


meme_caption_prompt = MemeCaptionPrompt(
    PromptLoader(settings.meme_prompt_path),
)
