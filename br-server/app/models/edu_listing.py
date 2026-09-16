from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domain.edu_listing_status import EduListingStatus


class EduListing(Base):
    """教培供需信息。

    完全独立于 teachers / courses / study_rooms，仅通过 user_id 关联发布者。
    单表用 listing_type 区分教（tutor 家教 / training 培训班）与学（demand 求教），
    综合广场天然混排。关联数据（发布者昵称/头像/认证状态）一律批量 select 后在
    service 层组装，本模型不声明 relationship，避免 async 序列化触发 MissingGreenlet。
    """

    __tablename__ = "edu_listings"
    __table_args__ = (
        CheckConstraint(
            "listing_type IN ('tutor', 'training', 'demand')",
            name="ck_edu_listings_listing_type",
        ),
        Index("ix_edu_listings_type_status_created", "listing_type", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    listing_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="tutor 家教 / training 培训班 / demand 求教"
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="科目分类")
    teaching_mode: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="授课/求学方式，如线上/线下/上门"
    )
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_unit: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="价格单位，如 元/小时")
    area: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="服务区域")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    images: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="图片 URL 列表，最多 3 张")
    available_times: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="可授课/可求学时间列表")
    status: Mapped[str] = mapped_column(
        String(20),
        default=EduListingStatus.PENDING.value,
        nullable=False,
        index=True,
    )
    reject_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # ponytail: 纯审计字段，无查询需求，故不加 FK（与 review 模块一致）
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
