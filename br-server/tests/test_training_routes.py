"""API 路由测试：培训室列表、课程列表和 room_type 过滤。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher


@pytest.fixture
async def seed_training_data(db_session: AsyncSession):
    """播种培训室、教师和课程测试数据。"""
    city = City(name="茂名市", province="广东", sort_order=1, status="active")
    db_session.add(city)
    await db_session.flush()

    rooms = [
        StudyRoom(
            name="培训中心A", description="培训室A", address="地址A",
            status="open", room_type="training", min_price=50.0, city_id=city.id,
            business_hours="08:00-22:00",
        ),
        StudyRoom(
            name="综合学习中心", description="综合", address="地址C",
            status="open", room_type="comprehensive", min_price=10.0, city_id=city.id,
            business_hours="07:00-23:00",
        ),
        StudyRoom(
            name="普通自习室", description="普通", address="地址D",
            status="open", room_type="study", min_price=8.0, city_id=city.id,
        ),
        StudyRoom(
            name="已关闭培训室", description="关闭", address="地址E",
            status="closed", room_type="training", min_price=30.0, city_id=city.id,
        ),
    ]
    db_session.add_all(rooms)
    await db_session.flush()

    teachers = [
        Teacher(name="李老师", title="考研名师", rating=4.9),
        Teacher(name="王老师", title="公考专家", rating=4.8),
    ]
    db_session.add_all(teachers)
    await db_session.flush()

    courses = [
        Course(
            room_id=rooms[0].id, teacher_id=teachers[0].id,
            name="考研政治冲刺", category="postgraduate", price=80.0,
            rating=4.9, enrollment_count=300, is_hot=True, sort_order=1,
            status="active", tags="考研,政治",
        ),
        Course(
            room_id=rooms[0].id, teacher_id=teachers[1].id,
            name="公务员行测精讲", category="civil_service", price=60.0,
            rating=4.8, enrollment_count=150, is_hot=True, sort_order=2,
            status="active", tags="公考,行测",
        ),
        Course(
            room_id=rooms[0].id, teacher_id=None,
            name="小学数学辅导", category="primaryschool", price=45.0,
            rating=4.5, enrollment_count=80, is_hot=True, sort_order=3,
            status="active", tags="小学,数学",
        ),
        Course(
            room_id=rooms[1].id, teacher_id=teachers[1].id,
            name="技能提升课程", category="skills", price=55.0,
            rating=4.7, enrollment_count=100, is_hot=True, sort_order=1,
            status="active", tags="技能,提升",
        ),
        Course(
            room_id=rooms[0].id, teacher_id=teachers[0].id,
            name="非热门课程", category="postgraduate", price=30.0,
            rating=4.0, enrollment_count=10, is_hot=False, sort_order=4,
            status="active", tags="非热门",
        ),
    ]
    db_session.add_all(courses)
    await db_session.flush()

    return {"city": city, "rooms": rooms, "teachers": teachers, "courses": courses}


class TestTrainingRoomsAPI:
    """培训室列表 API 测试。"""

    async def test_returns_200(self, client, seed_training_data):
        """GET /api/v1/training/rooms 返回 200。"""
        resp = await client.get("/api/v1/training/rooms")
        assert resp.status_code == 200

    async def test_excludes_study_rooms(self, client, seed_training_data):
        """培训室列表排除 room_type=study 的房间。"""
        resp = await client.get("/api/v1/training/rooms")
        data = resp.json()
        room_types = {item["room_type"] for item in data["items"]}
        assert "study" not in room_types
        assert room_types <= {"training", "comprehensive"}

    async def test_excludes_closed_rooms(self, client, seed_training_data):
        """培训室列表排除 status=closed 的房间。"""
        resp = await client.get("/api/v1/training/rooms")
        data = resp.json()
        names = {item["name"] for item in data["items"]}
        assert "已关闭培训室" not in names

    async def test_hot_courses_max_3(self, client, seed_training_data):
        """每间培训室最多返回 3 门热门课程。"""
        resp = await client.get("/api/v1/training/rooms")
        data = resp.json()
        for item in data["items"]:
            assert len(item["hot_courses"]) <= 3

    async def test_city_filter(self, client, seed_training_data):
        """city_id 过滤只返回指定城市的培训室。"""
        city_id = seed_training_data["city"].id
        resp = await client.get(f"/api/v1/training/rooms?city_id={city_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["city_id"] == city_id for item in data["items"])

    async def test_hot_courses_present(self, client, seed_training_data):
        """培训中心A 附带 3 门热门课程。"""
        resp = await client.get("/api/v1/training/rooms")
        data = resp.json()
        room_a = next(item for item in data["items"] if item["name"] == "培训中心A")
        assert len(room_a["hot_courses"]) == 3


class TestTrainingCoursesAPI:
    """课程列表 API 测试。"""

    async def test_returns_200(self, client, seed_training_data):
        """GET /api/v1/training/courses 返回 200。"""
        resp = await client.get("/api/v1/training/courses")
        assert resp.status_code == 200

    async def test_category_filter(self, client, seed_training_data):
        """category 过滤只返回指定分类的课程。"""
        resp = await client.get("/api/v1/training/courses?category=primaryschool")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) > 0
        assert all(item["category"] == "primaryschool" for item in data["items"])

    async def test_teacher_nested(self, client, seed_training_data):
        """课程响应包含嵌套教师信息。"""
        resp = await client.get("/api/v1/training/courses")
        data = resp.json()
        course_with_teacher = next(
            item for item in data["items"] if item["teacher"] is not None
        )
        assert course_with_teacher["teacher"]["name"] in {"李老师", "王老师"}

    async def test_teacher_null(self, client, seed_training_data):
        """无教师的课程 teacher 为 null。"""
        resp = await client.get("/api/v1/training/courses?category=primaryschool")
        data = resp.json()
        course_without_teacher = next(
            item for item in data["items"] if item["name"] == "小学数学辅导"
        )
        assert course_without_teacher["teacher"] is None

    async def test_room_name_in_response(self, client, seed_training_data):
        """课程响应包含 room_name。"""
        resp = await client.get("/api/v1/training/courses")
        data = resp.json()
        assert all("room_name" in item for item in data["items"])

    async def test_tags_parsed_as_list(self, client, seed_training_data):
        """tags 被解析为列表。"""
        resp = await client.get("/api/v1/training/courses?category=postgraduate")
        data = resp.json()
        course = next(item for item in data["items"] if item["name"] == "考研政治冲刺")
        assert isinstance(course["tags"], list)
        assert "考研" in course["tags"]


class TestRoomTypeFilter:
    """自习室列表 room_type 过滤测试。"""

    async def test_filter_study(self, client, seed_training_data):
        """room_type=study 只返回普通自习室。"""
        resp = await client.get("/api/v1/rooms?room_type=study")
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["room_type"] == "study" for item in data["items"])

    async def test_filter_training(self, client, seed_training_data):
        """room_type=training 只返回培训室。"""
        resp = await client.get("/api/v1/rooms?room_type=training")
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["room_type"] == "training" for item in data["items"])

    async def test_room_type_in_response(self, client, seed_training_data):
        """自习室响应包含 room_type 字段。"""
        resp = await client.get("/api/v1/rooms")
        assert resp.status_code == 200
        data = resp.json()
        assert all("room_type" in item for item in data["items"])
