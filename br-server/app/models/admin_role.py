from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.admin_menu import AdminMenu
    from app.models.admin_user import AdminUser


admin_user_roles = Table(
    "admin_user_roles",
    Base.metadata,
    Column(
        "admin_user_id",
        ForeignKey("admin_users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "admin_role_id",
        ForeignKey("admin_roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    UniqueConstraint("admin_user_id", "admin_role_id", name="uq_admin_user_roles"),
)


admin_role_menus = Table(
    "admin_role_menus",
    Base.metadata,
    Column(
        "admin_role_id",
        ForeignKey("admin_roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "admin_menu_id",
        ForeignKey("admin_menus.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    UniqueConstraint("admin_role_id", "admin_menu_id", name="uq_admin_role_menus"),
)


class AdminRole(Base):
    __tablename__ = "admin_roles"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'disabled')", name="ck_admin_roles_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    users: Mapped[list[AdminUser]] = relationship(
        "AdminUser",
        secondary=admin_user_roles,
        back_populates="roles",
        lazy="selectin",
    )
    menus: Mapped[list[AdminMenu]] = relationship(
        "AdminMenu",
        secondary=admin_role_menus,
        back_populates="roles",
        lazy="selectin",
    )
