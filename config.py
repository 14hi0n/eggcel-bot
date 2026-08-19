import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    ADMIN_IDS: list[int] = [
        int(user_id.strip())
        for user_id in os.getenv("ADMIN_IDS", "").split(",")
        if user_id.strip()
    ]
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    MEME_PROBABILITY: float = float(os.getenv("MEME_PROBABILITY", 0.1))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.db")
    ENABLE_HEALTH_SERVER: str = os.getenv("ENABLE_HEALTH_SERVER", "0")
