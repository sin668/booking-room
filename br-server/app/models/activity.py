from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_html: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cover_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    participant_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


class ActivityCoupon(Base):
    __tablename__ = "activity_coupons"
    __table_args__ = (
        CheckConstraint("total_quantity >= 0", name="ck_activity_coupons_total_quantity_non_negative"),
        CheckConstraint("claimed_quantity >= 0", name="ck_activity_coupons_claimed_quantity_non_negative"),
        CheckConstraint("claimed_quantity <= total_quantity", name="ck_activity_coupons_claimed_not_over_total"),
        CheckConstraint("per_user_limit > 0", name="ck_activity_coupons_per_user_limit_positive"),
        Index("ix_activity_coupons_activity_id", "activity_id"),
        Index("ix_activity_coupons_coupon_id", "coupon_id"),
        Index("ix_activity_coupons_activity_sort", "activity_id", "sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), nullable=False)
    coupon_id: Mapped[int] = mapped_column(ForeignKey("coupons.id"), nullable=False)
    total_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    claimed_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    per_user_limit: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    claim_starts_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    claim_ends_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    display_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    display_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
