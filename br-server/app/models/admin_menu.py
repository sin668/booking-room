from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.admin_role import admin_role_menus

if TYPE_CHECKING:
    from app.models.admin_role import AdminRole


class AdminMenu(Base):
    __tablename__ = "admin_menus"
    __table_args__ = (
        CheckConstraint("type IN ('directory', 'menu', 'button')", name="ck_admin_menus_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("admin_menus.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    permission_code: Mapped[str | None] = mapped_column(
        String(120),
        unique=True,
        nullable=True,
        index=True,
    )
    path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    component: Mapped[str | None] = mapped_column(String(255), nullable=True)
    redirect: Mapped[str | None] = mapped_column(String(255), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sort: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    keep_alive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    parent: Mapped[AdminMenu | None] = relationship(
        "AdminMenu",
        remote_side=[id],
        back_populates="children",
        lazy="selectin",
    )
    children: Mapped[list[AdminMenu]] = relationship(
        "AdminMenu",
        back_populates="parent",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    roles: Mapped[list[AdminRole]] = relationship(
        "AdminRole",
        secondary=admin_role_menus,
        back_populates="menus",
        lazy="selectin",
    )
