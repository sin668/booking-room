"""API tests for current-user followed study rooms."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.models.room_follow import RoomFollow
from app.models.study_room import StudyRoom
from app.models.user import User


USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
async def auth_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def seed_room_follow_data(db_session: AsyncSession) -> dict[str, StudyRoom]:
    db_session.add(
        User(
            id=USER_ID,
            phone="13800138013",
            nickname="关注用户",
            password_hash="hashed",
            username="room_follow_user",
        )
    )
    rooms = {
        "open": StudyRoom(
            name="南门自习室",
            address="南门街 1 号",
            status="open",
            min_price=12,
            cover_image="https://example.com/room.jpg",
        ),
        "closed": StudyRoom(
            name="暂停营业自习室",
            address="北门街 2 号",
            status="closed",
            min_price=10,
        ),
    }
    db_session.add_all(rooms.values())
    await db_session.flush()
    return rooms


@pytest.mark.asyncio
async def test_follow_room_persists_current_user_follow(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_room_follow_data: dict[str, StudyRoom],
) -> None:
    room = seed_room_follow_data["open"]

    response = await auth_client.post(f"/api/v1/room-follows/{room.id}")

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == room.id
    assert data["name"] == "南门自习室"
    assert data["followed_at"] is not None

    follow = (
        await db_session.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == USER_ID,
                RoomFollow.room_id == room.id,
            )
        )
    ).scalar_one()
    assert follow.room_id == room.id


@pytest.mark.asyncio
async def test_follow_room_is_idempotent(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_room_follow_data: dict[str, StudyRoom],
) -> None:
    room = seed_room_follow_data["open"]

    first = await auth_client.post(f"/api/v1/room-follows/{room.id}")
    second = await auth_client.post(f"/api/v1/room-follows/{room.id}")

    assert first.status_code == 201
    assert second.status_code == 200
    count = (
        await db_session.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == USER_ID,
                RoomFollow.room_id == room.id,
            )
        )
    ).scalars().all()
    assert len(count) == 1


@pytest.mark.asyncio
async def test_list_followed_rooms_returns_room_details(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_room_follow_data: dict[str, StudyRoom],
) -> None:
    room = seed_room_follow_data["open"]
    db_session.add(RoomFollow(user_id=USER_ID, room_id=room.id))
    await db_session.flush()

    response = await auth_client.get("/api/v1/room-follows")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == room.id
    assert data["items"][0]["address"] == "南门街 1 号"


@pytest.mark.asyncio
async def test_unfollow_room_deletes_current_user_follow(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_room_follow_data: dict[str, StudyRoom],
) -> None:
    room = seed_room_follow_data["open"]
    db_session.add(RoomFollow(user_id=USER_ID, room_id=room.id))
    await db_session.flush()

    response = await auth_client.delete(f"/api/v1/room-follows/{room.id}")

    assert response.status_code == 204
    remaining = (
        await db_session.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == USER_ID,
                RoomFollow.room_id == room.id,
            )
        )
    ).scalars().all()
    assert remaining == []


@pytest.mark.asyncio
async def test_follow_missing_or_closed_room_is_rejected(
    auth_client: AsyncClient,
    seed_room_follow_data: dict[str, StudyRoom],
) -> None:
    closed_room = seed_room_follow_data["closed"]

    closed_response = await auth_client.post(f"/api/v1/room-follows/{closed_room.id}")
    missing_response = await auth_client.post("/api/v1/room-follows/999999")

    assert closed_response.status_code == 404
    assert missing_response.status_code == 404
