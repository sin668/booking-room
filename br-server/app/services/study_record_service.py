import calendar
import uuid
from datetime import date, time
from decimal import Decimal

from sqlalchemy import and_, extract, func, select
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
    hours = _calculate_hours(booking.start_time, booking.end_time)
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
        # Fallback: no lesson_schedules, show as single record
        hours = _calculate_hours(booking.start_time, booking.end_time)
        items.append(StudyRecordItem(
            id=booking.id,
            record_type="course",
            status=status,
            course_name=course_name,
            date=booking.date,
            start_time=booking.start_time,
            end_time=booking.end_time,
            hours=hours,
            total_price=booking.total_price,
        ))
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

        hours = _calculate_hours(st, et)

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


async def get_monthly_summary(
    db: AsyncSession, user_id: uuid.UUID, month: date
) -> StudyRecordSummaryResponse:
    # Sync in-progress completions first
    await _sync_user_booking_completions(db, user_id)

    year = month.year
    month_num = month.month

    month_condition = and_(
        Booking.user_id == str(user_id),
        Booking.status.in_(["completed", "confirmed"]),  # Only studied records
        extract("year", Booking.date) == year,
        extract("month", Booking.date) == month_num,
    )

    result = await db.execute(select(Booking).where(month_condition))
    month_bookings = result.scalars().all()

    # Studied stats: need to expand course bookings into lessons
    monthly_hours = 0.0
    monthly_bookings = 0
    studied_dates: list[date] = []

    for b in month_bookings:
        if getattr(b, "booking_type", None) == "course" and b.lesson_ids:
            # Course booking: expand into individual lessons
            lesson_schedule_result = await db.execute(
                select(LessonSchedule).where(
                    LessonSchedule.schedule_id == b.course_id,
                    LessonSchedule.lesson_id.in_(b.lesson_ids),
                )
            )
            lesson_schedules = lesson_schedule_result.scalars().all()

            for ls in lesson_schedules:
                # Only count completed lessons (lesson_date < today)
                if _is_lesson_completed(ls.lesson_date):
                    monthly_bookings += 1
                    studied_dates.append(ls.lesson_date)
                    # Calculate hours from time slot
                    parts = ls.lesson_time_slot.split("-") if ls.lesson_time_slot else []
                    try:
                        st = time.fromisoformat(parts[0].strip()) if len(parts) >= 1 else b.start_time
                        et = time.fromisoformat(parts[1].strip()) if len(parts) >= 2 else b.end_time
                    except (ValueError, IndexError):
                        st = b.start_time
                        et = b.end_time
                    hours = _calculate_hours(st, et)
                    monthly_hours += hours
        else:
            # Seat booking: use booking's date/time directly
            hours = _calculate_hours(b.start_time, b.end_time)
            monthly_hours += hours
            monthly_bookings += 1
            studied_dates.append(b.date)

    # No upcoming bookings to track

    # Total hours (all-time studied: completed + confirmed, excluding future lessons)
    total_result = await db.execute(
        select(Booking).where(
            and_(
                Booking.user_id == str(user_id),
                Booking.status.in_(["completed", "confirmed"]),
            )
        )
    )
    all_bookings = total_result.scalars().all()
    total_hours = 0.0
    for b in all_bookings:
        if getattr(b, "booking_type", None) == "course" and b.lesson_ids:
            # Course booking: expand into lessons
            lesson_schedule_result = await db.execute(
                select(LessonSchedule).where(
                    LessonSchedule.schedule_id == b.course_id,
                    LessonSchedule.lesson_id.in_(b.lesson_ids),
                )
            )
            lesson_schedules = lesson_schedule_result.scalars().all()
            for ls in lesson_schedules:
                if _is_lesson_completed(ls.lesson_date):
                    parts = ls.lesson_time_slot.split("-") if ls.lesson_time_slot else []
                    try:
                        st = time.fromisoformat(parts[0].strip()) if len(parts) >= 1 else b.start_time
                        et = time.fromisoformat(parts[1].strip()) if len(parts) >= 2 else b.end_time
                    except (ValueError, IndexError):
                        st = b.start_time
                        et = b.end_time
                    total_hours += _calculate_hours(st, et)
        else:
            # Seat booking
            total_hours += _calculate_hours(b.start_time, b.end_time)

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
        monthly_hours=round(monthly_hours, 1),
        monthly_bookings=monthly_bookings,
        max_streak_days=max_streak,
        total_hours=round(total_hours, 1),
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
    offset = (page - 1) * page_size

    conditions = [
        Booking.user_id == str(user_id),
        Booking.status.in_(["completed", "confirmed"]),  # Only studied records
    ]
    if month is not None:
        conditions.append(extract("year", Booking.date) == month.year)
        conditions.append(extract("month", Booking.date) == month.month)

    # Status filter removed: only show studied (completed+confirmed) records

    where_clause = and_(*conditions)

    count_result = await db.execute(
        select(func.count()).select_from(Booking).where(where_clause)
    )
    total = count_result.scalar_one()

    # Sort: studied by date desc, upcoming by date asc
    order_clause = Booking.date.desc() if status != "upcoming" else Booking.date.asc()

    result = await db.execute(
        select(Booking)
        .where(where_clause)
        .order_by(order_clause, Booking.start_time.desc())
        .offset(offset)
        .limit(page_size)
    )
    bookings = result.scalars().all()

    # Build maps for seat/room/course lookups
    seat_ids = {b.seat_id for b in bookings if b.seat_id}
    room_ids = {b.room_id for b in bookings}
    course_ids = {
        b.course_id for b in bookings
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
        b for b in bookings
        if getattr(b, "booking_type", None) == "course" and b.lesson_ids
    ]
    if course_bookings:
        all_lesson_ids: set[int] = set()
        booking_lesson_ids: dict[int, list[int]] = {}
        for b in course_bookings:
            lids = list(b.lesson_ids) if b.lesson_ids else []
            booking_lesson_ids[b.id] = lids
            all_lesson_ids.update(lids)

        if all_lesson_ids:
            # Query lesson_schedules
            ls_result = await db.execute(
                select(LessonSchedule)
                .where(LessonSchedule.lesson_id.in_(all_lesson_ids))
                .order_by(LessonSchedule.sort_order)
            )
            all_ls = ls_result.scalars().all()

            # Build lesson_id -> lesson_schedule mapping
            ls_by_lesson_id: dict[int, LessonSchedule] = {}
            for ls in all_ls:
                ls_by_lesson_id[ls.lesson_id] = ls

            # Group by booking_id
            for bid, lids in booking_lesson_ids.items():
                booking_ls = [ls_by_lesson_id[lid] for lid in lids if lid in ls_by_lesson_id]
                booking_ls.sort(key=lambda x: (x.lesson_date, x.sort_order))
                if booking_ls:
                    lesson_schedule_map[bid] = booking_ls

            # Query lesson titles and durations
            lessons_result = await db.execute(
                select(CourseLesson).where(CourseLesson.id.in_(all_lesson_ids))
            )
            lesson_map = {l.id: l for l in lessons_result.scalars().all()}

    # Build record items
    items: list[StudyRecordItem] = []
    for b in bookings:
        record_status = "completed" if _is_studied(b.status) else "upcoming"
        booking_type = getattr(b, "booking_type", None) or "seat"

        if booking_type == "course":
            course_name = course_map.get(b.course_id) if b.course_id else None
            ls_list = lesson_schedule_map.get(b.id, [])
            course_items = _build_course_lesson_records(
                b, course_name, ls_list, lesson_map, record_status
            )
            items.extend(course_items)
        else:
            seat = seat_map.get(b.seat_id)
            room = room_map.get(b.room_id)
            if seat is None or room is None:
                continue
            items.append(_build_seat_record(b, seat, room, record_status))

    return StudyRecordListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
