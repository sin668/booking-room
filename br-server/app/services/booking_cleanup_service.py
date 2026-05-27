"""Cleanup for unpaid booking payment holds."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.services import coupon_service


async def cleanup_unpaid_bookings(
    db: AsyncSession,
    *,
    older_than_minutes: int = 15,
) -> int:
    """Cancel stale pending WeChat bookings and restore attached coupons."""
    cutoff = datetime.now() - timedelta(minutes=older_than_minutes)
    result = await db.execute(
        select(Booking).where(
            Booking.payment_status == "pending",
            Booking.status == "pending",
            Booking.created_at < cutoff,
        )
    )
    bookings = result.scalars().all()

    for booking in bookings:
        booking.status = "cancelled"
        await coupon_service.restore_user_coupon_for_booking(db, booking)

    await db.flush()
    return len(bookings)
