from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RoomFollow(Base):
    __tablename__ = "room_follows"
    __table_args__ = (
        UniqueConstraint("user_id", "room_id", "follow_type", name="uq_room_follows_user_room_type"),
        Index("ix_room_follows_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    room_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    follow_type: Mapped[str] = mapped_column(String(20), default="room", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
