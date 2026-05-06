import pytest
from datetime import date, time
from decimal import Decimal

from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.services.study_room_service import (
    admin_get_room,
    admin_list_rooms,
    create_room,
    delete_room,
    toggle_room_status,
    update_room,
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


async def test_admin_list_rooms(db_session):
    room1 = StudyRoom(name="Room1", address="Addr1", min_price=Decimal("10.00"))
    room2 = StudyRoom(name="Room2", address="Addr2", min_price=Decimal("20.00"))
    db_session.add_all([room1, room2])
    await db_session.commit()

    result = await admin_list_rooms(db_session)
    assert result.total == 2
    assert len(result.items) == 2


async def test_admin_list_rooms_with_status_filter(db_session):
    open_room = StudyRoom(
        name="OpenRoom", address="Addr1", status="open", min_price=Decimal("10.00")
    )
    closed_room = StudyRoom(
        name="ClosedRoom", address="Addr2", status="closed", min_price=Decimal("20.00")
    )
    db_session.add_all([open_room, closed_room])
    await db_session.commit()

    result = await admin_list_rooms(db_session, status="open")
    assert result.total == 1
    assert result.items[0].name == "OpenRoom"


async def test_admin_get_room(db_session, sample_room):
    result = await admin_get_room(db_session, sample_room.id)
    assert result.id == sample_room.id
    assert result.name == "测试自习室"
    assert result.address == "测试地址"
    assert result.status == "open"
    assert result.created_at is not None
    assert result.updated_at is not None


async def test_admin_get_room_not_found(db_session):
    with pytest.raises(ValueError, match="Room 999 not found"):
        await admin_get_room(db_session, 999)


async def test_admin_get_room_with_seat_counts(db_session, sample_room):
    seat1 = Seat(
        room_id=sample_room.id,
        seat_number="A1",
        zone="zone1",
        floor=3,
        price_per_hour=Decimal("10.00"),
        status="available",
        row=1,
        col=1,
    )
    seat2 = Seat(
        room_id=sample_room.id,
        seat_number="A2",
        zone="zone1",
        floor=3,
        price_per_hour=Decimal("10.00"),
        status="available",
        row=1,
        col=2,
    )
    seat3 = Seat(
        room_id=sample_room.id,
        seat_number="A3",
        zone="zone1",
        floor=3,
        price_per_hour=Decimal("10.00"),
        status="maintenance",
        row=1,
        col=3,
    )
    db_session.add_all([seat1, seat2, seat3])
    await db_session.commit()

    result = await admin_get_room(db_session, sample_room.id)
    assert result.seat_count == 3
    assert result.available_seat_count == 2


async def test_create_room(db_session):
    data = {
        "name": "New Room",
        "address": "New Address",
        "description": "A new room",
        "business_hours": "09:00-21:00",
        "min_price": Decimal("25.00"),
    }
    result = await create_room(db_session, data)
    assert result.id is not None
    assert result.name == "New Room"
    assert result.address == "New Address"
    assert result.status == "open"


async def test_update_room(db_session, sample_room):
    result = await update_room(db_session, sample_room.id, {"name": "Updated Name"})
    assert result.name == "Updated Name"
    assert result.address == "测试地址"


async def test_delete_room(db_session, sample_room):
    await delete_room(db_session, sample_room.id)
    with pytest.raises(ValueError):
        await admin_get_room(db_session, sample_room.id)


async def test_delete_room_with_active_bookings(db_session, sample_room):
    seat = Seat(
        room_id=sample_room.id,
        seat_number="A1",
        zone="zone1",
        floor=3,
        price_per_hour=Decimal("10.00"),
        row=1,
        col=1,
    )
    db_session.add(seat)
    await db_session.commit()
    await db_session.refresh(seat)

    booking = Booking(
        seat_id=seat.id,
        user_id="user-123",
        room_id=sample_room.id,
        date=date(2026, 5, 6),
        start_time=time(10, 0),
        end_time=time(12, 0),
        status="confirmed",
        total_price=Decimal("20.00"),
    )
    db_session.add(booking)
    await db_session.commit()

    with pytest.raises(ValueError, match="活跃预约"):
        await delete_room(db_session, sample_room.id)


async def test_toggle_room_status(db_session, sample_room):
    result = await toggle_room_status(db_session, sample_room.id, "closed")
    assert result.status == "closed"

    result = await toggle_room_status(db_session, sample_room.id, "open")
    assert result.status == "open"


async def test_toggle_room_status_not_found(db_session):
    with pytest.raises(ValueError, match="Room 999 not found"):
        await toggle_room_status(db_session, 999, "closed")
