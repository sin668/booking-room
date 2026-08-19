from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(512), nullable=True)
    title: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rating: Mapped[float] = mapped_column(Numeric(3, 1), default=0.0, nullable=False)
    bio: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    specialty: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="专业方向，如考研政治"
    )
    teaching_years: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    education: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="学历：本科/硕士/博士"
    )
    school: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    teaching_tags: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="教学特色标签，逗号分隔"
    )
    qualifications: Mapped[list | None] = mapped_column(
        JSON, nullable=True, comment="资质认证列表，如 [{\"name\":..., \"sub\":...}]"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
