"""学习记录页统计与记录列表一致性测试。

覆盖修复点：
1. 记录列表按订单自己的 schedule_id 关联课时，杜绝同一 lesson_id 跨排课混入
2. 无课时排课数据的课程订单在列表与统计两侧口径一致（均不计入）
3. 课程时长按 duration_minutes（课程资料元数据）统计，与下方记录展示的“XX分钟”同源
4. 统计学习时长与单条记录时长按四舍五入保留两位小数，上方统计 = 下方记录之和
"""

import uuid
from datetime import date, time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.course_schedule import CourseSchedule
from app.models.lesson_schedule import LessonSchedule
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.services.study_record_service import (
    get_monthly_summary,
    list_study_records,
)

USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
MONTH = date(2026, 8, 1)


@pytest.fixture
async def seed_study_data(db_session: AsyncSession):
    """座位订单 + 课程订单（含跨排课干扰数据）。"""
    room = StudyRoom(
        name="一致性测试室", address="地址", status="open",
        room_type="training", min_price=10.0,
    )
    db_session.add(room)
    await db_session.flush()

    seat = Seat(
        room_id=room.id, seat_number="A-01", zone="quiet", position="window",
        floor=1, price_per_hour=15.0, status="available", row=1, col=1,
    )
    db_session.add(seat)

    course = Course(room_id=room.id, name="一致性课程", category="skills", status="active")
    db_session.add(course)
    await db_session.flush()

    # duration_minutes=85（下方展示“85分钟”），排课时段故意设为 90 分钟，
    # 验证时长统计按 duration_minutes（85/60=1.42h）而非 time_slot（1.5h）
    lesson = CourseLesson(course_id=course.id, title="第1课", duration_minutes=85, sort_order=1)
    db_session.add(lesson)
    await db_session.flush()

    # 订单自己的排课 S1：课时在 2026-08-10 10:00-11:30（1.5h，已完成）
    schedule_own = CourseSchedule(
        course_id=course.id, start_date=date(2026, 8, 10), end_date=date(2026, 8, 31),
        time_slots='[{"weekday": 1, "time_slot": "10:00-11:30"}]',
        price=100.0, schedule_type="fixed", schedule_status="completed",
    )
    # 干扰排课 S2：同一 lesson_id，日期在未来、时段 2h（旧实现会误取该条）
    schedule_other = CourseSchedule(
        course_id=course.id, start_date=date(2026, 9, 20), end_date=date(2026, 9, 30),
        price=120.0, schedule_type="fixed", schedule_status="in_progress",
    )
    db_session.add_all([schedule_own, schedule_other])
    await db_session.flush()

    db_session.add_all([
        LessonSchedule(
            schedule_id=schedule_own.id, lesson_id=lesson.id,
            lesson_date=date(2026, 8, 10), lesson_time_slot="10:00-11:30", sort_order=1,
        ),
        LessonSchedule(
            schedule_id=schedule_other.id, lesson_id=lesson.id,
            lesson_date=date(2026, 9, 20), lesson_time_slot="10:00-12:00", sort_order=1,
        ),
    ])

    # 座位订单：2026-08-05 09:00-09:50（50/60 = 0.8333h，用于两位小数口径）
    seat_booking = Booking(
        seat_id=seat.id, user_id=str(USER_ID), room_id=room.id,
        date=date(2026, 8, 5), start_time=time(9, 0), end_time=time(9, 50),
        status="completed", total_price=12.5, booking_type="seat",
    )
    # 课程订单：关联 S1 + lesson
    course_booking = Booking(
        user_id=str(USER_ID), room_id=room.id, course_id=course.id,
        date=date(2026, 8, 10), start_time=time(10, 0), end_time=time(11, 30),
        status="completed", total_price=100.0, booking_type="course",
        lesson_ids=[lesson.id], schedule_id=schedule_own.id, schedule_type="fixed",
    )
    db_session.add_all([seat_booking, course_booking])
    await db_session.flush()

    return {
        "course": course,
        "lesson": lesson,
        "schedule_own": schedule_own,
        "seat_booking": seat_booking,
        "course_booking": course_booking,
    }


class TestSummaryMatchesRecords:
    @pytest.mark.asyncio
    async def test_summary_equals_sum_of_records(self, db_session: AsyncSession, seed_study_data):
        """上方统计 = 下方已学习记录时长之和（两位小数口径）。"""
        summary = await get_monthly_summary(db_session, USER_ID, MONTH)
        records = await list_study_records(
            db_session, USER_ID, page=1, page_size=50, month=MONTH
        )
        record_sum = round(sum(item.hours for item in records.items), 2)
        assert records.total == 2
        assert summary.monthly_hours == record_sum
        # 0.83(座位 50 分钟) + 1.42(课程 duration_minutes=85) = 2.25
        assert summary.monthly_hours == 2.25

    @pytest.mark.asyncio
    async def test_records_use_booking_own_schedule(self, db_session: AsyncSession, seed_study_data):
        """记录列表按订单自己的排课关联课时，不混入同 lesson_id 的其它排课。"""
        records = await list_study_records(
            db_session, USER_ID, page=1, page_size=50, month=MONTH
        )
        course_items = [i for i in records.items if i.record_type == "course"]
        assert len(course_items) == 1
        item = course_items[0]
        assert item.lesson_date == date(2026, 8, 10)
        assert item.lesson_time_slot == "10:00-11:30"
        # 时长按 duration_minutes=85 统计，不按 time_slot（90 分钟）
        assert item.hours == 1.42

    @pytest.mark.asyncio
    async def test_hours_rounded_to_two_decimals(self, db_session: AsyncSession, seed_study_data):
        """单条记录与统计时长均四舍五入保留两位小数。"""
        records = await list_study_records(
            db_session, USER_ID, page=1, page_size=50, month=MONTH
        )
        seat_item = next(i for i in records.items if i.record_type == "seat")
        assert seat_item.hours == 0.83

        summary = await get_monthly_summary(db_session, USER_ID, MONTH)
        assert summary.total_hours == 2.25

    @pytest.mark.asyncio
    async def test_course_booking_without_lesson_schedules_hidden(
        self, db_session: AsyncSession, seed_study_data
    ):
        """无课时排课数据的课程订单两侧口径一致：列表不展示、统计不计入。"""
        orphan = Booking(
            user_id=str(USER_ID), room_id=seed_study_data["course"].room_id,
            course_id=seed_study_data["course"].id,
            date=date(2026, 8, 15), start_time=time(14, 0), end_time=time(16, 0),
            status="completed", total_price=80.0, booking_type="course",
            lesson_ids=[seed_study_data["lesson"].id], schedule_id=None,
        )
        db_session.add(orphan)
        await db_session.flush()

        records = await list_study_records(
            db_session, USER_ID, page=1, page_size=50, month=MONTH
        )
        summary = await get_monthly_summary(db_session, USER_ID, MONTH)
        assert records.total == 2
        record_sum = round(sum(item.hours for item in records.items), 2)
        assert summary.monthly_hours == record_sum
