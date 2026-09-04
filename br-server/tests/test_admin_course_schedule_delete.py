"""Unit tests for AdminCourseService.delete_schedule 订单关联校验。

删除排课的准入规则：
- 排课不存在 → "not_found"
- 存在非取消状态的关联订单 → "has_active_bookings"（拒绝删除，排课与课时记录保留）
- 无关联订单，或关联订单全部已取消 → "ok"（删除排课 + 对应课时上课时间记录，
  并清空已取消订单的 schedule_id 外键引用）
"""

import uuid
from datetime import date, datetime, time
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.booking import Booking
from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.course_schedule import CourseSchedule
from app.models.lesson_schedule import LessonSchedule
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.services.admin_course_service import AdminCourseService

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def _seed_schedule(db: AsyncSession, schedule_id: int = 1) -> CourseSchedule:
    """创建房间/课程/老师/排课/课时上课时间记录，返回排课对象。"""
    db.add(StudyRoom(id=1, name="Room 1", address="Address", status="open"))
    db.add(Course(id=1, room_id=1, name="高考冲刺班", category="training", status="active"))
    db.add(Teacher(id=1, name="张老师"))
    schedule = CourseSchedule(
        id=schedule_id,
        course_id=1,
        teacher_id=1,
        start_date=date(2026, 5, 10),
        time_slots='[{"weekday": 3, "time_slot": "10:00-12:00"}]',
        price=Decimal("20.00"),
        custom_price=Decimal("20.00"),
        schedule_type="custom",
    )
    db.add(schedule)
    db.add(CourseLesson(id=1, course_id=1, title="第1课"))
    db.add(
        LessonSchedule(
            schedule_id=schedule_id,
            lesson_id=1,
            lesson_date=date(2026, 5, 13),
            lesson_time_slot="10:00-12:00",
            sort_order=0,
        )
    )
    return schedule


def _make_booking(
    db: AsyncSession,
    booking_id: int,
    schedule_id: int | None,
    status: str,
) -> Booking:
    now = datetime(2026, 5, 1, 10, 0, 0)
    booking = Booking(
        id=booking_id,
        seat_id=None,
        user_id=str(USER_ID),
        room_id=1,
        date=date(2026, 5, 10),
        start_time=time(10, 0),
        end_time=time(12, 0),
        status=status,
        payment_status="paid",
        total_price=Decimal("20.00"),
        booking_type="course",
        course_id=1,
        schedule_type="custom",
        schedule_id=schedule_id,
        created_at=now,
        updated_at=now,
    )
    db.add(booking)
    return booking


async def _schedule_exists(db: AsyncSession, schedule_id: int) -> bool:
    row = (
        await db.execute(select(CourseSchedule).where(CourseSchedule.id == schedule_id))
    ).scalar_one_or_none()
    return row is not None


async def _lesson_count(db: AsyncSession, schedule_id: int) -> int:
    rows = (
        await db.execute(select(LessonSchedule).where(LessonSchedule.schedule_id == schedule_id))
    ).scalars().all()
    return len(rows)


@pytest.mark.asyncio
async def test_delete_schedule_without_bookings_removes_schedule_and_lessons(db_session):
    _seed_schedule(db_session, 1)
    await db_session.flush()

    result = await AdminCourseService().delete_schedule(db_session, 1)

    assert result == "ok"
    assert await _schedule_exists(db_session, 1) is False
    assert await _lesson_count(db_session, 1) == 0


@pytest.mark.asyncio
async def test_delete_schedule_with_only_cancelled_booking_succeeds_and_detaches(db_session):
    _seed_schedule(db_session, 1)
    _make_booking(db_session, 1, schedule_id=1, status="cancelled")
    await db_session.flush()

    result = await AdminCourseService().delete_schedule(db_session, 1)

    assert result == "ok"
    assert await _schedule_exists(db_session, 1) is False
    assert await _lesson_count(db_session, 1) == 0
    # 已取消订单保留，但排课外键引用被清空，避免 FK 约束报错
    booking = (await db_session.execute(select(Booking).where(Booking.id == 1))).scalar_one()
    assert booking.status == "cancelled"
    assert booking.schedule_id is None


@pytest.mark.asyncio
async def test_delete_schedule_with_active_booking_is_blocked(db_session):
    _seed_schedule(db_session, 1)
    _make_booking(db_session, 1, schedule_id=1, status="pending_start")
    await db_session.flush()

    result = await AdminCourseService().delete_schedule(db_session, 1)

    assert result == "has_active_bookings"
    assert await _schedule_exists(db_session, 1) is True
    assert await _lesson_count(db_session, 1) == 1
    booking = (await db_session.execute(select(Booking).where(Booking.id == 1))).scalar_one()
    assert booking.schedule_id == 1


@pytest.mark.asyncio
async def test_delete_schedule_mixed_cancelled_and_active_is_blocked(db_session):
    _seed_schedule(db_session, 1)
    _make_booking(db_session, 1, schedule_id=1, status="cancelled")
    _make_booking(db_session, 2, schedule_id=1, status="in_progress")
    await db_session.flush()

    result = await AdminCourseService().delete_schedule(db_session, 1)

    assert result == "has_active_bookings"
    assert await _schedule_exists(db_session, 1) is True
    assert await _lesson_count(db_session, 1) == 1


@pytest.mark.asyncio
async def test_delete_schedule_not_found(db_session):
    _seed_schedule(db_session, 1)
    await db_session.flush()

    result = await AdminCourseService().delete_schedule(db_session, 999)

    assert result == "not_found"
