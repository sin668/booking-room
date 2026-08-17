"""Tests for room_follow_service follow_type extension (TDD – Red phase)."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.room_follow import RoomFollow
from app.models.study_room import StudyRoom
from app.models.user import User
from app.services import room_follow_service

USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
async def seed_user(db_session: AsyncSession) -> User:
    user = User(
        id=USER_ID,
        phone="13900139022",
        nickname="关注测试用户",
        password_hash="hashed",
        username="follow_type_user",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def seed_room(db_session: AsyncSession) -> StudyRoom:
    room = StudyRoom(
        name="测试自习室",
        address="测试街 1 号",
        status="open",
        min_price=10,
    )
    db_session.add(room)
    await db_session.flush()
    return room


@pytest.fixture
async def seed_course(db_session: AsyncSession, seed_room: StudyRoom) -> Course:
    course = Course(
        name="测试课程",
        room_id=seed_room.id,
        category="math",
        price=99.0,
        status="active",
    )
    db_session.add(course)
    await db_session.flush()
    return course


# ── list_followed_rooms ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_followed_rooms_default_type_returns_only_room_follows(
    db_session: AsyncSession,
    seed_user: User,
    seed_room: StudyRoom,
    seed_course: Course,
) -> None:
    """Default follow_type='room' should only return room follows."""
    # Create a room follow and a course follow
    db_session.add(RoomFollow(user_id=USER_ID, room_id=seed_room.id, follow_type="room"))
    db_session.add(RoomFollow(user_id=USER_ID, room_id=seed_course.id, follow_type="course"))
    await db_session.flush()

    result = await room_follow_service.list_followed_rooms(db_session, USER_ID)
    assert result.total == 1
    assert result.items[0].id == seed_room.id


@pytest.mark.asyncio
async def test_list_followed_rooms_course_type_returns_empty_for_now(
    db_session: AsyncSession,
    seed_user: User,
    seed_room: StudyRoom,
    seed_course: Course,
) -> None:
    """follow_type='course' should return empty list (current phase)."""
    db_session.add(RoomFollow(user_id=USER_ID, room_id=seed_room.id, follow_type="room"))
    await db_session.flush()

    result = await room_follow_service.list_followed_rooms(
        db_session, USER_ID, follow_type="course"
    )
    assert result.total == 0
    assert result.items == []


# ── follow_room ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_follow_room_with_type_course_validates_course(
    db_session: AsyncSession,
    seed_user: User,
    seed_course: Course,
) -> None:
    """follow_type='course' should validate against courses table."""
    room, created = await room_follow_service.follow_room(
        db_session, USER_ID, seed_course.id, follow_type="course"
    )
    assert created is True
    assert room.id == seed_course.id


@pytest.mark.asyncio
async def test_follow_room_with_type_course_missing_raises(
    db_session: AsyncSession,
    seed_user: User,
) -> None:
    """follow_type='course' with non-existent course should raise ValueError."""
    with pytest.raises(ValueError):
        await room_follow_service.follow_room(
            db_session, USER_ID, 999999, follow_type="course"
        )


@pytest.mark.asyncio
async def test_follow_room_same_target_different_types(
    db_session: AsyncSession,
    seed_user: User,
    seed_room: StudyRoom,
) -> None:
    """Same room_id can be followed as both 'room' and 'course' types."""
    # Follow as room type
    _, created1 = await room_follow_service.follow_room(
        db_session, USER_ID, seed_room.id, follow_type="room"
    )
    assert created1 is True

    # Follow same id as course type — should create a separate follow
    # But first we need a course with that id; since seed_room.id may not match a course,
    # this test verifies the follow_type is stored correctly
    # We'll use a direct DB approach for the course follow
    db_session.add(RoomFollow(user_id=USER_ID, room_id=seed_room.id, follow_type="course"))
    await db_session.flush()

    # Now list with room type — should only return 1
    result = await room_follow_service.list_followed_rooms(db_session, USER_ID, follow_type="room")
    assert result.total == 1


# ── unfollow_room ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unfollow_room_with_type_only_deletes_matching_type(
    db_session: AsyncSession,
    seed_user: User,
    seed_room: StudyRoom,
) -> None:
    """unfollow with follow_type='room' should not delete course follows."""
    db_session.add(RoomFollow(user_id=USER_ID, room_id=seed_room.id, follow_type="room"))
    db_session.add(RoomFollow(user_id=USER_ID, room_id=seed_room.id, follow_type="course"))
    await db_session.flush()

    await room_follow_service.unfollow_room(db_session, USER_ID, seed_room.id, follow_type="room")

    # Room follow should be gone
    from sqlalchemy import select
    remaining = (
        await db_session.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == USER_ID,
                RoomFollow.room_id == seed_room.id,
            )
        )
    ).scalars().all()
    assert len(remaining) == 1
    assert remaining[0].follow_type == "course"
