"""C 端课程展示口径测试：没有进行中固定班课排课的课程不展示。

覆盖 4 个列表类展示入口：
- list_courses（培训课程列表 /pages/training/index）
- get_training_room_detail（培训室详情课程区 /pages/booking/detail）
- list_training_rooms 热门课程
- get_course_detail 相关课程
"""

from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.course_schedule import CourseSchedule
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher


@pytest.fixture
async def seed_visibility_data(db_session: AsyncSession):
    """播种 4 门课程，分别覆盖不同排课状态。"""
    room = StudyRoom(
        name="可见性培训中心", address="地址", status="open",
        room_type="training", min_price=10.0, business_hours="08:00-22:00",
    )
    db_session.add(room)
    await db_session.flush()

    teacher = Teacher(name="张老师", title="骨干", rating=4.8)
    db_session.add(teacher)
    await db_session.flush()

    common = dict(room_id=room.id, category="primaryschool", status="active")
    courses = [
        Course(name="进行中固定班课", sort_order=1, is_hot=True, **common),
        Course(name="无排课课程", sort_order=2, is_hot=True, **common),
        Course(name="仅已完成排课课程", sort_order=3, is_hot=True, **common),
        Course(name="仅定制排课课程", sort_order=4, is_hot=True, **common),
    ]
    db_session.add_all(courses)
    await db_session.flush()

    today = date.today()
    schedules = [
        # 进行中固定班课排课 → 该课程应展示
        CourseSchedule(
            course_id=courses[0].id, teacher_id=teacher.id,
            start_date=today - timedelta(days=10), end_date=today + timedelta(days=30),
            time_slots='[{"weekday": 5, "time_slot": "08:00-10:00"}]',
            price=100.0, schedule_type="fixed", schedule_status="in_progress",
        ),
        # 已完成固定班课排课 → 该课程不应展示
        CourseSchedule(
            course_id=courses[2].id, teacher_id=teacher.id,
            start_date=today - timedelta(days=90), end_date=today - timedelta(days=30),
            time_slots='[{"weekday": 1, "time_slot": "09:00-11:00"}]',
            price=90.0, schedule_type="fixed", schedule_status="completed",
        ),
        # 定制排课（进行中）→ 定制排课不算固定班课，该课程不应展示
        CourseSchedule(
            course_id=courses[3].id, teacher_id=teacher.id,
            start_date=today, end_date=today + timedelta(days=30),
            price=120.0, schedule_type="custom", schedule_status="in_progress",
        ),
    ]
    db_session.add_all(schedules)
    await db_session.flush()

    return {"room": room, "courses": courses}


class TestListCoursesVisibility:
    @pytest.mark.asyncio
    async def test_only_courses_with_in_progress_fixed_schedule_shown(
        self, db_session: AsyncSession, seed_visibility_data
    ):
        from app.services.training_service import list_courses

        result = await list_courses(db_session)
        names = [item.name for item in result.items]
        assert names == ["进行中固定班课"]
        assert result.total == 1
        # 展示数据取自排课记录
        assert result.items[0].price == 100.0
        assert result.items[0].teacher is not None


class TestTrainingRoomDetailVisibility:
    @pytest.mark.asyncio
    async def test_room_detail_courses_hide_without_in_progress_fixed(
        self, db_session: AsyncSession, seed_visibility_data
    ):
        from app.services.training_service import get_training_room_detail

        result = await get_training_room_detail(
            db_session, seed_visibility_data["room"].id
        )
        assert result is not None
        names = [c.name for c in result.courses]
        assert names == ["进行中固定班课"]
        # 统计口径同步排除隐藏课程
        assert result.classroom_count == 1


class TestHotCoursesVisibility:
    @pytest.mark.asyncio
    async def test_hot_courses_hide_without_in_progress_fixed(
        self, db_session: AsyncSession, seed_visibility_data
    ):
        from app.services.training_service import list_training_rooms

        result = await list_training_rooms(db_session)
        room = result.items[0]
        names = [c.name for c in room.hot_courses]
        assert names == ["进行中固定班课"]


class TestRelatedCoursesVisibility:
    @pytest.mark.asyncio
    async def test_related_courses_hide_without_in_progress_fixed(
        self, db_session: AsyncSession, seed_visibility_data
    ):
        from app.services.training_service import get_course_detail

        visible_course = seed_visibility_data["courses"][0]
        result = await get_course_detail(db_session, visible_course.id)
        assert result is not None
        related_names = [c.name for c in result.related_courses]
        assert related_names == []
