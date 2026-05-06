import pytest
from datetime import date, time
from decimal import Decimal

from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.services.seat_service import (
    admin_get_seat,
    admin_list_seats,
    bulk_create_seats,
    create_seat,
    delete_seat,
    toggle_seat_status,
    update_seat,
)


@pytest.fixture
async def db_session():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.core.database import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def sample_room(db_session):
    room = StudyRoom(
        name="测试自习室",
        address="测试地址",
        business_hours="08:00-22:00",
        min_price=Decimal("15.00"),
    )
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)
    return room


@pytest.fixture
async def sample_seat(db_session, sample_room):
    seat = Seat(
        room_id=sample_room.id,
        seat_number="A-01",
        zone="quiet",
        price_per_hour=Decimal("6.00"),
        row=1,
        col=1,
    )
    db_session.add(seat)
    await db_session.commit()
    await db_session.refresh(seat)
    return seat


async def test_admin_list_seats(db_session, sample_room):
    seat1 = Seat(
        room_id=sample_room.id, seat_number="A-01", zone="quiet",
        price_per_hour=Decimal("6.00"), row=1, col=1,
    )
    seat2 = Seat(
        room_id=sample_room.id, seat_number="A-02", zone="quiet",
        price_per_hour=Decimal("6.00"), row=1, col=2,
    )
    db_session.add_all([seat1, seat2])
    await db_session.commit()

    result = await admin_list_seats(db_session, sample_room.id)
    assert len(result) == 2


async def test_admin_list_seats_with_zone_filter(db_session, sample_room):
    seat1 = Seat(
        room_id=sample_room.id, seat_number="A-01", zone="quiet",
        price_per_hour=Decimal("6.00"), row=1, col=1,
    )
    seat2 = Seat(
        room_id=sample_room.id, seat_number="B-01", zone="keyboard",
        price_per_hour=Decimal("8.00"), row=2, col=1,
    )
    db_session.add_all([seat1, seat2])
    await db_session.commit()

    result = await admin_list_seats(db_session, sample_room.id, zone="quiet")
    assert len(result) == 1
    assert result[0].zone == "quiet"


async def test_admin_list_seats_with_status_filter(db_session, sample_room):
    seat1 = Seat(
        room_id=sample_room.id, seat_number="A-01", zone="quiet",
        price_per_hour=Decimal("6.00"), status="available", row=1, col=1,
    )
    seat2 = Seat(
        room_id=sample_room.id, seat_number="A-02", zone="quiet",
        price_per_hour=Decimal("6.00"), status="maintenance", row=1, col=2,
    )
    db_session.add_all([seat1, seat2])
    await db_session.commit()

    result = await admin_list_seats(db_session, sample_room.id, status="maintenance")
    assert len(result) == 1
    assert result[0].status == "maintenance"


async def test_admin_list_seats_room_not_found(db_session):
    with pytest.raises(ValueError, match="Room 999 not found"):
        await admin_list_seats(db_session, 999)


async def test_admin_get_seat(db_session, sample_seat):
    result = await admin_get_seat(db_session, sample_seat.id)
    assert result.id == sample_seat.id
    assert result.seat_number == "A-01"
    assert result.room_name == "测试自习室"


async def test_admin_get_seat_not_found(db_session):
    with pytest.raises(ValueError, match="Seat 999 not found"):
        await admin_get_seat(db_session, 999)


async def test_create_seat(db_session, sample_room):
    data = {
        "seat_number": "B-01",
        "zone": "keyboard",
        "price_per_hour": Decimal("8.00"),
        "row": 2,
        "col": 1,
    }
    result = await create_seat(db_session, sample_room.id, data)
    assert result.id is not None
    assert result.seat_number == "B-01"
    assert result.zone == "keyboard"
    assert result.status == "available"
    assert result.room_name == "测试自习室"


async def test_create_seat_duplicate_number(db_session, sample_room, sample_seat):
    data = {
        "seat_number": "A-01",
        "zone": "keyboard",
        "price_per_hour": Decimal("8.00"),
        "row": 2,
        "col": 1,
    }
    with pytest.raises(ValueError, match="已存在相同编号"):
        await create_seat(db_session, sample_room.id, data)


async def test_bulk_create_seats_single_zone(db_session, sample_room):
    zone_configs = [
        {
            "prefix": "Q",
            "start_number": 1,
            "rows": 2,
            "cols": 3,
            "zone": "quiet",
            "price_per_hour": Decimal("6.00"),
            "floor": 3,
        }
    ]
    count = await bulk_create_seats(db_session, sample_room.id, zone_configs)
    assert count == 6


async def test_bulk_create_seats_multiple_zones(db_session, sample_room):
    zone_configs = [
        {
            "prefix": "Q",
            "start_number": 1,
            "rows": 1,
            "cols": 2,
            "zone": "quiet",
            "price_per_hour": Decimal("6.00"),
            "floor": 3,
        },
        {
            "prefix": "K",
            "start_number": 1,
            "rows": 1,
            "cols": 3,
            "zone": "keyboard",
            "price_per_hour": Decimal("8.00"),
            "floor": 3,
        },
    ]
    count = await bulk_create_seats(db_session, sample_room.id, zone_configs)
    assert count == 5


async def test_bulk_create_seats_number_conflict(db_session, sample_room, sample_seat):
    zone_configs = [
        {
            "prefix": "A",
            "start_number": 1,
            "rows": 1,
            "cols": 1,
            "zone": "quiet",
            "price_per_hour": Decimal("6.00"),
            "floor": 3,
        }
    ]
    with pytest.raises(ValueError, match="以下座位编号已存在"):
        await bulk_create_seats(db_session, sample_room.id, zone_configs)


async def test_bulk_create_seats_empty_list(db_session, sample_room):
    count = await bulk_create_seats(db_session, sample_room.id, [])
    assert count == 0


async def test_update_seat(db_session, sample_seat):
    result = await update_seat(db_session, sample_seat.id, {"price_per_hour": Decimal("10.00")})
    assert result.price_per_hour == Decimal("10.00")
    assert result.seat_number == "A-01"
    assert result.room_name == "测试自习室"


async def test_update_seat_number_conflict(db_session, sample_room):
    seat1 = Seat(
        room_id=sample_room.id, seat_number="A-01", zone="quiet",
        price_per_hour=Decimal("6.00"), row=1, col=1,
    )
    seat2 = Seat(
        room_id=sample_room.id, seat_number="B-01", zone="keyboard",
        price_per_hour=Decimal("8.00"), row=2, col=1,
    )
    db_session.add_all([seat1, seat2])
    await db_session.commit()
    await db_session.refresh(seat1)
    await db_session.refresh(seat2)

    with pytest.raises(ValueError, match="已存在相同编号"):
        await update_seat(db_session, seat1.id, {"seat_number": "B-01"})


async def test_update_seat_not_found(db_session):
    with pytest.raises(ValueError, match="Seat 999 not found"):
        await update_seat(db_session, 999, {"price_per_hour": Decimal("10.00")})


async def test_delete_seat(db_session, sample_seat):
    await delete_seat(db_session, sample_seat.id)

    result = await admin_list_seats(db_session, sample_seat.room_id)
    assert len(result) == 0


async def test_delete_seat_with_active_bookings(db_session, sample_room, sample_seat):
    booking = Booking(
        seat_id=sample_seat.id,
        user_id="user-123",
        room_id=sample_room.id,
        date=date(2026, 5, 6),
        start_time=time(10, 0),
        end_time=time(12, 0),
        status="confirmed",
        total_price=Decimal("12.00"),
    )
    db_session.add(booking)
    await db_session.commit()

    with pytest.raises(ValueError, match="活跃预约"):
        await delete_seat(db_session, sample_seat.id)


async def test_delete_seat_not_found(db_session):
    with pytest.raises(ValueError, match="Seat 999 not found"):
        await delete_seat(db_session, 999)


async def test_toggle_seat_status(db_session, sample_seat):
    result = await toggle_seat_status(db_session, sample_seat.id, "maintenance")
    assert result.status == "maintenance"

    result = await toggle_seat_status(db_session, sample_seat.id, "available")
    assert result.status == "available"


async def test_toggle_seat_status_not_found(db_session):
    with pytest.raises(ValueError, match="Seat 999 not found"):
        await toggle_seat_status(db_session, 999, "maintenance")
