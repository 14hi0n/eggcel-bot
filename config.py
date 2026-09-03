from pathlib import Path
from typing import Annotated, Any

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from utils.logging_config import LogLevel

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DATABASE_PATH = DATA_DIR / "database.db"


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram
    telegram_bot_token: str
    admin_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)
    webhook_url: str | None = None
    webhook_port: int = 8080
    webhook_path: str = "telegram"

    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-3.5-flash-lite"

    # Meme
    meme_prompt_path: Path = Path(BASE_DIR / "assets/prompts/example.txt")
    meme_probability: float = Field(default=0.1, ge=0.0, le=1.0)
    meme_style_probability: float = Field(default=0.33, ge=0.0, le=1.0)
    meme_style_path: Path = Path(BASE_DIR / "assets/prompts/meme_style.txt")
    font_source: str = "assets/fonts/default/Oswald-Bold.ttf"

    # Etc
    database_url: str = f"sqlite+aiosqlite:///{DEFAULT_DATABASE_PATH}"
    log_level: LogLevel = LogLevel.INFO
    log_to_file: bool = False

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [int(x.strip()) for x in value.split(",") if x.strip()]
        return value

    @field_validator("webhook_url")
    @classmethod
    def normalize_webhook_url(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip().rstrip("/")
        return value or None


settings = _Settings()  # type: ignore[call-arg]
