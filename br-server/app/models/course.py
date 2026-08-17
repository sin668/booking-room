from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("study_rooms.id"), nullable=False)
    teacher_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teachers.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cover_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(3, 1), default=0.0, nullable=False)
    enrollment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    schedule: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    custom_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    full_package_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    full_custom_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
