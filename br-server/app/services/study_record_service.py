import calendar
import uuid
from datetime import date, time
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.lesson_schedule import LessonSchedule
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.schemas.study_record import (
    CalendarMark,
    StudyRecordItem,
    StudyRecordListResponse,
    StudyRecordSummaryResponse,
)
from app.services.booking_service import (
    _calculate_hours,
    _sync_user_booking_completions,
)

MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10

# Zone labels matching frontend SEAT_ZONE_LABELS
_ZONE_LABELS = {
    "quiet": "静音区",
    "keyboard": "键盘区",
    "vip": "VIP区",
}


def _calculate_streak_days(studied_dates: list[date]) -> int:
    if not studied_dates:
        return 0
    sorted_dates = sorted(set(studied_dates))
    max_streak = 1
    current_streak = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    return max_streak


def _is_studied(status: str) -> bool:
    """completed + confirmed(in_progress) both count as studied."""
    return status in ("completed", "confirmed")


def _is_lesson_completed(lesson_date: date) -> bool:
    """Check if a lesson date is in the past (completed)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    return lesson_date < today


def _build_seat_record(
    booking: Booking, seat: Seat | None, room: StudyRoom | None, status: str
) -> StudyRecordItem:
    """Build a study record item for a seat booking."""
    # 四舍五入保留两位小数，与 summary 统计口径一致
    hours = round(_calculate_hours(booking.start_time, booking.end_time), 2)
    seat_zone_label = _ZONE_LABELS.get(seat.zone, seat.zone) if seat and seat.zone else None
    return StudyRecordItem(
        id=booking.id,
        record_type="seat",
        status=status,
        room_name=room.name if room else None,
        seat_number=seat.seat_number if seat else None,
        seat_zone=seat_zone_label,
        date=booking.date,
        start_time=booking.start_time,
        end_time=booking.end_time,
        hours=hours,
        total_price=booking.total_price,
    )


def _build_course_lesson_records(
    booking: Booking,
    course_name: str | None,
    lesson_schedules: list[LessonSchedule],
    lesson_map: dict[int, CourseLesson],
    status: str,
) -> list[StudyRecordItem]:
    """Expand a course booking into individual lesson record items."""
    items: list[StudyRecordItem] = []
    lesson_count = len(lesson_schedules)
    if lesson_count == 0:
        # 无课时排课数据时不展示记录，与 summary 统计口径一致（summary 同样跳过该订单）
        return items

    # Calculate per-lesson price
    lesson_price = None
    if lesson_count > 0 and booking.total_price:
        try:
            lesson_price = Decimal(str(booking.total_price)) / lesson_count
        except Exception:
            lesson_price = None

    for ls in lesson_schedules:
        # Skip future lessons (not yet completed)
        if not _is_lesson_completed(ls.lesson_date):
            continue

        lesson = lesson_map.get(ls.lesson_id)
        lesson_title = lesson.title if lesson else None
        duration_minutes = lesson.duration_minutes if lesson else None

        # Parse time slot "08:00-10:00" -> start_time, end_time
        parts = ls.lesson_time_slot.split("-") if ls.lesson_time_slot else []
        try:
            st = time.fromisoformat(parts[0].strip()) if len(parts) >= 1 else booking.start_time
        except (ValueError, IndexError):
            st = booking.start_time
        try:
            et = time.fromisoformat(parts[1].strip()) if len(parts) >= 2 else booking.end_time
        except (ValueError, IndexError):
            et = booking.end_time

        # 课程时长按课程资料的 duration_minutes 统计（与下方记录展示的“XX分钟”同源），
        # 无 duration_minutes 时回退按排课时段计算；四舍五入保留两位小数
        if duration_minutes:
            hours = round(duration_minutes / 60, 2)
        else:
            hours = round(_calculate_hours(st, et), 2)

        items.append(StudyRecordItem(
            id=ls.id,
            record_type="course",
            status=status,
            course_name=course_name,
            lesson_title=lesson_title,
            lesson_date=ls.lesson_date,
            lesson_time_slot=ls.lesson_time_slot,
            duration_minutes=duration_minutes,
            lesson_price=lesson_price,
            date=ls.lesson_date,
            start_time=st,
            end_time=et,
            hours=hours,
            total_price=booking.total_price,
        ))

    return items


async def _collect_studied_items(
    db: AsyncSession, user_id: uuid.UUID
) -> list[StudyRecordItem]:
    """构建用户全部已学习记录条目（按日期倒序）。

    列表与统计共用同一口径：get_monthly_summary 直接基于这些条目聚合，
    保证上方统计 = 下方已学习记录时长之和。
    """
    # Fetch ALL studied bookings (no month filter at SQL level)
    # because course booking's Booking.date != lesson dates
    base_conditions = [
        Booking.user_id == str(user_id),
        Booking.status.in_(["completed", "confirmed"]),
    ]
    base_where = and_(*base_conditions)

    result = await db.execute(
        select(Booking)
        .where(base_where)
        .order_by(Booking.date.desc(), Booking.start_time.desc())
    )
    all_bookings = result.scalars().all()

    # Build maps for seat/room/course lookups
    seat_ids = {b.seat_id for b in all_bookings if b.seat_id}
    room_ids = {b.room_id for b in all_bookings}
    course_ids = {
        b.course_id for b in all_bookings
        if getattr(b, "booking_type", None) == "course" and b.course_id
    }

    seat_map: dict[int, Seat] = {}
    if seat_ids:
        seats_result = await db.execute(select(Seat).where(Seat.id.in_(seat_ids)))
        seat_map = {s.id: s for s in seats_result.scalars().all()}

    room_map: dict[int, StudyRoom] = {}
    if room_ids:
        rooms_result = await db.execute(select(StudyRoom).where(StudyRoom.id.in_(room_ids)))
        room_map = {r.id: r for r in rooms_result.scalars().all()}

    course_map: dict[int, str] = {}
    if course_ids:
        courses_result = await db.execute(select(Course).where(Course.id.in_(course_ids)))
        course_map = {c.id: c.name for c in courses_result.scalars().all()}

    # Batch query lesson data for course bookings
    lesson_schedule_map: dict[int, list[LessonSchedule]] = {}
    lesson_map: dict[int, CourseLesson] = {}

    course_bookings = [
        b for b in all_bookings
        if getattr(b, "booking_type", None) == "course" and b.lesson_ids
    ]
    if course_bookings:
        all_lesson_ids: set[int] = set()
        schedule_ids: set[int] = set()
        booking_lesson_ids: dict[int, list[int]] = {}
        for b in course_bookings:
            lids = list(b.lesson_ids) if b.lesson_ids else []
            booking_lesson_ids[b.id] = lids
            all_lesson_ids.update(lids)
            if b.schedule_id:
                schedule_ids.add(b.schedule_id)

        if all_lesson_ids and schedule_ids:
            # 限定订单自己的 schedule_id，与 summary 统计的查询口径一致，
            # 避免同一 lesson_id 跨排课混入其它订单/排课的记录
            ls_result = await db.execute(
                select(LessonSchedule)
                .where(
                    LessonSchedule.schedule_id.in_(schedule_ids),
                    LessonSchedule.lesson_id.in_(all_lesson_ids),
                )
                .order_by(LessonSchedule.sort_order)
            )
            all_ls = ls_result.scalars().all()

            # (schedule_id, lesson_id) 复合键，避免跨排课互相覆盖
            ls_by_key: dict[tuple[int, int], LessonSchedule] = {}
            for ls in all_ls:
                ls_by_key[(ls.schedule_id, ls.lesson_id)] = ls

            for b in course_bookings:
                if not b.schedule_id:
                    continue
                booking_ls = [
                    ls_by_key[(b.schedule_id, lid)]
                    for lid in booking_lesson_ids[b.id]
                    if (b.schedule_id, lid) in ls_by_key
                ]
                booking_ls.sort(key=lambda x: (x.lesson_date, x.sort_order))
                if booking_ls:
                    lesson_schedule_map[b.id] = booking_ls

            lessons_result = await db.execute(
                select(CourseLesson).where(CourseLesson.id.in_(all_lesson_ids))
            )
            lesson_map = {l.id: l for l in lessons_result.scalars().all()}

    # Build record items (all, before month filter)
    all_items: list[StudyRecordItem] = []
    for b in all_bookings:
        record_status = "completed" if _is_studied(b.status) else "upcoming"
        booking_type = getattr(b, "booking_type", None) or "seat"

        if booking_type == "course":
            course_name = course_map.get(b.course_id) if b.course_id else None
            ls_list = lesson_schedule_map.get(b.id, [])
            course_items = _build_course_lesson_records(
                b, course_name, ls_list, lesson_map, record_status
            )
            all_items.extend(course_items)
        else:
            seat = seat_map.get(b.seat_id)
            room = room_map.get(b.room_id)
            if seat is None or room is None:
                continue
            all_items.append(_build_seat_record(b, seat, room, record_status))

    # Sort all records by date desc, then start_time desc
    all_items.sort(key=lambda x: (x.date, x.start_time), reverse=True)

    return all_items


async def get_monthly_summary(
    db: AsyncSession, user_id: uuid.UUID, month: date
) -> StudyRecordSummaryResponse:
    """基于与记录列表完全相同的条目聚合统计，保证上方统计 = 下方记录时长之和。

    课程时长按 duration_minutes（课程资料元数据）口径，座位时长按预约起止时段口径，
    均在条目构建时四舍五入保留两位小数。
    """
    # Sync in-progress completions first
    await _sync_user_booking_completions(db, user_id)

    year = month.year
    month_num = month.month

    all_items = await _collect_studied_items(db, user_id)

    monthly_items = [
        item for item in all_items
        if item.date.year == year and item.date.month == month_num
    ]

    monthly_hours = round(sum(item.hours for item in monthly_items), 2)
    monthly_bookings = len(monthly_items)
    studied_dates = [item.date for item in monthly_items]
    total_hours = round(sum(item.hours for item in all_items), 2)

    _, days_in_month = calendar.monthrange(year, month_num)
    studied_set = set(studied_dates)
    calendar_mark = [
        CalendarMark(
            date=date(year, month_num, day),
            studied=(date(year, month_num, day) in studied_set),
            upcoming=False,  # No upcoming records shown
        )
        for day in range(1, days_in_month + 1)
    ]

    max_streak = _calculate_streak_days(studied_dates)

    return StudyRecordSummaryResponse(
        monthly_hours=monthly_hours,
        monthly_bookings=monthly_bookings,
        max_streak_days=max_streak,
        total_hours=total_hours,
        calendar_mark=calendar_mark,
        monthly_upcoming_hours=0.0,
        monthly_upcoming_count=0,
    )


async def list_study_records(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    month: date | None = None,
    status: str | None = None,
) -> StudyRecordListResponse:
    # Sync in-progress completions first
    await _sync_user_booking_completions(db, user_id)

    page_size = min(page_size, MAX_PAGE_SIZE)

    all_items = await _collect_studied_items(db, user_id)

    # Apply month filter in Python (based on record's actual date)
    if month is not None:
        all_items = [
            item for item in all_items
            if item.date.year == month.year and item.date.month == month.month
        ]

    total = len(all_items)
    offset = (page - 1) * page_size
    items = all_items[offset:offset + page_size]

    return StudyRecordListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
