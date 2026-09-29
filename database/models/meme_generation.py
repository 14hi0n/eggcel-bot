import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from database.models.base import BaseModel


class GenerationMode(str, enum.Enum):
    ai = "ai"
    custom = "custom"


class MediaType(str, enum.Enum):
    photo = "photo"
    animation = "animation"


class GenerationStatus(str, enum.Enum):
    processing = "processing"
    success = "success"
    nsfw_rejected = "nsfw_rejected"
    blocked = "blocked"
    error = "error"


class MemeGeneration(BaseModel):
    __tablename__ = "meme_generations"

    __table_args__ = (
        Index(
            "ix_meme_generations_chat_created_at",
            "chat_id",
            "created_at",
        ),
        Index(
            "ix_meme_generations_user_created_at",
            "user_id",
            "created_at",
        ),
    )

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chats.id"),
        nullable=False,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    telegram_message_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    mode: Mapped[GenerationMode] = mapped_column(
        Enum(GenerationMode, name="generation_mode"),
        nullable=False,
    )

    media_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="generation_media_type"),
        nullable=False,
    )

    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus, name="generation_status"),
        nullable=False,
        default=GenerationStatus.processing,
    )

    error_code: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
