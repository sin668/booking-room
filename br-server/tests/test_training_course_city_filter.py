"""培训课程列表 city_id 过滤测试。

口径与培训室列表一致：所属培训室 city_id 等于指定值或未设置城市的课程可见；
count 查询在 city_id 过滤下不得因 StudyRoom 隐式笛卡尔积放大 total。
"""

from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.course_schedule import CourseSchedule
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher


@pytest.fixture
async def seed_city_filter_data(db_session: AsyncSession):
    """播种两座城市 + 无城市培训室，各挂一门可见课程。"""
    city_a = City(name="甲市", province="测试", sort_order=1, status="active")
    city_b = City(name="乙市", province="测试", sort_order=2, status="active")
    db_session.add_all([city_a, city_b])
    await db_session.flush()

    rooms = [
        StudyRoom(
            name="甲市培训室", address="A", status="open", room_type="training",
            min_price=10.0, city_id=city_a.id,
        ),
        StudyRoom(
            name="乙市培训室", address="B", status="open", room_type="training",
            min_price=10.0, city_id=city_b.id,
        ),
        StudyRoom(
            name="无城市培训室", address="C", status="open", room_type="training",
            min_price=10.0, city_id=None,
        ),
    ]
    db_session.add_all(rooms)
    await db_session.flush()

    teacher = Teacher(name="陈老师", title="讲师", rating=4.7)
    db_session.add(teacher)
    await db_session.flush()

    courses = [
        Course(name=f"{room.name}课程", room_id=room.id, category="skills",
               status="active", sort_order=i)
        for i, room in enumerate(rooms)
    ]
    db_session.add_all(courses)
    await db_session.flush()

    today = date.today()
    db_session.add_all([
        CourseSchedule(
            course_id=c.id, teacher_id=teacher.id,
            start_date=today - timedelta(days=1), end_date=today + timedelta(days=30),
            time_slots='[{"weekday": 3, "time_slot": "09:00-11:00"}]',
            price=100.0, schedule_type="fixed", schedule_status="in_progress",
        )
        for c in courses
    ])
    await db_session.flush()

    return {"city_a": city_a, "city_b": city_b, "courses": courses}


class TestCoursesCityFilter:
    async def test_no_city_returns_all(self, client, seed_city_filter_data):
        """不传 city_id 返回全部城市课程（回归基线）。"""
        resp = await client.get("/api/v1/training/courses?category=skills")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    async def test_filter_by_city_a(self, client, seed_city_filter_data):
        """city_id=甲市 只返回甲市与无城市培训室的课程，total 无笛卡尔积放大。"""
        city_a_id = seed_city_filter_data["city_a"].id
        resp = await client.get(
            f"/api/v1/training/courses?category=skills&city_id={city_a_id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        names = {item["name"] for item in data["items"]}
        assert names == {"甲市培训室课程", "无城市培训室课程"}
        assert data["total"] == 2

    async def test_filter_by_city_b_excludes_other_city(self, client, seed_city_filter_data):
        """city_id=乙市 不含甲市课程。"""
        city_b_id = seed_city_filter_data["city_b"].id
        resp = await client.get(
            f"/api/v1/training/courses?category=skills&city_id={city_b_id}"
        )
        data = resp.json()
        names = {item["name"] for item in data["items"]}
        assert "甲市培训室课程" not in names
        assert data["total"] == 2
