"""Unit tests for CourseBookingService."""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.course_schedule import CourseSchedule
from app.models.lesson_schedule import LessonSchedule
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.course_booking import CourseBookingCreate
from app.services.course_booking_service import CourseBookingService

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

# SQLite 不支持 PostgreSQL ARRAY 类型（Booking.lesson_ids），
# 需要真实 PG 数据库才能运行集成测试。
try:
    from sqlalchemy.dialects.sqlite import base as _sqlite_mod  # noqa: F401
    _HAS_SQLITE_ARRAY_SUPPORT = False  # SQLite 始终不支持 ARRAY
except ImportError:
    _HAS_SQLITE_ARRAY_SUPPORT = False


def _make_course(
    price=80.0,
    custom_price=0.0,
    full_package_price=None,
    status="active",
    room_id=1,
    name="测试课程",
) -> Course:
    """构造一个轻量 Course mock 对象。"""
    course = MagicMock(spec=Course)
    course.id = 1
    course.name = name
    course.room_id = room_id
    course.price = price
    course.custom_price = custom_price
    course.full_package_price = full_package_price
    course.status = status
    return course


def _make_schedule(
    price=80.0,
    custom_price=0.0,
    full_package_price=None,
    full_custom_price=None,
) -> dict:
    """构造排课价格 dict（与 get_course_with_lessons 返回结构一致）。"""
    return {
        "price": price,
        "custom_price": custom_price,
        "full_package_price": full_package_price,
        "full_custom_price": full_custom_price,
    }


def _make_lesson(lesson_id: int, course_id: int = 1, title: str = "课时") -> CourseLesson:
    lesson = MagicMock(spec=CourseLesson)
    lesson.id = lesson_id
    lesson.course_id = course_id
    lesson.title = title
    return lesson


class TestCourseBookingPricing:
    """价格计算测试。"""

    def setup_method(self):
        self.service = CourseBookingService()

    def test_fixed_pricing(self):
        """固定班课：3 课时 × ¥80 = ¥240。"""
        course = _make_course(price=80.0)
        result = self.service.calculate_price(
            course, _make_schedule(price=80.0), booking_type="fixed",
            lesson_ids=[1, 2, 3], total_lessons=12,
        )
        assert result["original_price"] == Decimal("240.00")
        assert result["discount_amount"] == Decimal("0.00")
        assert result["unit_price"] == Decimal("80.00")
        assert result["total_price"] == Decimal("240.00")

    def test_custom_pricing(self):
        """1V1 定制：2 课时 × ¥200 = ¥400。"""
        course = _make_course(price=80.0, custom_price=200.0)
        result = self.service.calculate_price(
            course, _make_schedule(price=80.0, custom_price=200.0),
            booking_type="custom", lesson_ids=[1, 2], total_lessons=12,
        )
        assert result["original_price"] == Decimal("400.00")
        assert result["discount_amount"] == Decimal("0.00")
        assert result["unit_price"] == Decimal("200.00")
        assert result["total_price"] == Decimal("400.00")

    def test_full_package_pricing(self):
        """全套优惠：12 课时，price=80, full_package_price=860
        → original_price=960（标准价）, discount_amount=100, total=860。"""
        course = _make_course(price=80.0, full_package_price=860.0)
        lesson_ids = list(range(1, 13))  # 12 lessons
        result = self.service.calculate_price(
            course, _make_schedule(price=80.0, full_package_price=860.0),
            booking_type="fixed", lesson_ids=lesson_ids, total_lessons=12,
        )
        assert result["original_price"] == Decimal("960.00")
        assert result["discount_amount"] == Decimal("100.00")  # 12*80 - 860 = 100
        assert result["total_price"] == Decimal("860.00")

    def test_partial_selection_no_full_package(self):
        """部分选择不触发全套优惠：10/12 课时
        → original_price=800, discount_amount=0。"""
        course = _make_course(price=80.0, full_package_price=860.0)
        lesson_ids = list(range(1, 11))  # 10 of 12
        result = self.service.calculate_price(
            course, _make_schedule(price=80.0, full_package_price=860.0),
            booking_type="fixed", lesson_ids=lesson_ids, total_lessons=12,
            selected_count=10,
        )
        assert result["original_price"] == Decimal("800.00")
        assert result["discount_amount"] == Decimal("0.00")
        assert result["total_price"] == Decimal("800.00")

    def test_full_package_not_set(self):
        """full_package_price 为 None 时不触发优惠。"""
        course = _make_course(price=80.0, full_package_price=None)
        lesson_ids = list(range(1, 13))
        result = self.service.calculate_price(
            course, _make_schedule(price=80.0, full_package_price=None),
            booking_type="fixed", lesson_ids=lesson_ids, total_lessons=12,
        )
        assert result["original_price"] == Decimal("960.00")
        assert result["discount_amount"] == Decimal("0.00")
        assert result["total_price"] == Decimal("960.00")

    def test_full_package_price_higher_than_standard_no_negative_discount(self):
        """full_package_price 高于标准价时，discount_amount 为 0。"""
        course = _make_course(price=80.0, full_package_price=1000.0)
        lesson_ids = list(range(1, 13))
        result = self.service.calculate_price(
            course, _make_schedule(price=80.0, full_package_price=1000.0),
            booking_type="fixed", lesson_ids=lesson_ids, total_lessons=12,
        )
        assert result["original_price"] == Decimal("960.00")
        assert result["discount_amount"] == Decimal("0.00")
        assert result["total_price"] == Decimal("1000.00")

    def test_single_lesson_fixed(self):
        """单课时固定班课。"""
        course = _make_course(price=80.0)
        result = self.service.calculate_price(
            course, _make_schedule(price=80.0), booking_type="fixed",
            lesson_ids=[1], total_lessons=12,
        )
        assert result["original_price"] == Decimal("80.00")
        assert result["total_price"] == Decimal("80.00")

    def test_custom_full_package_uses_full_custom_price(self):
        """1V1 定制全套用 full_custom_price（而非 full_package_price），
        基准单价用 custom_price。"""
        course = _make_course(price=80.0, custom_price=120.0)
        lesson_ids = list(range(1, 13))  # 12 计费课时
        result = self.service.calculate_price(
            course,
            _make_schedule(price=80.0, custom_price=120.0,
                           full_package_price=720.0, full_custom_price=1200.0),
            booking_type="custom", lesson_ids=lesson_ids, total_lessons=12,
            selected_count=12,
        )
        assert result["original_price"] == Decimal("1440.00")  # 12*120
        assert result["discount_amount"] == Decimal("240.00")  # 1440 - 1200
        assert result["total_price"] == Decimal("1200.00")

    def test_fixed_full_package_with_free_preview_lesson(self):
        """固定班课全套含免费试听课时：选择全部 12 课时（含 1 节试听），
        计费课时 11，仍应触发全套优惠（回归订单 94 场景）。"""
        course = _make_course(price=55.0, full_package_price=500.0)
        lesson_ids = list(range(1, 12))  # 11 计费课时
        result = self.service.calculate_price(
            course, _make_schedule(price=55.0, full_package_price=500.0),
            booking_type="fixed", lesson_ids=lesson_ids, total_lessons=12,
            selected_count=12,
        )
        assert result["original_price"] == Decimal("605.00")  # 11*55
        assert result["discount_amount"] == Decimal("105.00")  # 605 - 500
        assert result["total_price"] == Decimal("500.00")

    def test_custom_full_package_with_free_preview_lesson(self):
        """1V1 定制全套含免费试听课时：选择全部 12 课时（含 1 节试听），
        计费课时 11，应触发定制全套优惠（回归订单 93 场景）。"""
        course = _make_course(price=80.0, custom_price=120.0)
        lesson_ids = list(range(1, 12))  # 11 计费课时
        result = self.service.calculate_price(
            course,
            _make_schedule(price=80.0, custom_price=120.0,
                           full_package_price=720.0, full_custom_price=1200.0),
            booking_type="custom", lesson_ids=lesson_ids, total_lessons=12,
            selected_count=12,
        )
        assert result["original_price"] == Decimal("1320.00")  # 11*120
        assert result["discount_amount"] == Decimal("120.00")  # 1320 - 1200
        assert result["total_price"] == Decimal("1200.00")


# SQLite 不支持 PostgreSQL ARRAY 类型，DB 测试需要真实 PG 环境
_requires_pg = pytest.mark.skip(reason="需要 PostgreSQL 数据库，SQLite 不支持 ARRAY 类型")


class TestCourseBookingValidation:
    """验证逻辑测试（需要数据库）。"""

    @pytest.mark.asyncio
    async def test_empty_lesson_ids_rejected_by_schema(self):
        """空 lesson_ids 应被 Schema 拒绝。"""
        from app.schemas.course_booking import CourseBookingCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CourseBookingCreate(
                course_id=1,
                booking_type="fixed",
                lesson_ids=[],
                schedule_type="fixed",
                payment_method="balance",
            )

    @_requires_pg
    @pytest.mark.asyncio
    async def test_invalid_course_id_returns_none(self, db_session: AsyncSession):
        """不存在的 course_id 返回 None。"""
        service = CourseBookingService()
        result = await service.get_course_with_lessons(99999, db_session)
        assert result is None

    @_requires_pg
    @pytest.mark.asyncio
    async def test_lesson_not_belonging_to_course(self, db_session: AsyncSession):
        """lesson_id 不属于该课程应报错。"""
        from app.models.study_room import StudyRoom

        # 创建教室
        room = StudyRoom(name="Test Room", address="Addr", status="open", min_price=10.0)
        db_session.add(room)
        await db_session.flush()

        # 创建两个课程
        course_a = Course(
            room_id=room.id, name="课程A", category="music",
            price=80.0, status="active",
        )
        course_b = Course(
            room_id=room.id, name="课程B", category="music",
            price=100.0, status="active",
        )
        db_session.add_all([course_a, course_b])
        await db_session.flush()

        # 为课程 B 创建课时
        lesson_b = CourseLesson(course_id=course_b.id, title="B课时1", sort_order=1)
        db_session.add(lesson_b)
        await db_session.flush()

        # 尝试用课程 A 的预约流程验证课程 B 的课时
        service = CourseBookingService()
        course_data = await service.get_course_with_lessons(course_a.id, db_session)
        valid_lesson_ids = {lesson.id for lesson in course_data["lessons"]}
        invalid_ids = {lesson_b.id} - valid_lesson_ids
        assert len(invalid_ids) == 1  # lesson_b 不属于课程 A

    @_requires_pg
    @pytest.mark.asyncio
    async def test_get_course_with_lessons_returns_correct_data(self, db_session: AsyncSession):
        """正常查询返回课程 + 课时列表。"""
        from app.models.study_room import StudyRoom

        room = StudyRoom(name="Test Room 2", address="Addr", status="open", min_price=10.0)
        db_session.add(room)
        await db_session.flush()

        course = Course(
            room_id=room.id, name="课程X", category="art",
            price=60.0, status="active",
        )
        db_session.add(course)
        await db_session.flush()

        for i in range(3):
            db_session.add(CourseLesson(
                course_id=course.id, title=f"课时{i+1}", sort_order=i + 1,
            ))
        await db_session.flush()

        service = CourseBookingService()
        result = await service.get_course_with_lessons(course.id, db_session)
        assert result is not None
        assert result["course"].name == "课程X"
        assert result["total_lessons_count"] == 3
        assert len(result["lessons"]) == 3


class TestFixedBookingStartDateAndTimeSlots:
    """固定班课下单：预约日期/开课日期取已预约第一课时日期，时段复制排课记录。"""

    async def _setup_fixed_course(self, db_session: AsyncSession, first_lesson_date):
        """创建固定班课完整数据：教室/用户/课程/老师/排课/2 个课时及课时排课。"""
        second_lesson_date = first_lesson_date + timedelta(days=7)
        db_session.add(StudyRoom(id=1, name="Room", address="Addr", status="open"))
        db_session.add(User(
            id=USER_ID, phone="18800000001", nickname="Course User",
            password_hash="hash", balance=Decimal("1000.00"),
        ))
        db_session.add(Course(id=1, room_id=1, name="固定班课", category="training", status="active"))
        db_session.add(Teacher(id=1, name="张老师"))
        db_session.add(CourseSchedule(
            id=1, course_id=1, teacher_id=1,
            start_date=first_lesson_date - timedelta(days=30),
            time_slots='[{"weekday": 5, "time_slot": "08:00-10:00"}]',
            price=Decimal("80.00"), schedule_type="fixed",
        ))
        db_session.add(CourseLesson(id=1, course_id=1, title="第1课", sort_order=1))
        db_session.add(CourseLesson(id=2, course_id=1, title="第2课", sort_order=2))
        db_session.add(LessonSchedule(
            schedule_id=1, lesson_id=1, lesson_date=first_lesson_date,
            lesson_time_slot="08:00-10:00", sort_order=0,
        ))
        db_session.add(LessonSchedule(
            schedule_id=1, lesson_id=2, lesson_date=second_lesson_date,
            lesson_time_slot="08:00-10:00", sort_order=1,
        ))
        await db_session.flush()

    async def _create_fixed_booking(self, db_session: AsyncSession) -> Booking:
        service = CourseBookingService()
        result = await service.create_course_booking(
            USER_ID,
            CourseBookingCreate(
                course_id=1, booking_type="fixed", lesson_ids=[1, 2],
                schedule_type="fixed", payment_method="balance",
            ),
            db_session,
        )
        return (
            await db_session.execute(select(Booking).where(Booking.id == result.booking_id))
        ).scalar_one()

    @pytest.mark.asyncio
    async def test_fixed_booking_future_first_lesson_pending(self, db_session: AsyncSession):
        """第一课时在未来 → 待开始；预约日期=第一课时日期；时段复制排课；不改排课表。"""
        today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
        first_date = today + timedelta(days=10)
        await self._setup_fixed_course(db_session, first_date)

        booking = await self._create_fixed_booking(db_session)

        assert booking.status == "pending"
        assert booking.date == first_date
        assert booking.time_slots == '[{"weekday": 5, "time_slot": "08:00-10:00"}]'
        assert booking.schedule_id == 1
        # 排课表记录不被修改（start_date 保持原值）
        schedule = (
            await db_session.execute(select(CourseSchedule).where(CourseSchedule.id == 1))
        ).scalar_one()
        assert schedule.start_date == first_date - timedelta(days=30)

    @pytest.mark.asyncio
    async def test_fixed_booking_first_lesson_today_confirmed(self, db_session: AsyncSession):
        """第一课时日期 <= 今天 → 进行中（confirmed）。"""
        today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
        await self._setup_fixed_course(db_session, today)

        booking = await self._create_fixed_booking(db_session)

        assert booking.status == "confirmed"
        assert booking.date == today
        assert booking.time_slots == '[{"weekday": 5, "time_slot": "08:00-10:00"}]'
