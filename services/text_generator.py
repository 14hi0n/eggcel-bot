import logging

from google import genai
from google.genai import errors, types
from PIL import Image
from pydantic import BaseModel

from config import Config

logger = logging.getLogger(__name__)

_PROMPT = (
    "Ты пишешь подписи для классических Impact-мемов, которые будут нанесены "
    "белым шрифтом с чёрной обводкой сверху и/или снизу изображения.\n\n"
    "Подпись должна выглядеть так, будто её придумал обычный человек из "
    "аниме- или Telegram-сообщества, а не нейросеть.\n\n"
    "Не пытайся специально шутить. Не пытайся быть остроумным. "
    "Подпись может быть смешной, серьёзной, тупой, абсурдной, злой, "
    "эмоциональной или вообще выглядеть как случайная мысль. "
    "Главное - чтобы она ощущалась естественной.\n\n"
    "Избегай шаблонов:\n"
    "- «Когда...»\n"
    "- «Когда ты...»\n"
    "- «POV»\n"
    "- «Я:»\n"
    "- «Друг:»\n"
    "- «Никто:»\n"
    "- «Мы:»\n"
    "Используй такие конструкции только если без них действительно лучше.\n\n"
    "Мат полностью разрешён, но используй его только естественно. "
    "Не добавляй мат просто потому, что можешь.\n\n"
    "Подпись должна обыгрывать изображение, но не объяснять его. "
    "Не описывай буквально, что видно на картинке.\n\n"
    "Используй одну или две строки. "
    "Максимум шесть слов в строке. "
    "Не добавляй никаких пояснений, только текст для изображения."
)

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

_client = genai.Client(api_key=Config.GEMINI_API_KEY)


class _MemeTextSchema(BaseModel):
    top_text: str | None
    bottom_text: str


def generate_meme_caption(image: Image.Image) -> _MemeTextSchema | None:
    """
    Generates a meme caption based on an image.

    Args:
        image (Image.Image): The image for which to generate the caption.

    Returns:
        str: The generated meme caption.
    """
    try:
        response = _client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=[image, _PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_MemeTextSchema,
                safety_settings=_SAFETY_SETTINGS,
            ),
        )
    except errors.ClientError as esc:
        logger.warning(
            "Какая-то странная ошибка, которую стоит обработать: %s",
            esc,
        )
        raise

    # Если gemini не понравился input.
    # Например картинка или сам промпт.
    if (
        response.prompt_feedback is not None
        and response.prompt_feedback.block_reason is not None
    ):
        logger.warning(
            "Gemini INPUT feedback: block_reason=%s safety_ratings=%s",
            response.prompt_feedback.block_reason,
            response.prompt_feedback.safety_ratings,
        )
        return None

    if not response.candidates:
        logger.warning(
            "Gemini returned no candidates. prompt_feedback=%s",
            response.prompt_feedback,
        )
        return None

    candidate = response.candidates[0]

    # OUTPUT был остановлен фильтром
    if candidate.finish_reason == types.FinishReason.SAFETY:
        logger.warning(
            "Gemini OUTPIUT blocked: safity_rating=%s",
            candidate.safety_ratings,
        )
        return None

    if response.parsed is None:
        logger.warning(
            "Gemini response could not be parsed. finish_reason=%s",
            candidate.finish_reason,
        )
        return None

    return response.parsed
