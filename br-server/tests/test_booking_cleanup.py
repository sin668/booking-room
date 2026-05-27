"""Tests for stale unpaid booking cleanup."""

import uuid
from datetime import date, datetime, timedelta, time
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.coupon import Coupon, UserCoupon
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.services.booking_cleanup_service import cleanup_unpaid_bookings

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
async def cleanup_seed(db_session: AsyncSession):
    room = StudyRoom(name="Cleanup Room", address="123 Test St", status="open", min_price=10)
    db_session.add(room)
    await db_session.flush()
    seat = Seat(
        room_id=room.id,
        seat_number="A-01",
        zone="quiet",
        position="window",
        floor=3,
        price_per_hour=Decimal("15.00"),
        status="available",
        row=1,
        col=1,
    )
    coupon = Coupon(
        name="满20减3",
        description="全场通用",
        type="threshold_amount_off",
        discount_amount=Decimal("3.00"),
        min_order_amount=Decimal("20.00"),
        scope="all",
        valid_from=datetime.now() - timedelta(days=1),
        expires_at=datetime.now() + timedelta(days=1),
        is_active=True,
    )
    db_session.add_all([seat, coupon])
    await db_session.flush()
    return room, seat, coupon


@pytest.mark.asyncio
async def test_cleanup_unpaid_bookings_cancels_stale_and_restores_coupon(
    db_session: AsyncSession,
    cleanup_seed,
):
    room, seat, coupon = cleanup_seed
    user_coupon = UserCoupon(user_id=str(USER_ID), coupon_id=coupon.id, status="used")
    db_session.add(user_coupon)
    await db_session.flush()
    booking = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=date(2026, 5, 1),
        start_time=time(9, 0),
        end_time=time(12, 0),
        status="confirmed",
        total_price=Decimal("42.00"),
        coupon_id=user_coupon.id,
        payment_method="wechat",
        payment_status="pending",
        payment_provider="wechat",
        created_at=datetime.now() - timedelta(minutes=20),
    )
    db_session.add(booking)
    await db_session.flush()
    user_coupon.used_booking_id = booking.id
    user_coupon.used_at = datetime.now() - timedelta(minutes=20)
    await db_session.flush()

    count = await cleanup_unpaid_bookings(db_session)

    assert count == 1
    assert booking.status == "cancelled"
    assert user_coupon.status == "available"
    assert user_coupon.used_booking_id is None
    assert user_coupon.used_at is None


@pytest.mark.asyncio
async def test_cleanup_unpaid_bookings_keeps_recent_pending(
    db_session: AsyncSession,
    cleanup_seed,
):
    room, seat, _coupon = cleanup_seed
    booking = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=date(2026, 5, 1),
        start_time=time(9, 0),
        end_time=time(12, 0),
        status="confirmed",
        total_price=Decimal("45.00"),
        payment_method="wechat",
        payment_status="pending",
        payment_provider="wechat",
        created_at=datetime.now() - timedelta(minutes=5),
    )
    db_session.add(booking)
    await db_session.flush()

    count = await cleanup_unpaid_bookings(db_session)

    assert count == 0
    assert booking.status == "confirmed"


@pytest.mark.asyncio
async def test_cleanup_unpaid_bookings_no_pending_is_safe(db_session: AsyncSession):
    assert await cleanup_unpaid_bookings(db_session) == 0
