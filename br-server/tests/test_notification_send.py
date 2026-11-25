"""Tests for the shared notification sender and the arrival reminder API."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.models.notification import Notification, NotificationPreference
from app.models.study_room import StudyRoom
from app.models.user import User
from app.schemas.notification import NotificationCreate
from app.services.notification_service import NotificationService

USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
ROOM_LATITUDE = 30.5000000
ROOM_LONGITUDE = 114.3000000


@pytest.fixture
async def auth_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def seed_user_and_room(db_session: AsyncSession) -> StudyRoom:
    db_session.add(
        User(
            id=USER_ID,
            phone="13800138021",
            nickname="到店用户",
            password_hash="hashed",
            username="arrival_user_1",
        )
    )
    room = StudyRoom(
        name="光谷自习室",
        address="光谷大道88号",
        latitude=ROOM_LATITUDE,
        longitude=ROOM_LONGITUDE,
        status="open",
        room_type="study",
        min_price=0,
        rating=0,
    )
    db_session.add(room)
    await db_session.flush()
    return room


@pytest.mark.asyncio
async def test_send_notification_fills_default_target(
    db_session: AsyncSession,
    seed_user_and_room: StudyRoom,
) -> None:
    service = NotificationService(db_session)

    result = await service.send_notification(
        NotificationCreate(
            user_id=USER_ID,
            type="activity",
            title="活动通知",
            content="新活动上线",
        )
    )

    assert result is not None
    assert result["target_url"] == "/pages/index/index"


@pytest.mark.asyncio
async def test_send_notification_skips_disabled_preference(
    db_session: AsyncSession,
    seed_user_and_room: StudyRoom,
) -> None:
    db_session.add(NotificationPreference(user_id=USER_ID, arrival_enabled=False))
    await db_session.flush()
    service = NotificationService(db_session)

    result = await service.send_notification(
        NotificationCreate(
            user_id=USER_ID,
            type="arrival",
            title="到店签到提醒",
            content="已到达",
        )
    )

    assert result is None
    stored = await db_session.execute(select(Notification))
    assert stored.scalars().all() == []


@pytest.mark.asyncio
async def test_arrival_reminder_sends_when_within_500_meters(
    auth_client: AsyncClient,
    seed_user_and_room: StudyRoom,
) -> None:
    response = await auth_client.post(
        "/api/v1/notifications/arrival-reminder",
        json={
            "room_id": seed_user_and_room.id,
            "latitude": ROOM_LATITUDE + 0.001,
            "longitude": ROOM_LONGITUDE,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sent"] is True
    assert data["distance"] is not None and data["distance"] <= 500
    assert data["notification"]["title"] == "到店签到提醒"
    assert data["notification"]["target_url"] == "/pages-sub/qrcode/index"
    assert data["notification"]["target_type"] == "room"
    assert data["notification"]["target_id"] == str(seed_user_and_room.id)


@pytest.mark.asyncio
async def test_arrival_reminder_skips_when_too_far(
    auth_client: AsyncClient,
    seed_user_and_room: StudyRoom,
) -> None:
    response = await auth_client.post(
        "/api/v1/notifications/arrival-reminder",
        json={
            "room_id": seed_user_and_room.id,
            "latitude": ROOM_LATITUDE + 0.01,
            "longitude": ROOM_LONGITUDE,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["sent"] is False
    assert data["reason"] == "too_far"


@pytest.mark.asyncio
async def test_arrival_reminder_skips_room_without_coordinates(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_user_and_room: StudyRoom,
) -> None:
    room = StudyRoom(
        name="无坐标自习室",
        address="未知地址",
        latitude=None,
        longitude=None,
        status="open",
        room_type="study",
        min_price=0,
        rating=0,
    )
    db_session.add(room)
    await db_session.flush()

    response = await auth_client.post(
        "/api/v1/notifications/arrival-reminder",
        json={
            "room_id": room.id,
            "latitude": ROOM_LATITUDE,
            "longitude": ROOM_LONGITUDE,
        },
    )

    assert response.status_code == 200
    assert response.json()["reason"] == "room_without_coordinates"


@pytest.mark.asyncio
async def test_arrival_reminder_respects_disabled_preference(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_user_and_room: StudyRoom,
) -> None:
    db_session.add(NotificationPreference(user_id=USER_ID, arrival_enabled=False))
    await db_session.flush()

    response = await auth_client.post(
        "/api/v1/notifications/arrival-reminder",
        json={
            "room_id": seed_user_and_room.id,
            "latitude": ROOM_LATITUDE,
            "longitude": ROOM_LONGITUDE,
        },
    )

    assert response.status_code == 200
    assert response.json()["reason"] == "disabled"


@pytest.mark.asyncio
async def test_arrival_reminder_deduplicates_within_24_hours(
    auth_client: AsyncClient,
    seed_user_and_room: StudyRoom,
) -> None:
    payload = {
        "room_id": seed_user_and_room.id,
        "latitude": ROOM_LATITUDE,
        "longitude": ROOM_LONGITUDE,
    }

    first = await auth_client.post(
        "/api/v1/notifications/arrival-reminder", json=payload
    )
    second = await auth_client.post(
        "/api/v1/notifications/arrival-reminder", json=payload
    )

    assert first.json()["sent"] is True
    assert second.json()["sent"] is False
    assert second.json()["reason"] == "already_sent"


@pytest.mark.asyncio
async def test_arrival_reminder_returns_404_for_unknown_room(
    auth_client: AsyncClient,
    seed_user_and_room: StudyRoom,
) -> None:
    response = await auth_client.post(
        "/api/v1/notifications/arrival-reminder",
        json={
            "room_id": 999999,
            "latitude": ROOM_LATITUDE,
            "longitude": ROOM_LONGITUDE,
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_arrival_reminder_requires_authentication(
    client: AsyncClient,
    seed_user_and_room: StudyRoom,
) -> None:
    response = await client.post(
        "/api/v1/notifications/arrival-reminder",
        json={
            "room_id": seed_user_and_room.id,
            "latitude": ROOM_LATITUDE,
            "longitude": ROOM_LONGITUDE,
        },
    )

    assert response.status_code == 401
