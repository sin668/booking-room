"""订单状态定时任务（课程订单）回归测试。

背景：同一课程下固定班课排课与定制排课可能引用相同 lesson_id（不同日期），
旧代码按 course_id + lesson_ids 查询课时导致已开课的固定班课课时混入，
把未到开课日期的定制订单误转为 confirmed。本测试复刻该数据形态，
验证当前实现（schedule_id 精确查询 + 开课日期统一取第一课时日期）
不会再发生误转。
"""
from datetime import date, time
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.course import Course
from app.models.course_schedule import CourseSchedule
from app.models.lesson_schedule import LessonSchedule
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.services.order_status_scheduler import _process_course_booking

USER_ID = "11111111-1111-1111-1111-111111111111"


def _empty_stats() -> dict:
    """返回 6 键全 0 的 stats dict。

    §5.2 Q6 修正后，pending_start → in_progress 转移会显式自增 course_started，
    故测试须传真实 6 键 dict 而非 {}（否则 KeyError）。
    """
    return {"total_scanned": 0, "seat_started": 0, "seat_completed": 0,
            "course_started": 0, "course_highlight_updated": 0, "course_completed": 0}


def _make_base_data(db_session: AsyncSession) -> None:
    db_session.add(StudyRoom(id=1, name="测试自习室", address="测试地址", status="open"))
    db_session.add(Course(id=2, room_id=1, name="测试课程", category="training", status="active"))
    db_session.add(Teacher(id=1, name="测试老师"))
    # 排课1：同课程固定班课（已开课），课时日期已过 —— 污染源
    db_session.add(
        CourseSchedule(
            id=1, course_id=2, teacher_id=1, schedule_type="fixed",
            start_date=date(2026, 8, 19), price=Decimal("100"),
        )
    )
    for i, (lesson_id, lesson_date) in enumerate(
        [(122, date(2026, 8, 20)), (123, date(2026, 8, 22))]
    ):
        db_session.add(
            LessonSchedule(
                schedule_id=1, lesson_id=lesson_id, lesson_date=lesson_date,
                lesson_time_slot="16:00-18:00", sort_order=i,
            )
        )
    # 排课36：定制订单专属排课（未开课），复用相同 lesson_id
    db_session.add(
        CourseSchedule(
            id=36, course_id=2, teacher_id=1, schedule_type="custom",
            start_date=date(2026, 9, 5), price=Decimal("20"),
        )
    )
    for i, (lesson_id, lesson_date) in enumerate(
        [(122, date(2026, 9, 5)), (123, date(2026, 9, 12))]
    ):
        db_session.add(
            LessonSchedule(
                schedule_id=36, lesson_id=lesson_id, lesson_date=lesson_date,
                lesson_time_slot="16:00-18:00", sort_order=i,
            )
        )


def _make_custom_booking(
    db_session: AsyncSession, schedule_id: int | None, booking_date: date | None = None
) -> Booking:
    booking = Booking(
        user_id=USER_ID, room_id=1,
        date=booking_date or date(2026, 9, 5), start_time=time(16, 0), end_time=time(18, 0),
        status="pending", payment_status="paid", total_price=Decimal("20"),
        booking_type="course", course_id=2, schedule_type="custom",
        schedule_id=schedule_id, lesson_ids=[122, 123],
    )
    db_session.add(booking)
    return booking


@pytest.mark.asyncio
async def test_course_custom_booking_not_converted_before_start_date(db_session: AsyncSession):
    """定制订单未到开课日期时不得被误转 confirmed（订单 98 事故回归）。

    同课程固定班课排课含相同 lesson_id 且已开课，订单通过 schedule_id
    精确命中自己的定制排课课时（9-05/9-12），今天（9-01）< 开课日期，保持 pending。
    """
    _make_base_data(db_session)
    booking = _make_custom_booking(db_session, schedule_id=36)
    await db_session.flush()

    await _process_course_booking(db_session, booking, date(2026, 9, 1), _empty_stats())

    assert booking.status == "pending"
    assert booking.highlighted_lesson_id is None


@pytest.mark.asyncio
async def test_course_custom_booking_fallback_keeps_pending_via_schedule_type_filter(
    db_session: AsyncSession,
):
    """旧订单无 schedule_id 时，回退查询按 schedule_type 过滤，不混入固定班课课时。"""
    _make_base_data(db_session)
    booking = _make_custom_booking(db_session, schedule_id=None)
    await db_session.flush()

    await _process_course_booking(db_session, booking, date(2026, 9, 1), _empty_stats())

    assert booking.status == "pending"
    assert booking.highlighted_lesson_id is None


@pytest.mark.asyncio
async def test_course_custom_booking_converts_on_start_date(db_session: AsyncSession):
    """到达开课日期后正常转为 confirmed 并高亮第一课时。"""
    _make_base_data(db_session)
    booking = _make_custom_booking(db_session, schedule_id=36)
    await db_session.flush()

    stats = _empty_stats()
    await _process_course_booking(db_session, booking, date(2026, 9, 5), stats)

    assert booking.status == "confirmed"
    assert booking.highlighted_lesson_id == 122
    assert stats["course_started"] == 1


@pytest.mark.asyncio
async def test_course_custom_booking_start_date_follows_first_lesson_not_booking_date(
    db_session: AsyncSession,
):
    """开课日期口径：定制订单与固定班课一致，以第一课时日期为准而非 bookings.date。

    bookings.date 早于第一课时日期时，未到首课时日期保持 pending，
    到达首课时日期才转 confirmed。
    """
    _make_base_data(db_session)
    booking = _make_custom_booking(db_session, schedule_id=36, booking_date=date(2026, 9, 1))
    await db_session.flush()

    await _process_course_booking(db_session, booking, date(2026, 9, 4), _empty_stats())
    assert booking.status == "pending"

    await _process_course_booking(db_session, booking, date(2026, 9, 5), _empty_stats())
    assert booking.status == "confirmed"
    assert booking.highlighted_lesson_id == 122
