"""TDD tests for course detail API (Task 4).

Covers:
- 4.3 CourseDetailResponse / RoomBrief / RelatedCourseItem schemas
- 4.4 training_service.get_course_detail()
- 4.5 GET /api/v1/training/courses/{course_id} route
"""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def seed_course_detail_data(db_session: AsyncSession):
    """播种课程详情测试数据。"""
    city = City(name="茂名市", province="广东", sort_order=1, status="active")
    db_session.add(city)
    await db_session.flush()

    room = StudyRoom(
        name="培训中心A", address="茂名市光谷大道88号",
        status="open", room_type="training", min_price=50.0,
        city_id=city.id, cover_image="https://img.example.com/room.jpg",
    )
    db_session.add(room)
    await db_session.flush()

    teacher = Teacher(name="李老师", title="考研名师", rating=4.9, avatar="https://img.example.com/teacher.jpg")
    db_session.add(teacher)
    await db_session.flush()

    # 主课程（含 description）
    course = Course(
        room_id=room.id, teacher_id=teacher.id,
        name="考研政治冲刺", category="postgraduate", price=80.0,
        rating=4.9, enrollment_count=300, sort_order=1,
        status="active", tags="考研,政治",
        description="本课程为考研政治冲刺阶段专项训练",
        is_hot=True,
    )
    db_session.add(course)
    await db_session.flush()

    # 课时
    lessons = [
        CourseLesson(course_id=course.id, title="第一章 马原", sort_order=1, duration_minutes=45, is_free_preview=True),
        CourseLesson(course_id=course.id, title="第二章 毛中特", sort_order=2, duration_minutes=60),
        CourseLesson(course_id=course.id, title="第三章 史纲", sort_order=3, duration_minutes=50),
    ]
    db_session.add_all(lessons)

    # 同分类其他课程（用于 related_courses）
    related = [
        Course(
            room_id=room.id, teacher_id=teacher.id,
            name="考研英语强化", category="postgraduate", price=70.0,
            rating=4.8, enrollment_count=200, sort_order=2,
            status="active", tags="考研,英语",
        ),
        Course(
            room_id=room.id, teacher_id=None,
            name="考研数学基础", category="postgraduate", price=60.0,
            rating=4.5, enrollment_count=100, sort_order=3,
            status="active", tags="考研,数学",
        ),
    ]
    db_session.add_all(related)

    # 不同分类课程（不应出现在 related）
    other_cat = Course(
        room_id=room.id, teacher_id=None,
        name="公务员行测精讲", category="civil_service", price=55.0,
        rating=4.7, enrollment_count=150, sort_order=4,
        status="active", tags="公考",
    )
    db_session.add(other_cat)

    # 已下线课程（不应出现）
    inactive = Course(
        room_id=room.id, teacher_id=None,
        name="已下线课程", category="postgraduate", price=30.0,
        rating=4.0, enrollment_count=10, sort_order=99,
        status="inactive", tags="已下线",
    )
    db_session.add(inactive)

    await db_session.flush()

    return {
        "course_id": course.id,
        "room_id": room.id,
        "teacher_id": teacher.id,
        "inactive_course_id": inactive.id,
    }


@pytest.fixture
async def seed_course_no_teacher_no_room(db_session: AsyncSession):
    """播种无教师和教室的课程。"""
    # 创建课程，room_id 指向一个不存在的房间（使用 0 或 FK 允许的话用 None）
    # 由于 room_id 是 NOT NULL FK，我们创建一个 room 但不创建 teacher
    room = StudyRoom(
        name="临时教室", address="地址", status="open",
        room_type="training", min_price=10.0,
    )
    db_session.add(room)
    await db_session.flush()

    course = Course(
        room_id=room.id, teacher_id=None,
        name="无教师课程", category="skills", price=50.0,
        rating=4.0, enrollment_count=20, sort_order=1,
        status="active", tags="技能",
    )
    db_session.add(course)
    await db_session.flush()

    return {"course_id": course.id}


# ---------------------------------------------------------------------------
# 4.3 Schema Tests (can run without DB)
# ---------------------------------------------------------------------------


class TestCourseDetailSchemas:
    """测试 CourseDetailResponse / RoomBrief / RelatedCourseItem Schema。"""

    def test_roombrief_creation(self):
        """RoomBrief 可正常创建。"""
        from app.schemas.course import RoomBrief

        brief = RoomBrief(id=1, name="教室A", address="地址A", cover_image="img.jpg")
        assert brief.id == 1
        assert brief.name == "教室A"
        assert brief.address == "地址A"
        assert brief.cover_image == "img.jpg"

    def test_roombrief_cover_image_optional(self):
        """RoomBrief cover_image 可选。"""
        from app.schemas.course import RoomBrief

        brief = RoomBrief(id=1, name="教室A", address="地址A")
        assert brief.cover_image is None

    def test_relatedcourseitem_creation(self):
        """RelatedCourseItem 可正常创建。"""
        from app.schemas.course import RelatedCourseItem

        item = RelatedCourseItem(id=1, name="课程A", price=Decimal("80.00"))
        assert item.id == 1
        assert item.price == Decimal("80.00")
        assert item.cover_image is None

    def test_course_detail_response_creation(self):
        """CourseDetailResponse 完整创建。"""
        from app.schemas.course import CourseDetailResponse, RoomBrief, TeacherBrief

        resp = CourseDetailResponse(
            id=1, name="考研政治冲刺", category="postgraduate",
            price=Decimal("80.00"), rating=Decimal("4.9"),
            enrollment_count=300, status="active",
            description="课程描述",
            teacher=TeacherBrief(id=1, name="李老师", rating=Decimal("4.9")),
            room=RoomBrief(id=1, name="教室A", address="地址A"),
            lessons=[], related_courses=[],
        )
        assert resp.description == "课程描述"
        assert resp.teacher.name == "李老师"
        assert resp.room.name == "教室A"
        assert resp.tags == []
        assert resp.is_hot is False

    def test_course_detail_tags_validator(self):
        """tags 字段验证器正常工作。"""
        from app.schemas.course import CourseDetailResponse

        # 逗号分隔字符串
        resp = CourseDetailResponse(
            id=1, name="test", category="test",
            price=Decimal("10"), rating=Decimal("4.0"),
            enrollment_count=0, status="active",
            tags="考研,政治",
        )
        assert resp.tags == ["考研", "政治"]

        # None -> 空列表
        resp2 = CourseDetailResponse(
            id=2, name="test2", category="test",
            price=Decimal("10"), rating=Decimal("4.0"),
            enrollment_count=0, status="active",
            tags=None,
        )
        assert resp2.tags == []

        # 空字符串 -> 空列表
        resp3 = CourseDetailResponse(
            id=3, name="test3", category="test",
            price=Decimal("10"), rating=Decimal("4.0"),
            enrollment_count=0, status="active",
            tags="",
        )
        assert resp3.tags == []


# ---------------------------------------------------------------------------
# 4.4 Service Tests
# ---------------------------------------------------------------------------


class TestGetCourseDetailService:
    """测试 training_service.get_course_detail()。"""

    @pytest.mark.asyncio
    async def test_returns_full_detail(
        self, db_session: AsyncSession, seed_course_detail_data
    ):
        """正常返回课程详情，含教师、教室、课时和相关课程。"""
        from app.services.training_service import get_course_detail

        ids = seed_course_detail_data
        result = await get_course_detail(db_session, ids["course_id"])

        assert result is not None
        assert result.id == ids["course_id"]
        assert result.name == "考研政治冲刺"
        assert result.category == "postgraduate"
        assert result.price == Decimal("80.00")
        assert result.description == "本课程为考研政治冲刺阶段专项训练"
        assert result.status == "active"
        assert result.is_hot is True
        assert result.tags == ["考研", "政治"]

        # 教师
        assert result.teacher is not None
        assert result.teacher.name == "李老师"
        assert result.teacher.title == "考研名师"

        # 教室
        assert result.room is not None
        assert result.room.name == "培训中心A"
        assert result.room.address == "茂名市光谷大道88号"

        # 课时（按 sort_order 排序）
        assert len(result.lessons) == 3
        assert result.lessons[0].title == "第一章 马原"
        assert result.lessons[1].title == "第二章 毛中特"
        assert result.lessons[2].title == "第三章 史纲"

        # 相关课程（同分类 postgraduate，排除自身，不含已下线）
        assert len(result.related_courses) == 2
        related_names = [c.name for c in result.related_courses]
        assert "考研英语强化" in related_names
        assert "考研数学基础" in related_names
        assert "考研政治冲刺" not in related_names  # 排除自身
        assert "已下线课程" not in related_names  # 排除 inactive
        assert "公务员行测精讲" not in related_names  # 不同分类

    @pytest.mark.asyncio
    async def test_course_not_found(
        self, db_session: AsyncSession, seed_course_detail_data
    ):
        """不存在的课程返回 None。"""
        from app.services.training_service import get_course_detail

        result = await get_course_detail(db_session, 99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_inactive_course_returns_none(
        self, db_session: AsyncSession, seed_course_detail_data
    ):
        """已下线课程返回 None。"""
        from app.services.training_service import get_course_detail
        from sqlalchemy import select
        from app.models.course import Course

        # 找到已下线课程的 ID
        ids = seed_course_detail_data
        result = await db_session.execute(
            select(Course).where(Course.status == "inactive")
        )
        inactive_course = result.scalar_one()

        detail = await get_course_detail(db_session, inactive_course.id)
        assert detail is None

    @pytest.mark.asyncio
    async def test_no_teacher_returns_none_teacher(
        self, db_session: AsyncSession, seed_course_no_teacher_no_room
    ):
        """无教师的课程，teacher 字段为 None。"""
        from app.services.training_service import get_course_detail

        ids = seed_course_no_teacher_no_room
        result = await get_course_detail(db_session, ids["course_id"])

        assert result is not None
        assert result.teacher is None
        assert result.room is not None  # room 仍然存在

    @pytest.mark.asyncio
    async def test_no_lessons_returns_empty_list(
        self, db_session: AsyncSession, seed_course_no_teacher_no_room
    ):
        """无课时的课程，lessons 为空列表。"""
        from app.services.training_service import get_course_detail

        ids = seed_course_no_teacher_no_room
        result = await get_course_detail(db_session, ids["course_id"])

        assert result is not None
        assert result.lessons == []

    @pytest.mark.asyncio
    async def test_no_related_courses(
        self, db_session: AsyncSession, seed_course_no_teacher_no_room
    ):
        """无同分类课程时，related_courses 为空列表。"""
        from app.services.training_service import get_course_detail

        ids = seed_course_no_teacher_no_room
        result = await get_course_detail(db_session, ids["course_id"])

        assert result is not None
        assert result.related_courses == []


# ---------------------------------------------------------------------------
# 4.5 Route Tests
# ---------------------------------------------------------------------------


class TestCourseDetailRoute:
    """测试 GET /api/v1/training/courses/{course_id} 路由。"""

    @pytest.mark.asyncio
    async def test_get_course_detail_200(
        self, client: AsyncClient, seed_course_detail_data
    ):
        """正常请求返回 200。"""
        ids = seed_course_detail_data
        resp = await client.get(f"/api/v1/training/courses/{ids['course_id']}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["id"] == ids["course_id"]
        assert data["name"] == "考研政治冲刺"
        assert data["description"] == "本课程为考研政治冲刺阶段专项训练"
        assert data["teacher"]["name"] == "李老师"
        assert data["room"]["name"] == "培训中心A"
        assert len(data["lessons"]) == 3
        assert len(data["related_courses"]) == 2

    @pytest.mark.asyncio
    async def test_get_course_detail_404(
        self, client: AsyncClient, seed_course_detail_data
    ):
        """不存在的课程返回 404。"""
        resp = await client.get("/api/v1/training/courses/99999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_course_detail_inactive_404(
        self, client: AsyncClient, seed_course_detail_data
    ):
        """已下线课程返回 404。"""
        ids = seed_course_detail_data
        resp = await client.get(f"/api/v1/training/courses/{ids['inactive_course_id']}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_course_detail_response_fields(
        self, client: AsyncClient, seed_course_detail_data
    ):
        """响应包含所有必需字段。"""
        ids = seed_course_detail_data
        resp = await client.get(f"/api/v1/training/courses/{ids['course_id']}")
        data = resp.json()

        # 验证所有顶层字段存在
        required_fields = [
            "id", "name", "cover_image", "category", "price",
            "rating", "enrollment_count", "schedule", "tags",
            "status", "is_hot", "description", "teacher", "room",
            "lessons", "related_courses",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_lessons_sorted_by_sort_order(
        self, client: AsyncClient, seed_course_detail_data
    ):
        """课时按 sort_order 排序。"""
        ids = seed_course_detail_data
        resp = await client.get(f"/api/v1/training/courses/{ids['course_id']}")
        data = resp.json()

        lessons = data["lessons"]
        assert len(lessons) == 3
        assert lessons[0]["title"] == "第一章 马原"
        assert lessons[1]["title"] == "第二章 毛中特"
        assert lessons[2]["title"] == "第三章 史纲"

    @pytest.mark.asyncio
    async def test_related_courses_max_6(
        self, client: AsyncClient, seed_course_detail_data
    ):
        """相关课程最多返回 6 门。"""
        ids = seed_course_detail_data
        resp = await client.get(f"/api/v1/training/courses/{ids['course_id']}")
        data = resp.json()

        assert len(data["related_courses"]) <= 6
