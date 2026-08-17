from datetime import datetime
from enum import Enum

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Time, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PaymentMethod(str, Enum):
    balance = "balance"
    wechat = "wechat"


class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seat_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    room_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    start_time: Mapped[datetime] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime] = mapped_column(Time, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="confirmed", nullable=False)
    original_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    coupon_id: Mapped[int | None] = mapped_column(ForeignKey("user_coupons.id"), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(20), default="balance", nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), default="paid", nullable=False)
    payment_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
    prepay_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transaction_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    payment_check_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_payment_check_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    penalty_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    refund_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    cancel_policy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    booking_type: Mapped[str] = mapped_column(String(20), default="seat", nullable=False, index=True)
    course_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("courses.id"), nullable=True)
    lesson_ids: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    schedule_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
