from pathlib import Path

from config import settings
from services.meme_style import MemeStyleSelector

_REQUIRED_PROMPT = (
    "Если на изображении содержится порнография или обнажённая натура, "
    "верни verdict='REJECTED' и reason='NSFW'. "
    "Не создавай в этом случае подпись. "
    "Во всех остальных случаях верни verdict='OK' и сгенерируй подпись."
)


class MemeCaptionPromptBuilder:
    def __init__(
        self,
        prompt_path: Path,
        style_service: MemeStyleSelector,
    ):
        self._base_prompt = self._load_prompt(prompt_path)
        self.loader = prompt_path
        self.style_service = style_service

    def build(self) -> str:
        parts = [self._base_prompt]
        style = self.style_service.get_random_style()

        if style is not None:
            parts.append(style)

        parts.append(_REQUIRED_PROMPT)

        return "\n\n".join(parts)

    @staticmethod
    def _load_prompt(path: Path) -> str:
        prompt = path.read_text(encoding="utf-8").strip()

        if not prompt:
            raise ValueError("Prompt file is empty: %s", path)

        return prompt


meme_prompt_builder = MemeCaptionPromptBuilder(
    prompt_path=settings.meme_prompt_path,
    style_service=MemeStyleSelector(
        path=settings.meme_style_path,
        probability=settings.meme_style_probability,
    ),
)
