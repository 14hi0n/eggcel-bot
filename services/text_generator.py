from google import genai
from google.genai import types
from PIL import Image
from pydantic import BaseModel

from config import Config

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


class _MemeTextSchema(BaseModel):
    top_text: str | None
    bottom_text: str


def generate_meme_caption(image: Image.Image) -> _MemeTextSchema:
    """
    Generates a meme caption based on an image.

    Args:
        image (Image.Image): The image for which to generate the caption.

    Returns:
        str: The generated meme caption.
    """
    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=Config.GEMINI_MODEL,
        contents=[image, _PROMPT],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_MemeTextSchema,
        ),
    )

    meme_data: _MemeTextSchema = response.parsed
    return meme_data
