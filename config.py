from pathlib import Path
from typing import Annotated, Any

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    telegram_bot_token: str
    admin_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)
    webhook_url: str | None = None
    webhook_port: str = "8080"
    webhook_path: str = "telegram"

    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash-lite"
    meme_prompt_path: Path = Path(BASE_DIR / "assets/prompts/example.txt")
    meme_probability: float = 0.1
    meme_style_probability: float = 0.33

    font_source: str = "assets/fonts/default/Oswald-Bold.ttf"

    database_url: str = "sqlite+aiosqlite:///database.db"

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [int(x.strip()) for x in value.split(",") if x.strip()]
        return value


settings = _Settings()
