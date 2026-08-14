"""Integration tests for training room and course APIs."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher


@pytest.fixture
async def seed_training_data(db_session: AsyncSession):
    """Insert training rooms, teachers, and courses into the test database."""
    maoming = City(name="茂名市", province="广东省", sort_order=1, status="active")
    db_session.add(maoming)
    await db_session.flush()

    t1 = Teacher(name="李明华", title="考研政治名师", rating=4.9)
    t2 = Teacher(name="王晓雯", title="公考行测专家", rating=4.8)
    t3 = Teacher(name="陈雅琪", title="雅思口语讲师", rating=5.0)
    db_session.add_all([t1, t2, t3])
    await db_session.flush()

    r1 = StudyRoom(name="去K书培训中心", address="茂名市光谷大道88号", status="open", min_price=50.00, room_type="training", city_id=maoming.id)
    r2 = StudyRoom(name="去K书·星火教室", address="茂名市文明中路56号", status="open", min_price=40.00, room_type="training")
    r3 = StudyRoom(name="去K书·综合学习中心", address="茂名市光华南路200号", status="open", min_price=10.00, room_type="comprehensive")
    r4 = StudyRoom(name="安静自习室", address="茂名市油城三路", status="open", min_price=8.00, room_type="study")
    r5 = StudyRoom(name="关闭的培训室", address="某地址", status="closed", min_price=30.00, room_type="training")
    db_session.add_all([r1, r2, r3, r4, r5])
    await db_session.flush()

    courses = [
        Course(room_id=r1.id, teacher_id=t1.id, name="考研政治冲刺班", category="postgraduate", price=80.00, rating=4.9, enrollment_count=328, tags="考研,政治", status="active", is_hot=True, sort_order=1),
        Course(room_id=r1.id, teacher_id=t2.id, name="公务员行测精讲", category="civil_service", price=60.00, rating=4.8, enrollment_count=156, tags="公考,行测", status="active", is_hot=True, sort_order=2),
        Course(room_id=r1.id, teacher_id=t3.id, name="雅思口语1v1冲刺", category="language", price=120.00, rating=5.0, enrollment_count=89, tags="雅思,口语", status="active", is_hot=True, sort_order=3),
        Course(room_id=r1.id, teacher_id=t3.id, name="雅思口语进阶班", category="language", price=100.00, rating=4.8, enrollment_count=50, tags="雅思,口语", status="active", is_hot=True, sort_order=4),
        Course(room_id=r2.id, teacher_id=None, name="小学数学同步辅导", category="primaryschool", price=45.00, rating=4.6, enrollment_count=78, tags="小学,数学", status="active", is_hot=True, sort_order=1),
        Course(room_id=r3.id, teacher_id=t1.id, name="考研政治冲刺班", category="postgraduate", price=80.00, rating=4.9, enrollment_count=200, tags=None, status="active", is_hot=False, sort_order=1),
        Course(room_id=r3.id, teacher_id=None, name="初中物理提升班", category="middleschool", price=55.00, rating=4.7, enrollment_count=95, tags="", status="active", is_hot=False, sort_order=2),
    ]
    db_session.add_all(courses)
    await db_session.flush()


class TestTrainingRoomsAPI:
    async def test_list_training_rooms_default(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    async def test_list_training_rooms_filter_city(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms?city_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "去K书培训中心"

    async def test_comprehensive_room_appears(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        names = [item["name"] for item in resp.json()["items"]]
        assert "去K书·综合学习中心" in names

    async def test_study_room_excluded(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        names = [item["name"] for item in resp.json()["items"]]
        assert "安静自习室" not in names
        assert "关闭的培训室" not in names

    async def test_hot_courses_limit_3(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        data = resp.json()
        room1 = [r for r in data["items"] if r["name"] == "去K书培训中心"][0]
        assert len(room1["hot_courses"]) == 3

    async def test_hot_courses_include_teacher(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        data = resp.json()
        room1 = [r for r in data["items"] if r["name"] == "去K书培训中心"][0]
        hot = room1["hot_courses"][0]
        assert hot["teacher"] is not None
        assert hot["teacher"]["name"] == "李明华"

    async def test_training_room_hot_courses(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        data = resp.json()
        room2 = [r for r in data["items"] if r["name"] == "去K书·星火教室"][0]
        assert len(room2["hot_courses"]) >= 1


class TestCoursesAPI:
    async def test_list_courses_default(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 7
        assert len(data["items"]) == 7

    async def test_list_courses_filter_category(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses?category=postgraduate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["category"] == "postgraduate"

    async def test_course_teacher_nested(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses?category=postgraduate")
        data = resp.json()
        course = [c for c in data["items"] if c["name"] == "考研政治冲刺班"][0]
        assert course["teacher"] is not None
        assert course["teacher"]["name"] == "李明华"

    async def test_course_without_teacher(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses?category=primaryschool")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["teacher"] is None

    async def test_course_tags_parsing(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses?category=postgraduate")
        data = resp.json()
        course = [c for c in data["items"] if c["room_name"] == "去K书培训中心"][0]
        assert course["tags"] == ["考研", "政治"]

    async def test_course_empty_tags(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses?category=middleschool")
        data = resp.json()
        assert data["items"][0]["tags"] == []
