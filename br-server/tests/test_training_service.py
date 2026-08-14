"""Unit tests for training_service and room_type filter in study_room_service."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def seed_training_data(db_session: AsyncSession):
    """播种培训室、教师和课程测试数据。"""
    # 城市
    city = City(name="茂名市", province="广东", sort_order=1, status="active")
    db_session.add(city)
    await db_session.flush()

    # 培训室（room_type=training）
    rooms = [
        StudyRoom(
            name="培训中心A", description="培训室A", address="地址A",
            status="open", room_type="training", min_price=50.0, city_id=city.id,
            business_hours="08:00-22:00",
        ),
        StudyRoom(
            name="培训中心B", description="培训室B", address="地址B",
            status="open", room_type="training", min_price=40.0, city_id=city.id,
            business_hours="08:00-21:00",
        ),
        StudyRoom(
            name="综合学习中心", description="综合", address="地址C",
            status="open", room_type="comprehensive", min_price=10.0, city_id=city.id,
            business_hours="07:00-23:00",
        ),
        # 普通自习室（不应出现在培训室列表中）
        StudyRoom(
            name="普通自习室", description="普通", address="地址D",
            status="open", room_type="study", min_price=8.0, city_id=city.id,
        ),
        # 已关闭的培训室（不应出现在培训室列表中）
        StudyRoom(
            name="已关闭培训室", description="关闭", address="地址E",
            status="closed", room_type="training", min_price=30.0, city_id=city.id,
        ),
    ]
    db_session.add_all(rooms)
    await db_session.flush()

    # 教师
    teachers = [
        Teacher(name="李老师", title="考研名师", rating=4.9),
        Teacher(name="王老师", title="公考专家", rating=4.8),
    ]
    db_session.add_all(teachers)
    await db_session.flush()

    # 课程
    courses = [
        # 培训中心A 的热门课程（3个）
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
            rating=4.6, enrollment_count=80, is_hot=True, sort_order=3,
            status="active", tags="小学,数学",
        ),
        # 培训中心A 的非热门课程（不应出现在 hot_courses 中）
        Course(
            room_id=rooms[0].id, teacher_id=None,
            name="初中物理提升", category="middleschool", price=55.0,
            rating=4.7, enrollment_count=90, is_hot=False, sort_order=4,
            status="active", tags="初中,物理",
        ),
        # 培训中心B 的热门课程
        Course(
            room_id=rooms[1].id, teacher_id=teachers[0].id,
            name="考研英语强化", category="postgraduate", price=70.0,
            rating=4.8, enrollment_count=200, is_hot=True, sort_order=1,
            status="active", tags="考研,英语",
        ),
        # 已关闭课程（不应出现）
        Course(
            room_id=rooms[0].id, teacher_id=None,
            name="已下线课程", category="skills", price=30.0,
            rating=4.0, enrollment_count=10, is_hot=True, sort_order=99,
            status="inactive", tags="已下线",
        ),
    ]
    db_session.add_all(courses)
    await db_session.flush()


# ---------------------------------------------------------------------------
# list_training_rooms
# ---------------------------------------------------------------------------


class TestListTrainingRooms:
    @pytest.mark.asyncio
    async def test_returns_only_training_and_comprehensive_rooms(
        self, db_session: AsyncSession, seed_training_data
    ):
        """只返回 room_type 为 training 或 comprehensive 且 status=open 的房间。"""
        from app.services.training_service import list_training_rooms

        result = await list_training_rooms(db_session)
        # 3 个符合条件的房间（2 training + 1 comprehensive），排除 study 和 closed
        assert result.total == 3
        room_names = [item.name for item in result.items]
        assert "培训中心A" in room_names
        assert "培训中心B" in room_names
        assert "综合学习中心" in room_names
        assert "普通自习室" not in room_names
        assert "已关闭培训室" not in room_names

    @pytest.mark.asyncio
    async def test_hot_courses_limited_to_3_per_room(
        self, db_session: AsyncSession, seed_training_data
    ):
        """每个房间最多返回 3 门热门课程。"""
        from app.services.training_service import list_training_rooms

        result = await list_training_rooms(db_session)
        room_a = next(item for item in result.items if item.name == "培训中心A")
        # 培训中心A 有 3 门热门课程
        assert len(room_a.hot_courses) == 3

    @pytest.mark.asyncio
    async def test_hot_courses_exclude_non_hot(
        self, db_session: AsyncSession, seed_training_data
    ):
        """非热门课程不出现在 hot_courses 中。"""
        from app.services.training_service import list_training_rooms

        result = await list_training_rooms(db_session)
        room_a = next(item for item in result.items if item.name == "培训中心A")
        course_names = [c.name for c in room_a.hot_courses]
        assert "初中物理提升" not in course_names  # is_hot=False
        assert "已下线课程" not in course_names   # status=inactive

    @pytest.mark.asyncio
    async def test_hot_courses_teacher_info(
        self, db_session: AsyncSession, seed_training_data
    ):
        """热门课程包含教师信息。"""
        from app.services.training_service import list_training_rooms

        result = await list_training_rooms(db_session)
        room_a = next(item for item in result.items if item.name == "培训中心A")
        course_with_teacher = next(
            c for c in room_a.hot_courses if c.name == "考研政治冲刺"
        )
        assert course_with_teacher.teacher is not None
        assert course_with_teacher.teacher.name == "李老师"

        # 无教师的课程
        course_no_teacher = next(
            c for c in room_a.hot_courses if c.name == "小学数学辅导"
        )
        assert course_no_teacher.teacher is None

    @pytest.mark.asyncio
    async def test_pagination(
        self, db_session: AsyncSession, seed_training_data
    ):
        """分页参数正常工作。"""
        from app.services.training_service import list_training_rooms

        result = await list_training_rooms(db_session, page=1, page_size=2)
        assert len(result.items) == 2
        assert result.total == 3
        assert result.page == 1
        assert result.page_size == 2

        result2 = await list_training_rooms(db_session, page=2, page_size=2)
        assert len(result2.items) == 1
        assert result2.total == 3

    @pytest.mark.asyncio
    async def test_city_id_filter(
        self, db_session: AsyncSession, seed_training_data
    ):
        """city_id 过滤正常工作。"""
        from app.services.training_service import list_training_rooms

        # 使用不存在的 city_id
        result = await list_training_rooms(db_session, city_id=9999)
        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_empty_result(
        self, db_session: AsyncSession
    ):
        """空数据库返回空列表。"""
        from app.services.training_service import list_training_rooms

        result = await list_training_rooms(db_session)
        assert result.total == 0
        assert result.items == []


# ---------------------------------------------------------------------------
# list_courses
# ---------------------------------------------------------------------------


class TestListCourses:
    @pytest.mark.asyncio
    async def test_returns_active_courses(
        self, db_session: AsyncSession, seed_training_data
    ):
        """只返回 status=active 的课程。"""
        from app.services.training_service import list_courses

        result = await list_courses(db_session)
        # 共 5 门 active 课程（排除 1 门 inactive）
        assert result.total == 5
        assert all(item.status == "active" for item in result.items)

    @pytest.mark.asyncio
    async def test_category_filter(
        self, db_session: AsyncSession, seed_training_data
    ):
        """category 过滤正常工作。"""
        from app.services.training_service import list_courses

        result = await list_courses(db_session, category="postgraduate")
        assert result.total == 2
        assert all(item.category == "postgraduate" for item in result.items)

    @pytest.mark.asyncio
    async def test_course_includes_room_and_teacher(
        self, db_session: AsyncSession, seed_training_data
    ):
        """课程响应包含房间名和教师信息。"""
        from app.services.training_service import list_courses

        result = await list_courses(db_session)
        course = next(item for item in result.items if item.name == "考研政治冲刺")
        assert course.room_name == "培训中心A"
        assert course.teacher is not None
        assert course.teacher.name == "李老师"

    @pytest.mark.asyncio
    async def test_pagination(
        self, db_session: AsyncSession, seed_training_data
    ):
        """分页参数正常工作。"""
        from app.services.training_service import list_courses

        result = await list_courses(db_session, page=1, page_size=2)
        assert len(result.items) == 2
        assert result.total == 5
        assert result.page_size == 2


# ---------------------------------------------------------------------------
# list_study_rooms with room_type filter
# ---------------------------------------------------------------------------


class TestListStudyRoomsRoomTypeFilter:
    @pytest.mark.asyncio
    async def test_room_type_filter(
        self, db_session: AsyncSession, seed_training_data
    ):
        """room_type 参数过滤自习室。"""
        from app.services.study_room_service import list_study_rooms

        # 只查询 study 类型
        result = await list_study_rooms(db_session, room_type="study")
        assert result.total == 1
        assert result.items[0].name == "普通自习室"

        # 只查询 training 类型（status=open 的有 2 个）
        result2 = await list_study_rooms(db_session, room_type="training")
        assert result2.total == 2

    @pytest.mark.asyncio
    async def test_no_room_type_returns_all_open(
        self, db_session: AsyncSession, seed_training_data
    ):
        """不传 room_type 时返回所有 open 状态的房间。"""
        from app.services.study_room_service import list_study_rooms

        result = await list_study_rooms(db_session)
        # 4 个 open 状态的房间（排除已关闭的）
        assert result.total == 4


# ---------------------------------------------------------------------------
# admin_list_rooms with room_type filter
# ---------------------------------------------------------------------------


class TestAdminListRoomsRoomTypeFilter:
    @pytest.mark.asyncio
    async def test_room_type_filter(
        self, db_session: AsyncSession, seed_training_data
    ):
        """admin_list_rooms 的 room_type 过滤。"""
        from app.services.study_room_service import admin_list_rooms

        result = await admin_list_rooms(db_session, room_type="training")
        # 3 个 training 类型的房间（包含已关闭的）
        assert result.total == 3

    @pytest.mark.asyncio
    async def test_status_and_room_type_combined(
        self, db_session: AsyncSession, seed_training_data
    ):
        """status 和 room_type 同时过滤。"""
        from app.services.study_room_service import admin_list_rooms

        result = await admin_list_rooms(db_session, status="open", room_type="training")
        assert result.total == 2
