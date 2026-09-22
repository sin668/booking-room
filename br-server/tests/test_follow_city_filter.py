"""关注列表 city_id 过滤测试（followed-rooms-city-filter）。

覆盖 room/course/teacher 三种 follow_type 的城市过滤、
无城市归属豁免、教师无房间关联豁免、不传 city_id 行为不变。
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.models.city import City
from app.models.course import Course
from app.models.room_follow import RoomFollow
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.models.teacher_room import TeacherRoom
from app.models.user import User


USER_ID = uuid.UUID("77777777-7777-7777-7777-777777777777")


@pytest.fixture
async def auth_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def seed_city_follow_data(db_session: AsyncSession) -> dict:
    """两个城市 + 三间房间（A/B/无城市）+ 课程/教师关注数据。"""
    db_session.add(
        User(
            id=USER_ID,
            phone="13800138077",
            nickname="城市关注用户",
            password_hash="hashed",
            username="follow_city_user",
        )
    )
    city_a = City(name="甲市", province="测试省", sort_order=1)
    city_b = City(name="乙市", province="测试省", sort_order=2)
    db_session.add_all([city_a, city_b])
    await db_session.flush()

    room_a = StudyRoom(
        name="甲市房间", address="甲街 1 号", status="open",
        min_price=10, city_id=city_a.id,
    )
    room_b = StudyRoom(
        name="乙市房间", address="乙街 2 号", status="open",
        min_price=20, city_id=city_b.id, room_type="training",
    )
    room_null = StudyRoom(
        name="无城市房间", address="无街 3 号", status="open", min_price=30,
    )
    db_session.add_all([room_a, room_b, room_null])
    await db_session.flush()

    course_a = Course(
        name="甲市课程", room_id=room_a.id, category="postgraduate", status="active",
    )
    course_b = Course(
        name="乙市课程", room_id=room_b.id, category="postgraduate", status="active",
    )
    teacher_a = Teacher(name="老师甲", title="数学", rating=4.8)
    teacher_b = Teacher(name="老师乙", title="英语", rating=4.7)
    teacher_orphan = Teacher(name="无房间老师", title="政治", rating=4.6)
    db_session.add_all([course_a, course_b, teacher_a, teacher_b, teacher_orphan])
    await db_session.flush()

    db_session.add_all([
        TeacherRoom(teacher_id=teacher_a.id, room_id=room_a.id),
        TeacherRoom(teacher_id=teacher_b.id, room_id=room_b.id),
        RoomFollow(user_id=USER_ID, room_id=room_a.id, follow_type="room"),
        RoomFollow(user_id=USER_ID, room_id=room_b.id, follow_type="room"),
        RoomFollow(user_id=USER_ID, room_id=room_null.id, follow_type="room"),
        RoomFollow(user_id=USER_ID, room_id=course_a.id, follow_type="course"),
        RoomFollow(user_id=USER_ID, room_id=course_b.id, follow_type="course"),
        RoomFollow(user_id=USER_ID, room_id=teacher_a.id, follow_type="teacher"),
        RoomFollow(user_id=USER_ID, room_id=teacher_b.id, follow_type="teacher"),
        RoomFollow(user_id=USER_ID, room_id=teacher_orphan.id, follow_type="teacher"),
    ])
    await db_session.flush()

    return {
        "city_a": city_a,
        "city_b": city_b,
        "room_a": room_a,
        "room_b": room_b,
        "room_null": room_null,
        "course_a": course_a,
        "course_b": course_b,
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "teacher_orphan": teacher_orphan,
    }


def _names(payload: dict) -> set[str]:
    return {item["name"] for item in payload["items"]}


@pytest.mark.asyncio
async def test_room_follows_filtered_by_city(
    auth_client: AsyncClient, seed_city_follow_data: dict
) -> None:
    resp = await auth_client.get(
        f"/api/v1/room-follows?city_id={seed_city_follow_data['city_a'].id}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert _names(data) == {"甲市房间", "无城市房间"}
    assert data["total"] == len(data["items"])


@pytest.mark.asyncio
async def test_room_follows_without_city_id_returns_all(
    auth_client: AsyncClient, seed_city_follow_data: dict
) -> None:
    resp = await auth_client.get("/api/v1/room-follows")
    assert resp.status_code == 200
    assert _names(resp.json()) == {"甲市房间", "乙市房间", "无城市房间"}


@pytest.mark.asyncio
async def test_course_follows_filtered_by_room_city(
    auth_client: AsyncClient, seed_city_follow_data: dict
) -> None:
    resp = await auth_client.get(
        "/api/v1/room-follows?follow_type=course"
        f"&city_id={seed_city_follow_data['city_b'].id}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert _names(data) == {"乙市课程"}
    assert data["total"] == 1


@pytest.mark.asyncio
async def test_teacher_follows_filtered_by_city(
    auth_client: AsyncClient, seed_city_follow_data: dict
) -> None:
    resp = await auth_client.get(
        "/api/v1/room-follows?follow_type=teacher"
        f"&city_id={seed_city_follow_data['city_a'].id}"
    )
    assert resp.status_code == 200
    data = resp.json()
    # 老师甲归属甲市可见；老师乙归属乙市被过滤；无房间关联教师始终可见
    assert _names(data) == {"老师甲", "无房间老师"}
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_teacher_follows_without_city_id_returns_all(
    auth_client: AsyncClient, seed_city_follow_data: dict
) -> None:
    resp = await auth_client.get("/api/v1/room-follows?follow_type=teacher")
    assert resp.status_code == 200
    assert _names(resp.json()) == {"老师甲", "老师乙", "无房间老师"}


@pytest.mark.asyncio
async def test_invalid_city_id_rejected(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/room-follows?city_id=0")
    assert resp.status_code == 422
