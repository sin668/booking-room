"""Integration tests for Course Booking API.

注意：当前测试基础设施使用 SQLite 内存数据库，不支持 PostgreSQL ARRAY 类型
（Booking.lesson_ids 字段）。集成测试需要连接真实 PostgreSQL 才能运行。
"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.study_room import StudyRoom
from app.models.user import User

# SQLite 不支持 PostgreSQL ARRAY 类型，所有需要 db_session 的测试跳过
_requires_pg = pytest.mark.skip(reason="需要 PostgreSQL 数据库，SQLite 不支持 ARRAY 类型")

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
async def seed_course_data(db_session: AsyncSession):
    """创建教室 + 课程 + 课时测试数据。"""
    room = StudyRoom(name="Test Room", address="123 Test St", status="open", min_price=10.0)
    db_session.add(room)
    await db_session.flush()

    course = Course(
        room_id=room.id,
        name="钢琴基础课",
        category="music",
        price=80.0,
        custom_price=200.0,
        full_package_price=860.0,
        status="active",
    )
    db_session.add(course)
    await db_session.flush()

    lessons = []
    for i in range(12):
        lesson = CourseLesson(
            course_id=course.id,
            title=f"第{i+1}课",
            description=f"课时描述{i+1}",
            duration_minutes=45,
            sort_order=i + 1,
            is_free_preview=(i == 0),
        )
        db_session.add(lesson)
        lessons.append(lesson)
    await db_session.flush()

    return {"room": room, "course": course, "lessons": lessons}


@pytest.fixture
async def auth_client(client: AsyncClient):
    """带认证的 client。"""
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def seed_user(db_session: AsyncSession):
    """创建测试用户。"""
    user = User(
        id=USER_ID,
        phone="18800000099",
        nickname="Course User",
        password_hash="hash",
        balance=Decimal("1000.00"),
    )
    db_session.add(user)
    await db_session.flush()
    return user


@_requires_pg
class TestGetCourseLessons:
    """GET /api/v1/courses/{id}/lessons。"""

    @pytest.mark.asyncio
    async def test_get_course_lessons_success(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_course_data,
    ):
        """返回课程详情 + 课时列表。"""
        course = seed_course_data["course"]
        resp = await auth_client.get(f"/api/v1/courses/{course.id}/lessons")
        assert resp.status_code == 200
        data = resp.json()
        assert data["course"]["name"] == "钢琴基础课"
        assert data["total_lessons_count"] == 12
        assert len(data["lessons"]) == 12
        assert data["lessons"][0]["title"] == "第1课"

    @pytest.mark.asyncio
    async def test_get_course_lessons_not_found(self, auth_client: AsyncClient):
        """不存在的课程返回 404。"""
        resp = await auth_client.get("/api/v1/courses/99999/lessons")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "课程不存在"

    @pytest.mark.asyncio
    async def test_get_course_lessons_no_auth(self, client: AsyncClient, seed_course_data):
        """未认证返回 401。"""
        course = seed_course_data["course"]
        resp = await client.get(f"/api/v1/courses/{course.id}/lessons")
        assert resp.status_code == 401


@_requires_pg
class TestCreateCourseBooking:
    """POST /api/v1/course-bookings。"""

    @pytest.mark.asyncio
    async def test_create_course_booking_balance_payment(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_course_data,
        seed_user,
    ):
        """余额支付创建课程预约。"""
        course = seed_course_data["course"]
        lesson_ids = [lesson.id for lesson in seed_course_data["lessons"][:3]]

        resp = await auth_client.post(
            "/api/v1/course-bookings",
            json={
                "course_id": course.id,
                "booking_type": "fixed",
                "lesson_ids": lesson_ids,
                "schedule_type": "fixed",
                "payment_method": "balance",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["course_name"] == "钢琴基础课"
        assert data["lesson_count"] == 3
        assert data["original_price"] == 240.0  # 3 × 80
        assert data["discount_amount"] == 0.0
        assert data["total_price"] == 240.0
        assert data["payment_status"] == "paid"
        assert data["payment_method"] == "balance"
        assert data["booking_type"] == "course"

    @pytest.mark.asyncio
    async def test_create_course_booking_full_package(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_course_data,
        seed_user,
    ):
        """全套优惠价格计算。"""
        course = seed_course_data["course"]
        lesson_ids = [lesson.id for lesson in seed_course_data["lessons"]]  # all 12

        resp = await auth_client.post(
            "/api/v1/course-bookings",
            json={
                "course_id": course.id,
                "booking_type": "fixed",
                "lesson_ids": lesson_ids,
                "schedule_type": "fixed",
                "payment_method": "balance",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["original_price"] == 860.0  # full_package_price
        assert data["discount_amount"] == 100.0  # 12*80 - 860
        assert data["total_price"] == 760.0

    @pytest.mark.asyncio
    async def test_create_course_booking_empty_lessons(self, auth_client: AsyncClient, seed_course_data):
        """空 lesson_ids 返回 422。"""
        course = seed_course_data["course"]
        resp = await auth_client.post(
            "/api/v1/course-bookings",
            json={
                "course_id": course.id,
                "booking_type": "fixed",
                "lesson_ids": [],
                "schedule_type": "fixed",
                "payment_method": "balance",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_course_booking_invalid_course(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_user,
    ):
        """不存在的课程返回 404。"""
        resp = await auth_client.post(
            "/api/v1/course-bookings",
            json={
                "course_id": 99999,
                "booking_type": "fixed",
                "lesson_ids": [1],
                "schedule_type": "fixed",
                "payment_method": "balance",
            },
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "课程不存在"

    @pytest.mark.asyncio
    async def test_create_course_booking_invalid_lesson_ids(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_course_data,
        seed_user,
    ):
        """无效 lesson_ids 返回 400。"""
        course = seed_course_data["course"]
        resp = await auth_client.post(
            "/api/v1/course-bookings",
            json={
                "course_id": course.id,
                "booking_type": "fixed",
                "lesson_ids": [99998, 99999],
                "schedule_type": "fixed",
                "payment_method": "balance",
            },
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_course_booking_insufficient_balance(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_course_data,
    ):
        """余额不足返回 402。"""
        # 创建余额为 0 的用户
        db_session.add(User(
            id=USER_ID, phone="18800000098",
            nickname="Poor User", password_hash="hash",
            balance=Decimal("0.00"),
        ))
        await db_session.flush()

        course = seed_course_data["course"]
        lesson_ids = [lesson.id for lesson in seed_course_data["lessons"][:3]]
        resp = await auth_client.post(
            "/api/v1/course-bookings",
            json={
                "course_id": course.id,
                "booking_type": "fixed",
                "lesson_ids": lesson_ids,
                "schedule_type": "fixed",
                "payment_method": "balance",
            },
        )
        assert resp.status_code == 402
        assert resp.json()["detail"] == "余额不足"

    @pytest.mark.asyncio
    async def test_create_course_booking_no_auth(self, client: AsyncClient, seed_course_data):
        """未认证返回 401。"""
        course = seed_course_data["course"]
        resp = await client.post(
            "/api/v1/course-bookings",
            json={
                "course_id": course.id,
                "booking_type": "fixed",
                "lesson_ids": [1, 2, 3],
                "schedule_type": "fixed",
                "payment_method": "balance",
            },
        )
        assert resp.status_code == 401


@_requires_pg
class TestCancelCourseBooking:
    """POST /api/v1/course-bookings/{booking_id}/cancel。"""

    @pytest.mark.asyncio
    async def test_cancel_course_booking_success(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_course_data,
        seed_user,
    ):
        """取消课程预约 + 退款。"""
        course = seed_course_data["course"]
        lesson_ids = [lesson.id for lesson in seed_course_data["lessons"][:3]]

        # 先创建预约
        create_resp = await auth_client.post(
            "/api/v1/course-bookings",
            json={
                "course_id": course.id,
                "booking_type": "fixed",
                "lesson_ids": lesson_ids,
                "schedule_type": "fixed",
                "payment_method": "balance",
            },
        )
        assert create_resp.status_code == 201
        booking_id = create_resp.json()["booking_id"]

        # 取消
        cancel_resp = await auth_client.post(f"/api/v1/course-bookings/{booking_id}/cancel")
        assert cancel_resp.status_code == 200
        data = cancel_resp.json()
        assert data["status"] == "cancelled"
        assert data["refund_amount"] == 240.0

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_booking(self, auth_client: AsyncClient):
        """取消不存在的预约返回 404。"""
        resp = await auth_client.post("/api/v1/course-bookings/99999/cancel")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "预约不存在"

    @pytest.mark.asyncio
    async def test_cancel_course_booking_no_auth(self, client: AsyncClient):
        """未认证返回 401。"""
        resp = await client.post("/api/v1/course-bookings/1/cancel")
        assert resp.status_code == 401
