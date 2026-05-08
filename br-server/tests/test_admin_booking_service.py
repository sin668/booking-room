"""Unit tests for admin booking service methods."""

import pytest
from datetime import date, datetime, time
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.services.booking_service import (
    admin_list_bookings,
    admin_get_booking,
    admin_cancel_booking,
    BookingNotFoundError,
    BookingAlreadyCancelledError,
)


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
