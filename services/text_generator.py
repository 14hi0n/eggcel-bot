from dataclasses import dataclass
from enum import Enum
from typing import Literal

from google import genai
from google.genai import errors, types
from PIL import Image
from pydantic import BaseModel, ValidationError

from config import settings
from services.meme_prompt_builder import CAPTION_SPLIT_MARKER, meme_prompt_builder
from utils.parse import parse_caption_with_marker

from .exceptions.gemini import (
    GeminiError,
    GeminiInputBlockedError,
    GeminiNoCandidatesError,
    GeminiNSFWError,
    GeminiOutputBlockedError,
    GeminiParseError,
    GeminiUnavailableError,
)

# Работает только для OUTPUT
_SAFETY_SETTINGS = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    ),
]

_client = genai.Client(api_key=settings.gemini_api_key)


"""
Gemini должен вернуть одну из двух форм.

Успешная генерация:
{
  "result": {
    "verdict": "OK",
    "caption": "ВЕРХНИЙ ТЕКСТ <SPLIT> НИЖНИЙ ТЕКСТ"
  }
}

Или отказ:
{
  "result": {
    "verdict": "REJECTED",
    "reason": "NSFW"
  }
}

Такая структура нужна, чтобы успешный результат всегда содержал
bottom_text, а отказ имел отдельный формат.
"""


class _RejectionReason(str, Enum):
    """Причины отказа в генерации."""

    NSFW = "NSFW"


class _OkResult(BaseModel):
    """Результат успешной генерации."""

    verdict: Literal["OK"]
    caption: str


class _RejectResult(BaseModel):
    """Результат отказа в генерации."""

    verdict: Literal["REJECTED"]
    reason: _RejectionReason


class _MemeTextSchema(BaseModel):
    """Ответ Gemini: успешная генерация или отказ."""

    result: _OkResult | _RejectResult


@dataclass(frozen=True, slots=True)
class MemeCaption:
    top_text: str | None
    bottom_text: str


async def generate_meme_caption(image: Image.Image) -> MemeCaption:
    """
     Генерирует текст для мема на основе изображения.

    Args:
        image (Image.Image): Изображение для которого сгенерить текст.

    Returns:
        MemeCaption: Объект содержащий top_text и bottom_text.
    """
    prompt = meme_prompt_builder.build()

    try:
        response = await _client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=[image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_MemeTextSchema,
                safety_settings=_SAFETY_SETTINGS,
            ),
        )

    except errors.ServerError as exc:
        if exc.code == 503:
            raise GeminiUnavailableError(
                exc.message or "Gemini API unavailable."
            ) from exc
        raise GeminiError(str(exc)) from exc

    except errors.ClientError as exc:
        raise GeminiError(str(exc)) from exc

    # Если gemini не понравился input.
    # Например картинка или сам промпт.
    if (
        response.prompt_feedback is not None
        and response.prompt_feedback.block_reason is not None
    ):
        raise GeminiInputBlockedError(
            f"block_reason={response.prompt_feedback.block_reason}, "
            f"safety_ratings={response.prompt_feedback.safety_ratings}"
        )

    if not response.candidates:
        raise GeminiNoCandidatesError(f"prompt_feedback={response.prompt_feedback}")

    candidate = response.candidates[0]

    # OUTPUT был остановлен фильтром
    if candidate.finish_reason == types.FinishReason.SAFETY:
        raise GeminiOutputBlockedError(f"safety_ratings={candidate.safety_ratings}")

    raw_response = response.text

    if raw_response is None:
        raise GeminiParseError(
            "Gemini returned no text: "
            f"finish_reason={candidate.finish_reason}, "
            f"response_id={response.response_id}"
        )

    try:
        meme_data = _MemeTextSchema.model_validate_json(raw_response)
    except ValidationError as exc:
        raise GeminiParseError(
            "Could not parse Gemini response: "
            f"finish_reason={candidate.finish_reason}, "
            f"response_id={response.response_id}, "
            f"model_version={response.model_version}, "
            f"errors={exc.errors(include_url=False)}, "
            f"raw_response={raw_response[:500]!r}"
        ) from exc

    result = meme_data.result

    if isinstance(result, _RejectResult):
        raise GeminiNSFWError(f"Gemini rejected input: {result.reason.value}")

    try:
        top_text, bottom_text = parse_caption_with_marker(
            result.caption, CAPTION_SPLIT_MARKER
        )
    except ValueError as exc:
        raise GeminiParseError(str(exc)) from exc

    return MemeCaption(
        top_text=top_text,
        bottom_text=bottom_text,
    )
