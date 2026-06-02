from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserIdentityVerification(Base):
    __tablename__ = "user_identity_verifications"
    __table_args__ = (
        Index("ix_user_identity_verifications_user_id_status", "user_id", "status"),
        Index("ix_user_identity_verifications_id_card_hash", "id_card_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    real_name: Mapped[str] = mapped_column(String(50), nullable=False)
    id_card_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    id_card_masked: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="verified", nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship("User", back_populates="identity_verifications")
