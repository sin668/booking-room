from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.admin_role import AdminRole, admin_user_roles


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("user_type IN ('app', 'admin')", name="ck_users_user_type"),
        Index("ix_users_phone", "phone", unique=True, postgresql_where="phone IS NOT NULL"),
        Index("ix_users_username", "username", unique=True, postgresql_where="username IS NOT NULL"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_type: Mapped[str] = mapped_column(
        String(10),
        default="app",
        nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(
        String(11),
        nullable=True,
    )
    nickname: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    invite_code: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
    )
    wechat_openid: Mapped[str | None] = mapped_column(
        String(128),
        unique=True,
        nullable=True,
    )
    username: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    mobile: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    avatar: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    is_super_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        index=True,
        nullable=False,
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    roles: Mapped[list[AdminRole]] = relationship(
        "AdminRole",
        secondary="admin_user_roles",
        back_populates="users",
        lazy="selectin",
    )
