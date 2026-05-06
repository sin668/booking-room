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
async def unauth_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Client with DB overrides but NO admin auth override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: AsyncMock()
    # Do NOT override get_current_admin

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_room(db_session):
    room = StudyRoom(name="测试自习室", address="测试地址", min_price=Decimal("15.00"))
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)
    return room


BASE_URL = "/api/v1/admin/rooms"


@pytest.mark.asyncio
async def test_admin_list_rooms_empty(admin_client):
    resp = await admin_client.get(BASE_URL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_admin_create_room(admin_client):
    payload = {
        "name": "新自习室",
        "address": "新地址",
        "min_price": "20.00",
        "description": "描述",
    }
    resp = await admin_client.post(BASE_URL, json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "新自习室"
    assert data["address"] == "新地址"
    assert data["min_price"] == "20.00"
    assert data["description"] == "描述"
    assert data["status"] == "open"
    assert "id" in data


@pytest.mark.asyncio
async def test_admin_create_room_missing_fields(admin_client):
    resp = await admin_client.post(BASE_URL, json={"address": "地址"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_admin_get_room(admin_client, sample_room):
    resp = await admin_client.get(f"{BASE_URL}/{sample_room.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "测试自习室"
    assert data["seat_count"] == 0


@pytest.mark.asyncio
async def test_admin_get_room_not_found(admin_client):
    resp = await admin_client.get(f"{BASE_URL}/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_room(admin_client, sample_room):
    resp = await admin_client.put(f"{BASE_URL}/{sample_room.id}", json={"name": "更新名称"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "更新名称"


@pytest.mark.asyncio
async def test_admin_update_room_not_found(admin_client):
    resp = await admin_client.put(f"{BASE_URL}/999", json={"name": "不存在"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_delete_room(admin_client, sample_room):
    resp = await admin_client.delete(f"{BASE_URL}/{sample_room.id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_admin_delete_room_not_found(admin_client):
    resp = await admin_client.delete(f"{BASE_URL}/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_delete_room_with_active_bookings(admin_client, db_session):
    room = StudyRoom(name="有预约自习室", address="地址", min_price=Decimal("10.00"))
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

    resp = await admin_client.delete(f"{BASE_URL}/{room.id}")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_admin_toggle_room_status(admin_client, sample_room):
    resp = await admin_client.patch(
        f"{BASE_URL}/{sample_room.id}/status/", json={"status": "closed"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"


@pytest.mark.asyncio
async def test_admin_toggle_room_status_invalid(admin_client, sample_room):
    resp = await admin_client.patch(
        f"{BASE_URL}/{sample_room.id}/status/", json={"status": "invalid"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_admin_unauthorized(unauth_client):
    resp = await unauth_client.get(BASE_URL)
    assert resp.status_code == 401
