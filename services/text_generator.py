from enum import Enum
from typing import Literal

from google import genai
from google.genai import errors, types
from PIL import Image
from pydantic import BaseModel

from config import settings
from services.meme_prompt import meme_prompt_builder

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
    "top_text": null,
    "bottom_text": "КУДА Я ОПЯТЬ ПОПАЛ"
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
    top_text: str | None = None
    bottom_text: str


class _RejectResult(BaseModel):
    """Результат отказа в генерации."""

    verdict: Literal["REJECTED"]
    reason: _RejectionReason


class _MemeTextSchema(BaseModel):
    """Ответ Gemini: успешная генерация или отказ."""

    result: _OkResult | _RejectResult


async def generate_meme_caption(image: Image.Image) -> _OkResult | None:
    """
    Generates a meme caption based on an image.

    Args:
        image (Image.Image): The image for which to generate the caption.

    Returns:
        str: The generated meme caption.
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
                exc.message or "Gemini API unvailable."
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
        raise GeminiOutputBlockedError(f"safity_rating={candidate.safety_ratings}")

    meme_data = response.parsed

    if not isinstance(meme_data, _MemeTextSchema):
        raise GeminiParseError(
            f"Could not parse Gemini response. finish_reason={candidate.finish_reason}"
        )

    result = meme_data.result

    if isinstance(result, _RejectResult):
        raise GeminiNSFWError(f"Gemini rejected input: {result.reason.value}")

    return result
