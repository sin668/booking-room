"""API 路由测试：培训室详情 GET /api/v1/training/rooms/{room_id}。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher


@pytest.fixture
async def seed_detail_data(db_session: AsyncSession):
    """播种培训室详情测试数据。"""
    city = City(name="茂名市", province="广东", sort_order=1, status="active")
    db_session.add(city)
    await db_session.flush()

    room = StudyRoom(
        name="培训中心A",
        description="优质培训中心",
        address="茂名市XX路1号",
        status="open",
        room_type="training",
        min_price=50.0,
        city_id=city.id,
        business_hours="08:00-22:00",
        rating=4.5,
    )
    db_session.add(room)
    await db_session.flush()

    teacher = Teacher(name="李老师", title="考研名师", rating=4.9)
    db_session.add(teacher)
    await db_session.flush()

    course = Course(
        room_id=room.id,
        teacher_id=teacher.id,
        name="考研政治冲刺",
        category="postgraduate",
        price=80.0,
        rating=4.9,
        enrollment_count=300,
        is_hot=True,
        sort_order=1,
        status="active",
        tags="考研,政治",
    )
    db_session.add(course)
    await db_session.flush()

    return {"city": city, "room": room, "teacher": teacher, "course": course}


class TestTrainingRoomDetailAPI:
    """培训室详情 API 测试。"""

    async def test_404_for_non_existent_room(self, client, seed_detail_data):
        """GET /api/v1/training/rooms/{non_existent_id} 返回 404。"""
        resp = await client.get("/api/v1/training/rooms/999999")
        assert resp.status_code == 404
        data = resp.json()
        assert "培训室" in data["detail"]

    async def test_200_for_valid_room(self, client, seed_detail_data):
        """GET /api/v1/training/rooms/{valid_id} 返回 200 及正确数据。"""
        room_id = seed_detail_data["room"].id
        resp = await client.get(f"/api/v1/training/rooms/{room_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == room_id
        assert data["name"] == "培训中心A"
        assert data["room_type"] == "training"
        assert data["classroom_count"] == 1
        assert data["teacher_count"] == 1
        assert len(data["courses"]) == 1
        assert data["courses"][0]["name"] == "考研政治冲刺"
