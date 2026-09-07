from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domain.review_status import ReviewStatus


class Review(Base):
    """学员评价。

    一条评价挂靠一个订单，`booking_id` 唯一约束由数据库强制"一单一评"。
    `course_id` / `teacher_id` 从订单冗余而来，支撑课程与老师两个维度的单表索引过滤
    （Course 没有 teacher_id，不冗余则两个维度都要 join bookings）。
    关联数据（课程名、老师名、用户昵称头像）一律批量 select 后在 service 层组装，
    本模型不声明 relationship，避免 async 序列化触发 MissingGreenlet。
    """

    __tablename__ = "reviews"
    # 复合索引的最左前缀已覆盖按 course_id / teacher_id / user_id 的单列过滤，
    # 且列表查询恒为「按维度过滤 + 按 created_at 排序」，故不再建冗余的单列索引
    __table_args__ = (
        Index("ix_reviews_course_id_created_at", "course_id", "created_at"),
        Index("ix_reviews_teacher_id_created_at", "teacher_id", "created_at"),
        Index("ix_reviews_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
    )
    teacher_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False, comment="综合星级 1-5")
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    images: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="评价图片 URL 列表，最多 9 张")
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="评价标签列表，最多 5 个")
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ReviewStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    reject_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reply_content: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="机构回复")
    reply_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # ponytail: 纯审计字段，无查询需求，故不加 FK（仓库亦无 admin 外键先例）
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
