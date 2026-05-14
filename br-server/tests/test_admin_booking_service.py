"""Unit tests for admin booking service methods."""

import pytest
import uuid
from datetime import UTC, date, datetime, timedelta, time
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.booking import Booking
from app.models.coupon import Coupon, UserCoupon
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.schemas.booking import BookingCreate
from app.services.booking_service import (
    BookingAlreadyCancelledError,
    BookingCouponUnavailableError,
    BookingNotFoundError,
    admin_list_bookings,
    admin_get_booking,
    admin_cancel_booking,
    cancel_booking,
    create_booking,
)

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def _make_room(db: AsyncSession, room_id: int = 1, name: str = "Room 1"):
    room = StudyRoom(id=room_id, name=name, address="Address", status="open")
    db.add(room)
    return room


def _make_seat(db: AsyncSession, seat_id: int = 1, room_id: int = 1):
    seat = Seat(
        id=seat_id,
        room_id=room_id,
        seat_number="A1",
        zone="quiet",
        price_per_hour=Decimal("10.00"),
        status="available",
        row=1,
        col=1,
    )
    db.add(seat)
    return seat


def _make_booking(
    db: AsyncSession,
    booking_id: int = 1,
    seat_id: int = 1,
    room_id: int = 1,
    user_id: str = "user-1",
    booking_date: date = date(2026, 5, 1),
    status: str = "confirmed",
):
    now = datetime(2026, 5, 1, 10, 0, 0)
    booking = Booking(
        id=booking_id,
        seat_id=seat_id,
        user_id=user_id,
        room_id=room_id,
        date=booking_date,
        start_time=time(9, 0),
        end_time=time(11, 0),
        status=status,
        total_price=Decimal("20.00"),
        created_at=now,
        updated_at=now,
    )
    db.add(booking)
    return booking


def _make_coupon(
    db: AsyncSession,
    user_id: str = str(USER_ID),
    discount_amount: Decimal = Decimal("3.00"),
    min_order_amount: Decimal = Decimal("20.00"),
):
    now = datetime.now(UTC)
    coupon = Coupon(
        name="满20减3",
        description="全场通用",
        type="threshold_amount_off",
        discount_amount=discount_amount,
        discount_percent=None,
        min_order_amount=min_order_amount,
        scope="all",
        seat_zone=None,
        valid_from=now - timedelta(days=1),
        expires_at=now + timedelta(days=1),
        is_active=True,
    )
    db.add(coupon)
    return coupon


async def _make_user_coupon(
    db: AsyncSession,
    user_id: str = str(USER_ID),
):
    coupon = _make_coupon(db, user_id=user_id)
    await db.flush()
    user_coupon = UserCoupon(user_id=user_id, coupon_id=coupon.id, status="available")
    db.add(user_coupon)
    await db.flush()
    return user_coupon


@pytest.mark.asyncio
async def test_create_booking_service_without_coupon_sets_original_and_zero_discount(
    db_session: AsyncSession,
):
    _make_room(db_session, 1)
    seat = _make_seat(db_session, 1, 1)
    await db_session.flush()

    result = await create_booking(
        db_session,
        USER_ID,
        BookingCreate(
            seat_id=seat.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
        ),
    )

    assert result.original_price == Decimal("20.00")
    assert result.discount_amount == Decimal("0.00")
    assert result.total_price == Decimal("20.00")
    assert result.coupon_id is None


@pytest.mark.asyncio
async def test_create_booking_service_with_coupon_marks_coupon_used(
    db_session: AsyncSession,
):
    _make_room(db_session, 1)
    seat = _make_seat(db_session, 1, 1)
    user_coupon = await _make_user_coupon(db_session)

    result = await create_booking(
        db_session,
        USER_ID,
        BookingCreate(
            seat_id=seat.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            coupon_id=user_coupon.id,
        ),
    )

    assert result.original_price == Decimal("20.00")
    assert result.discount_amount == Decimal("3.00")
    assert result.total_price == Decimal("17.00")
    assert result.coupon_id == user_coupon.id
    await db_session.refresh(user_coupon)
    assert user_coupon.status == "used"
    assert user_coupon.used_booking_id == result.id
    assert user_coupon.used_at is not None


@pytest.mark.asyncio
async def test_create_booking_service_invalid_coupon_does_not_create_booking_or_mutate_coupon(
    db_session: AsyncSession,
):
    _make_room(db_session, 1)
    seat = _make_seat(db_session, 1, 1)
    user_coupon = await _make_user_coupon(db_session, user_id=str(OTHER_USER_ID))

    with pytest.raises(BookingCouponUnavailableError):
        await create_booking(
            db_session,
            USER_ID,
            BookingCreate(
                seat_id=seat.id,
                date=date(2026, 5, 1),
                start_time=time(9, 0),
                end_time=time(11, 0),
                coupon_id=user_coupon.id,
            ),
        )

    booking_ids = (await db_session.execute(select(Booking.id))).scalars().all()
    assert booking_ids == []
    await db_session.refresh(user_coupon)
    assert user_coupon.status == "available"
    assert user_coupon.used_booking_id is None
    assert user_coupon.used_at is None


@pytest.mark.asyncio
async def test_cancel_booking_service_restores_used_coupon(db_session: AsyncSession):
    _make_room(db_session, 1)
    seat = _make_seat(db_session, 1, 1)
    user_coupon = await _make_user_coupon(db_session)
    booking = _make_booking(db_session, 1, seat.id, 1, str(USER_ID), status="confirmed")
    booking.original_price = Decimal("20.00")
    booking.discount_amount = Decimal("3.00")
    booking.total_price = Decimal("17.00")
    booking.coupon_id = user_coupon.id
    await db_session.flush()
    user_coupon.status = "used"
    user_coupon.used_booking_id = booking.id
    user_coupon.used_at = datetime.now(UTC)
    await db_session.flush()

    result = await cancel_booking(db_session, booking.id, USER_ID)

    assert result.status == "cancelled"
    await db_session.refresh(user_coupon)
    assert user_coupon.status == "available"
    assert user_coupon.used_booking_id is None
    assert user_coupon.used_at is None


@pytest.mark.asyncio
async def test_admin_list_bookings_normal_pagination(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_seat(db_session, 1, 1)
    _make_booking(db_session, 1, 1, 1, "user-1")
    _make_booking(db_session, 2, 1, 1, "user-2")
    _make_booking(db_session, 3, 1, 1, "user-3")
    await db_session.flush()

    result = await admin_list_bookings(db_session, page=1, page_size=2)
    assert result.total == 3
    assert len(result.items) == 2
    assert result.page == 1
    assert result.page_size == 2


@pytest.mark.asyncio
async def test_admin_list_bookings_filter_by_status(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_seat(db_session, 1, 1)
    _make_booking(db_session, 1, 1, 1, "user-1", status="confirmed")
    _make_booking(db_session, 2, 1, 1, "user-2", status="cancelled")
    _make_booking(db_session, 3, 1, 1, "user-3", status="confirmed")
    await db_session.flush()

    result = await admin_list_bookings(db_session, status="confirmed")
    assert result.total == 2
    assert all(b.status == "confirmed" for b in result.items)


@pytest.mark.asyncio
async def test_admin_list_bookings_filter_by_room_id(db_session: AsyncSession):
    _make_room(db_session, 1, "Room A")
    _make_room(db_session, 2, "Room B")
    _make_seat(db_session, 1, 1)
    _make_seat(db_session, 2, 2)
    _make_booking(db_session, 1, 1, 1, "user-1")
    _make_booking(db_session, 2, 2, 2, "user-2")
    await db_session.flush()

    result = await admin_list_bookings(db_session, room_id=2)
    assert result.total == 1
    assert result.items[0].room_id == 2


@pytest.mark.asyncio
async def test_admin_list_bookings_filter_by_date_range(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_seat(db_session, 1, 1)
    _make_booking(db_session, 1, 1, 1, "user-1", booking_date=date(2026, 5, 1))
    _make_booking(db_session, 2, 1, 1, "user-2", booking_date=date(2026, 5, 10))
    _make_booking(db_session, 3, 1, 1, "user-3", booking_date=date(2026, 5, 15))
    await db_session.flush()

    result = await admin_list_bookings(
        db_session, date_start=date(2026, 5, 5), date_end=date(2026, 5, 12)
    )
    assert result.total == 1
    assert result.items[0].date == date(2026, 5, 10)


@pytest.mark.asyncio
async def test_admin_list_bookings_empty_result(db_session: AsyncSession):
    result = await admin_list_bookings(db_session)
    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_admin_get_booking(db_session: AsyncSession):
    _make_room(db_session, 1, "Room A")
    _make_seat(db_session, 1, 1)
    _make_booking(db_session, 1, 1, 1, "user-1")
    await db_session.flush()

    result = await admin_get_booking(db_session, 1)
    assert result.id == 1
    assert result.user_id == "user-1"
    assert result.seat.seat_number == "A1"
    assert result.room.name == "Room A"


@pytest.mark.asyncio
async def test_admin_get_booking_not_found(db_session: AsyncSession):
    with pytest.raises(BookingNotFoundError):
        await admin_get_booking(db_session, 999)


@pytest.mark.asyncio
async def test_admin_cancel_booking(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_seat(db_session, 1, 1)
    _make_booking(db_session, 1, 1, 1, "user-1", status="confirmed")
    await db_session.flush()

    result = await admin_cancel_booking(db_session, 1)
    assert result.status == "cancelled"


@pytest.mark.asyncio
async def test_admin_cancel_booking_already_cancelled(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_seat(db_session, 1, 1)
    _make_booking(db_session, 1, 1, 1, "user-1", status="cancelled")
    await db_session.flush()

    with pytest.raises(BookingAlreadyCancelledError):
        await admin_cancel_booking(db_session, 1)


@pytest.mark.asyncio
async def test_admin_cancel_booking_not_found(db_session: AsyncSession):
    with pytest.raises(BookingNotFoundError):
        await admin_cancel_booking(db_session, 999)
