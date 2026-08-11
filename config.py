import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    ADMIN_IDS: list[int] = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    MEME_PROBABILITY: float = float(os.getenv("MEME_PROBABILITY", 0.1))
    ALLOWED_CHAT_IDS: list[int] = list(
        map(int, os.getenv("ALLOWED_CHAT_IDS", "").split(","))
    )
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.db")
