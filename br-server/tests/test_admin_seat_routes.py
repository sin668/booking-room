import pytest
from collections.abc import AsyncGenerator
from datetime import date, time
from decimal import Decimal
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_admin
from app.core.database import get_db
from app.core.redis import get_redis
from app.main import app
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom


@pytest.fixture
async def admin_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Client with admin auth and DB overrides."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: AsyncMock()
    app.dependency_overrides[get_current_admin] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_room_with_seat(db_session):
    room = StudyRoom(name="测试自习室", address="测试地址", min_price=Decimal("15.00"))
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)

    seat = Seat(
        room_id=room.id,
        seat_number="A-01",
        zone="quiet",
        price_per_hour=Decimal("6.00"),
        row=1,
        col=1,
    )
    db_session.add(seat)
    await db_session.commit()
    await db_session.refresh(seat)

    return room, seat


NESTED_URL = "/api/v1/admin/rooms/{room_id}/seats"
FLAT_URL = "/api/v1/admin/seats"


# ---- Room-nested endpoints ----


@pytest.mark.asyncio
async def test_admin_create_seat(admin_client, sample_room_with_seat):
    room = sample_room_with_seat[0]
    url = NESTED_URL.format(room_id=room.id)
    payload = {
        "seat_number": "B-01",
        "zone": "keyboard",
        "price_per_hour": "8.00",
        "row": 2,
        "col": 1,
    }
    resp = await admin_client.post(url, json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["seat_number"] == "B-01"
    assert data["room_id"] == room.id


@pytest.mark.asyncio
async def test_admin_create_seat_duplicate(admin_client, sample_room_with_seat):
    room, seat = sample_room_with_seat
    url = NESTED_URL.format(room_id=room.id)
    payload = {
        "seat_number": "A-01",
        "zone": "quiet",
        "price_per_hour": "6.00",
        "row": 1,
        "col": 1,
    }
    resp = await admin_client.post(url, json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_admin_create_seat_room_not_found(admin_client):
    url = NESTED_URL.format(room_id=999)
    payload = {
        "seat_number": "X-01",
        "zone": "quiet",
        "price_per_hour": "5.00",
        "row": 1,
        "col": 1,
    }
    resp = await admin_client.post(url, json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_bulk_create_seats(admin_client, sample_room_with_seat):
    room = sample_room_with_seat[0]
    url = f"{NESTED_URL.format(room_id=room.id)}/bulk/"
    payload = {
        "seats": [
            {
                "zone": "quiet",
                "rows": 2,
                "cols": 2,
                "prefix": "Q",
                "start_number": 1,
                "price_per_hour": "6.00",
                "floor": 3,
            }
        ]
    }
    resp = await admin_client.post(url, json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["created"] == 4


@pytest.mark.asyncio
async def test_admin_bulk_create_seats_conflict(admin_client, sample_room_with_seat):
    room, seat = sample_room_with_seat
    url = f"{NESTED_URL.format(room_id=room.id)}/bulk/"
    payload = {
        "seats": [
            {
                "zone": "quiet",
                "rows": 1,
                "cols": 1,
                "prefix": "A",
                "start_number": 1,
                "price_per_hour": "6.00",
                "floor": 3,
            }
        ]
    }
    resp = await admin_client.post(url, json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_admin_list_seats(admin_client, sample_room_with_seat):
    room = sample_room_with_seat[0]
    url = NESTED_URL.format(room_id=room.id)
    resp = await admin_client.get(url)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any(s["seat_number"] == "A-01" for s in data)


@pytest.mark.asyncio
async def test_admin_list_seats_with_filters(admin_client, db_session):
    room = StudyRoom(name="多座位自习室", address="地址", min_price=Decimal("10.00"))
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)

    seat1 = Seat(
        room_id=room.id, seat_number="A-01", zone="quiet",
        price_per_hour=Decimal("6.00"), row=1, col=1, status="available",
    )
    seat2 = Seat(
        room_id=room.id, seat_number="K-01", zone="keyboard",
        price_per_hour=Decimal("8.00"), row=1, col=1, status="maintenance",
    )
    db_session.add_all([seat1, seat2])
    await db_session.commit()

    url = NESTED_URL.format(room_id=room.id)

    resp = await admin_client.get(url, params={"zone": "quiet"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["zone"] == "quiet"

    resp2 = await admin_client.get(url, params={"status": "maintenance"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2) == 1
    assert data2[0]["status"] == "maintenance"


# ---- Flat seat endpoints ----


@pytest.mark.asyncio
async def test_admin_get_seat(admin_client, sample_room_with_seat):
    _, seat = sample_room_with_seat
    resp = await admin_client.get(f"{FLAT_URL}/{seat.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["seat_number"] == "A-01"
    assert data["room_name"] == "测试自习室"


@pytest.mark.asyncio
async def test_admin_get_seat_not_found(admin_client):
    resp = await admin_client.get(f"{FLAT_URL}/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_seat(admin_client, sample_room_with_seat):
    _, seat = sample_room_with_seat
    resp = await admin_client.put(f"{FLAT_URL}/{seat.id}", json={"zone": "vip"})
    assert resp.status_code == 200
    assert resp.json()["zone"] == "vip"


@pytest.mark.asyncio
async def test_admin_update_seat_not_found(admin_client):
    resp = await admin_client.put(f"{FLAT_URL}/999", json={"zone": "vip"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_delete_seat(admin_client, sample_room_with_seat):
    _, seat = sample_room_with_seat
    resp = await admin_client.delete(f"{FLAT_URL}/{seat.id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_admin_delete_seat_not_found(admin_client):
    resp = await admin_client.delete(f"{FLAT_URL}/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_delete_seat_with_booking(admin_client, db_session):
    room = StudyRoom(name="预约测试自习室", address="地址", min_price=Decimal("10.00"))
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)

    seat = Seat(
        room_id=room.id, seat_number="A-01", zone="quiet",
        price_per_hour=Decimal("6.00"), row=1, col=1,
    )
    db_session.add(seat)
    await db_session.commit()
    await db_session.refresh(seat)

    booking = Booking(
        seat_id=seat.id,
        user_id="user-001",
        room_id=room.id,
        date=date(2026, 5, 10),
        start_time=time(9, 0),
        end_time=time(12, 0),
        status="confirmed",
        total_price=Decimal("18.00"),
    )
    db_session.add(booking)
    await db_session.commit()

    resp = await admin_client.delete(f"{FLAT_URL}/{seat.id}")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_admin_toggle_seat_status(admin_client, sample_room_with_seat):
    _, seat = sample_room_with_seat
    resp = await admin_client.patch(f"{FLAT_URL}/{seat.id}/status/", json={"status": "maintenance"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "maintenance"


@pytest.mark.asyncio
async def test_admin_toggle_seat_status_invalid(admin_client, sample_room_with_seat):
    _, seat = sample_room_with_seat
    resp = await admin_client.patch(f"{FLAT_URL}/{seat.id}/status/", json={"status": "invalid"})
    assert resp.status_code == 422
