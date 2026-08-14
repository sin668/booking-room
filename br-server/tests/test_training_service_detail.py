"""Unit tests for get_training_room_detail in training_service."""

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
async def seed_detail_data(db_session: AsyncSession):
    """播种培训室详情测试数据。"""
    # 城市
    city = City(name="茂名市", province="广东", sort_order=1, status="active")
    db_session.add(city)
    await db_session.flush()

    # 培训室
    training_room = StudyRoom(
        name="培训中心A",
        description="一流培训环境",
        cover_image="https://example.com/cover.jpg",
        address="广东省茂名市XX路1号",
        business_hours="08:00-22:00",
        status="open",
        room_type="training",
        min_price=50.0,
        rating=4.8,
        city_id=city.id,
    )
    db_session.add(training_room)

    comprehensive_room = StudyRoom(
        name="综合学习中心",
        description="综合学习环境",
        address="广东省茂名市YY路2号",
        business_hours="07:00-23:00",
        status="open",
        room_type="comprehensive",
        min_price=10.0,
        rating=4.5,
        city_id=city.id,
    )
    db_session.add(comprehensive_room)

    study_room = StudyRoom(
        name="普通自习室",
        description="安静自习",
        address="地址C",
        status="open",
        room_type="study",
        min_price=8.0,
        city_id=city.id,
    )
    db_session.add(study_room)

    empty_room = StudyRoom(
        name="空培训室",
        description="暂无课程",
        address="地址D",
        status="open",
        room_type="training",
        min_price=30.0,
        rating=4.0,
        city_id=city.id,
    )
    db_session.add(empty_room)
    await db_session.flush()

    # 教师（教师1将关联多门课程，用于去重测试）
    teacher1 = Teacher(name="李老师", title="考研名师", rating=4.9)
    teacher2 = Teacher(name="王老师", title="公考专家", rating=4.8)
    db_session.add_all([teacher1, teacher2])
    await db_session.flush()

    # 课程（培训中心A）
    courses = [
        Course(
            room_id=training_room.id,
            teacher_id=teacher1.id,
            name="考研政治冲刺",
            category="postgraduate",
            price=80.0,
            rating=4.9,
            enrollment_count=300,
            is_hot=True,
            sort_order=1,
            status="active",
            tags="考研,政治",
        ),
        Course(
            room_id=training_room.id,
            teacher_id=teacher1.id,  # 同一教师，用于去重测试
            name="考研英语强化",
            category="postgraduate",
            price=70.0,
            rating=4.8,
            enrollment_count=200,
            is_hot=True,
            sort_order=2,
            status="active",
            tags="考研,英语",
        ),
        Course(
            room_id=training_room.id,
            teacher_id=teacher2.id,
            name="公务员行测精讲",
            category="civil_service",
            price=60.0,
            rating=4.7,
            enrollment_count=150,
            is_hot=False,
            sort_order=3,
            status="active",
            tags="公考,行测",
        ),
        Course(
            room_id=training_room.id,
            teacher_id=None,  # 无教师课程
            name="自主练习题",
            category="skills",
            price=40.0,
            rating=4.5,
            enrollment_count=50,
            is_hot=False,
            sort_order=4,
            status="active",
            tags=None,  # 测试 tags=None
        ),
        # 非 active 课程（不应出现）
        Course(
            room_id=training_room.id,
            teacher_id=None,
            name="已下线课程",
            category="skills",
            price=30.0,
            rating=4.0,
            enrollment_count=10,
            is_hot=False,
            sort_order=99,
            status="inactive",
            tags="已下线",
        ),
    ]
    db_session.add_all(courses)
    await db_session.flush()

    return {
        "city": city,
        "training_room": training_room,
        "comprehensive_room": comprehensive_room,
        "study_room": study_room,
        "empty_room": empty_room,
        "teacher1": teacher1,
        "teacher2": teacher2,
    }


# ---------------------------------------------------------------------------
# get_training_room_detail
# ---------------------------------------------------------------------------


class TestGetTrainingRoomDetail:
    @pytest.mark.asyncio
    async def test_training_room_detail_all_fields(
        self, db_session: AsyncSession, seed_detail_data
    ):
        """正常培训室详情返回所有字段。"""
        from app.services.training_service import get_training_room_detail

        room = seed_detail_data["training_room"]
        result = await get_training_room_detail(db_session, room.id)

        assert result is not None
        # 房间基本信息
        assert result.id == room.id
        assert result.name == "培训中心A"
        assert result.description == "一流培训环境"
        assert result.cover_image == "https://example.com/cover.jpg"
        assert result.address == "广东省茂名市XX路1号"
        assert result.business_hours == "08:00-22:00"
        assert result.status == "open"
        assert result.room_type == "training"
        assert float(result.min_price) == 50.0
        assert result.city_id == seed_detail_data["city"].id
        assert result.city_name == "茂名市"
        assert float(result.rating) == 4.8

        # 教室概况统计：4 门 active 课程
        assert result.classroom_count == 4
        assert result.class_capacity == "8-12"
        # 2 位去重教师（teacher1 出现 2 次，teacher2 出现 1 次）
        assert result.teacher_count == 2
        # 总学生数 = 300 + 200 + 150 + 50 = 700
        assert result.total_students == 700

        # 教师列表
        assert len(result.teachers) == 2
        teacher_names = {t.name for t in result.teachers}
        assert teacher_names == {"李老师", "王老师"}

        # 课程列表（仅 active，按 sort_order 排序）
        assert len(result.courses) == 4
        assert result.courses[0].name == "考研政治冲刺"
        assert result.courses[1].name == "考研英语强化"
        assert result.courses[2].name == "公务员行测精讲"
        assert result.courses[3].name == "自主练习题"

        # 课程 room_name 正确
        for course in result.courses:
            assert course.room_name == "培训中心A"

    @pytest.mark.asyncio
    async def test_comprehensive_room_returns_same_structure(
        self, db_session: AsyncSession, seed_detail_data
    ):
        """综合学习中心（room_type=comprehensive）返回相同结构。"""
        from app.services.training_service import get_training_room_detail

        room = seed_detail_data["comprehensive_room"]
        result = await get_training_room_detail(db_session, room.id)

        assert result is not None
        assert result.room_type == "comprehensive"
        assert result.name == "综合学习中心"
        # 没有课程
        assert result.classroom_count == 0
        assert result.teacher_count == 0
        assert result.total_students == 0
        assert result.courses == []
        assert result.teachers == []

    @pytest.mark.asyncio
    async def test_nonexistent_room_returns_none(
        self, db_session: AsyncSession, seed_detail_data
    ):
        """不存在的 room_id 返回 None。"""
        from app.services.training_service import get_training_room_detail

        result = await get_training_room_detail(db_session, 99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_study_room_returns_none(
        self, db_session: AsyncSession, seed_detail_data
    ):
        """room_type=study 的房间返回 None（仅允许 training/comprehensive）。"""
        from app.services.training_service import get_training_room_detail

        room = seed_detail_data["study_room"]
        result = await get_training_room_detail(db_session, room.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_teacher_deduplication(
        self, db_session: AsyncSession, seed_detail_data
    ):
        """同一教师关联多门课程时，teachers 列表不重复。"""
        from app.services.training_service import get_training_room_detail

        room = seed_detail_data["training_room"]
        result = await get_training_room_detail(db_session, room.id)

        assert result is not None
        # teacher1 (李老师) 关联了 2 门课程，但 teachers 列表中只出现 1 次
        teacher1_count = sum(
            1 for t in result.teachers if t.name == "李老师"
        )
        assert teacher1_count == 1
        assert result.teacher_count == 2

    @pytest.mark.asyncio
    async def test_empty_courses_scenario(
        self, db_session: AsyncSession, seed_detail_data
    ):
        """没有课程的培训室返回空列表，统计值为 0。"""
        from app.services.training_service import get_training_room_detail

        room = seed_detail_data["empty_room"]
        result = await get_training_room_detail(db_session, room.id)

        assert result is not None
        assert result.classroom_count == 0
        assert result.teacher_count == 0
        assert result.total_students == 0
        assert result.courses == []
        assert result.teachers == []

    @pytest.mark.asyncio
    async def test_tags_parsing(
        self, db_session: AsyncSession, seed_detail_data
    ):
        """tags 字段正确解析：逗号分隔字符串转为列表，None 转为空列表。"""
        from app.services.training_service import get_training_room_detail

        room = seed_detail_data["training_room"]
        result = await get_training_room_detail(db_session, room.id)

        assert result is not None
        # 有 tags 的课程
        course_with_tags = next(
            c for c in result.courses if c.name == "考研政治冲刺"
        )
        assert course_with_tags.tags == ["考研", "政治"]

        # tags=None 的课程
        course_no_tags = next(
            c for c in result.courses if c.name == "自主练习题"
        )
        assert course_no_tags.tags == []

    @pytest.mark.asyncio
    async def test_inactive_courses_excluded(
        self, db_session: AsyncSession, seed_detail_data
    ):
        """status != active 的课程不包含在结果中。"""
        from app.services.training_service import get_training_room_detail

        room = seed_detail_data["training_room"]
        result = await get_training_room_detail(db_session, room.id)

        assert result is not None
        course_names = [c.name for c in result.courses]
        assert "已下线课程" not in course_names

    @pytest.mark.asyncio
    async def test_course_teacher_info(
        self, db_session: AsyncSession, seed_detail_data
    ):
        """课程中嵌套的 teacher 字段正确。"""
        from app.services.training_service import get_training_room_detail

        room = seed_detail_data["training_room"]
        result = await get_training_room_detail(db_session, room.id)

        assert result is not None
        # 有教师的课程
        course_with_teacher = next(
            c for c in result.courses if c.name == "考研政治冲刺"
        )
        assert course_with_teacher.teacher is not None
        assert course_with_teacher.teacher.name == "李老师"

        # 无教师的课程
        course_no_teacher = next(
            c for c in result.courses if c.name == "自主练习题"
        )
        assert course_no_teacher.teacher is None
