import enum
from typing import Optional

from sqlalchemy import BigInteger, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class ChatStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Chat(BaseModel):
    __tablename__ = "chats"

    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        unique=True,
    )
    chat_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    chat_title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    tag_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[ChatStatus] = mapped_column(
        Enum(ChatStatus, name="chat_status"),
        nullable=False,
        default=ChatStatus.pending,
    )
