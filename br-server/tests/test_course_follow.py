"""TDD tests for course follow API (Task 6.2).

Covers follow/unfollow/list for follow_type=course via /api/v1/room-follows.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.models.course import Course
from app.models.room_follow import RoomFollow
from app.models.study_room import StudyRoom
from app.models.user import User


USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")


@pytest.fixture
async def auth_client(client: AsyncClient):
    """Create a client with mocked auth returning USER_ID."""
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def seed_course_follow_data(db_session: AsyncSession) -> dict:
    """Seed user, room, and course for course follow tests."""
    db_session.add(
        User(
            id=USER_ID,
            phone="13800138033",
            nickname="课程关注用户",
            password_hash="hashed",
            username="course_follow_user",
        )
    )
    await db_session.flush()

    room = StudyRoom(
        name="课程关注测试教室",
        address="课程街 1 号",
        status="open",
        min_price=10,
    )
    db_session.add(room)
    await db_session.flush()

    course = Course(
        name="考研数学强化",
        room_id=room.id,
        category="postgraduate",
        price=99.0,
        rating=4.8,
        enrollment_count=200,
        status="active",
    )
    db_session.add(course)
    await db_session.flush()

    return {"room": room, "course": course}


# ---------------------------------------------------------------------------
# 关注课程
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_follow_course_returns_201(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_course_follow_data: dict,
) -> None:
    """关注课程（follow_type=course）返回 201。"""
    course = seed_course_follow_data["course"]

    response = await auth_client.post(f"/api/v1/room-follows/{course.id}?follow_type=course")

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == course.id

    # Verify DB record
    follow = (
        await db_session.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == USER_ID,
                RoomFollow.room_id == course.id,
                RoomFollow.follow_type == "course",
            )
        )
    ).scalar_one()
    assert follow.follow_type == "course"


# ---------------------------------------------------------------------------
# 重复关注同一课程（幂等）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_follow_course_duplicate_returns_200(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_course_follow_data: dict,
) -> None:
    """重复关注同一课程返回 200，幂等。"""
    course = seed_course_follow_data["course"]

    first = await auth_client.post(f"/api/v1/room-follows/{course.id}?follow_type=course")
    second = await auth_client.post(f"/api/v1/room-follows/{course.id}?follow_type=course")

    assert first.status_code == 201
    assert second.status_code == 200

    # Only one record in DB
    follows = (
        await db_session.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == USER_ID,
                RoomFollow.room_id == course.id,
                RoomFollow.follow_type == "course",
            )
        )
    ).scalars().all()
    assert len(follows) == 1


# ---------------------------------------------------------------------------
# 取消关注课程
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unfollow_course_returns_204(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_course_follow_data: dict,
) -> None:
    """取消关注课程返回 204。"""
    course = seed_course_follow_data["course"]
    db_session.add(RoomFollow(user_id=USER_ID, room_id=course.id, follow_type="course"))
    await db_session.flush()

    response = await auth_client.delete(f"/api/v1/room-follows/{course.id}?follow_type=course")

    assert response.status_code == 204

    # Verify DB record deleted
    remaining = (
        await db_session.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == USER_ID,
                RoomFollow.room_id == course.id,
                RoomFollow.follow_type == "course",
            )
        )
    ).scalars().all()
    assert remaining == []


# ---------------------------------------------------------------------------
# 列表过滤 follow_type=course
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_follow_type_course_returns_only_course_follows(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_course_follow_data: dict,
) -> None:
    """列表过滤 follow_type=course 只返回课程关注。"""
    room = seed_course_follow_data["room"]
    course = seed_course_follow_data["course"]

    # Create both room and course follows
    db_session.add(RoomFollow(user_id=USER_ID, room_id=room.id, follow_type="room"))
    db_session.add(RoomFollow(user_id=USER_ID, room_id=course.id, follow_type="course"))
    await db_session.flush()

    response = await auth_client.get("/api/v1/room-follows?follow_type=course")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == course.id


# ---------------------------------------------------------------------------
# 同一 target 不同 follow_type → 两条记录并存
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_same_target_different_follow_type_coexist(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_course_follow_data: dict,
) -> None:
    """同一 target 以不同 follow_type 关注，产生两条独立记录。"""
    room = seed_course_follow_data["room"]

    # Follow same room as both 'room' and 'course' types
    db_session.add(RoomFollow(user_id=USER_ID, room_id=room.id, follow_type="room"))
    db_session.add(RoomFollow(user_id=USER_ID, room_id=room.id, follow_type="course"))
    await db_session.flush()

    # List room type → 1
    room_resp = await auth_client.get("/api/v1/room-follows?follow_type=room")
    assert room_resp.status_code == 200
    assert room_resp.json()["total"] == 1

    # List course type → 1
    course_resp = await auth_client.get("/api/v1/room-follows?follow_type=course")
    assert course_resp.status_code == 200
    assert course_resp.json()["total"] == 1

    # DB has 2 records
    all_follows = (
        await db_session.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == USER_ID,
                RoomFollow.room_id == room.id,
            )
        )
    ).scalars().all()
    assert len(all_follows) == 2


# ---------------------------------------------------------------------------
# 不传 follow_type → 默认 room，行为不变
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_default_follow_type_is_room(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_course_follow_data: dict,
) -> None:
    """不传 follow_type 默认为 room，行为不变。"""
    room = seed_course_follow_data["room"]
    course = seed_course_follow_data["course"]

    db_session.add(RoomFollow(user_id=USER_ID, room_id=room.id, follow_type="room"))
    db_session.add(RoomFollow(user_id=USER_ID, room_id=course.id, follow_type="course"))
    await db_session.flush()

    # GET without follow_type → defaults to room
    response = await auth_client.get("/api/v1/room-follows")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == room.id


# ---------------------------------------------------------------------------
# 非法 follow_type 值 → 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_follow_type_returns_422(
    auth_client: AsyncClient,
) -> None:
    """非法 follow_type 值返回 422。"""
    response = await auth_client.get("/api/v1/room-follows?follow_type=invalid")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_invalid_follow_type_returns_422(
    auth_client: AsyncClient,
    seed_course_follow_data: dict,
) -> None:
    """POST with invalid follow_type returns 422."""
    course = seed_course_follow_data["course"]
    response = await auth_client.post(f"/api/v1/room-follows/{course.id}?follow_type=invalid")

    assert response.status_code == 422
