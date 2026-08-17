"""教师关注 API 测试。

覆盖：关注、取消关注、幂等、类型隔离、不存在教师。
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.models.room_follow import RoomFollow
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.models.user import User


USER_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
async def auth_client(client: AsyncClient):
    """Create a client with mocked auth returning USER_ID."""
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def seed_teacher_follow_data(db_session: AsyncSession) -> dict:
    """Seed user, teacher, and room for teacher follow tests."""
    db_session.add(
        User(
            id=USER_ID,
            phone="13800138055",
            nickname="教师关注用户",
            password_hash="hashed",
            username="teacher_follow_user",
        )
    )
    await db_session.flush()

    teacher = Teacher(
        name="李明华",
        title="考研政治",
        rating=4.9,
        bio="专注考研政治辅导8年。",
        student_count=328,
    )
    db_session.add(teacher)
    await db_session.flush()

    room = StudyRoom(
        name="关注测试教室",
        address="关注街 1 号",
        status="open",
        min_price=10,
    )
    db_session.add(room)
    await db_session.flush()

    return {"teacher": teacher, "room": room}


# ---------------------------------------------------------------------------
# 关注教师
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_follow_teacher_returns_201(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_teacher_follow_data: dict,
) -> None:
    teacher = seed_teacher_follow_data["teacher"]

    response = await auth_client.post(f"/api/v1/room-follows/{teacher.id}?follow_type=teacher")

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == teacher.id
    assert data["name"] == "李明华"

    # Verify DB record
    follow = (
        await db_session.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == USER_ID,
                RoomFollow.room_id == teacher.id,
                RoomFollow.follow_type == "teacher",
            )
        )
    ).scalar_one()
    assert follow.follow_type == "teacher"


# ---------------------------------------------------------------------------
# 重复关注（幂等）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_follow_teacher_duplicate_returns_200(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_teacher_follow_data: dict,
) -> None:
    teacher = seed_teacher_follow_data["teacher"]

    first = await auth_client.post(f"/api/v1/room-follows/{teacher.id}?follow_type=teacher")
    second = await auth_client.post(f"/api/v1/room-follows/{teacher.id}?follow_type=teacher")

    assert first.status_code == 201
    assert second.status_code == 200

    follows = (
        await db_session.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == USER_ID,
                RoomFollow.room_id == teacher.id,
                RoomFollow.follow_type == "teacher",
            )
        )
    ).scalars().all()
    assert len(follows) == 1


# ---------------------------------------------------------------------------
# 取消关注
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unfollow_teacher_returns_204(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_teacher_follow_data: dict,
) -> None:
    teacher = seed_teacher_follow_data["teacher"]
    db_session.add(RoomFollow(user_id=USER_ID, room_id=teacher.id, follow_type="teacher"))
    await db_session.flush()

    response = await auth_client.delete(f"/api/v1/room-follows/{teacher.id}?follow_type=teacher")

    assert response.status_code == 204

    remaining = (
        await db_session.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == USER_ID,
                RoomFollow.room_id == teacher.id,
                RoomFollow.follow_type == "teacher",
            )
        )
    ).scalars().all()
    assert remaining == []


# ---------------------------------------------------------------------------
# 类型隔离
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teacher_follow_type_isolated_from_room(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_teacher_follow_data: dict,
) -> None:
    teacher = seed_teacher_follow_data["teacher"]
    room = seed_teacher_follow_data["room"]

    db_session.add(RoomFollow(user_id=USER_ID, room_id=room.id, follow_type="room"))
    db_session.add(RoomFollow(user_id=USER_ID, room_id=teacher.id, follow_type="teacher"))
    await db_session.flush()

    room_resp = await auth_client.get("/api/v1/room-follows?follow_type=room")
    assert room_resp.status_code == 200
    assert room_resp.json()["total"] == 1

    teacher_resp = await auth_client.get("/api/v1/room-follows?follow_type=teacher")
    assert teacher_resp.status_code == 200
    assert teacher_resp.json()["total"] == 1


# ---------------------------------------------------------------------------
# 不存在的教师
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_follow_nonexistent_teacher_returns_404(
    auth_client: AsyncClient,
    seed_teacher_follow_data: dict,
) -> None:
    response = await auth_client.post("/api/v1/room-follows/99999?follow_type=teacher")
    assert response.status_code == 404
