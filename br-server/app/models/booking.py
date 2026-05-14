from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seat_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
