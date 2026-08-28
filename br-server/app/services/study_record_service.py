import calendar
import uuid
from datetime import date, time
from decimal import Decimal

from sqlalchemy import and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.course import Course
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.schemas.study_record import (
    CalendarMark,
    StudyRecordItem,
    StudyRecordListResponse,
    StudyRecordSummaryResponse,
)
from app.services.booking_service import _calculate_hours

MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10


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


def _build_seat_record(booking: Booking, seat: Seat | None, room: StudyRoom | None, status: str) -> StudyRecordItem:
    """Build a study record item for a seat booking."""
    hours = _calculate_hours(booking.start_time, booking.end_time)
    return StudyRecordItem(
        id=booking.id,
        record_type="seat",
        status=status,
        room_name=room.name if room else None,
        seat_number=seat.seat_number if seat else None,
        date=booking.date,
        start_time=booking.start_time,
        end_time=booking.end_time,
        hours=hours,
        total_price=booking.total_price,
    )


def _build_course_record(booking: Booking, course_name: str | None, status: str) -> StudyRecordItem:
    """Build a study record item for a course booking."""
    hours = _calculate_hours(booking.start_time, booking.end_time)
    return StudyRecordItem(
        id=booking.id,
        record_type="course",
        status=status,
        course_name=course_name,
        date=booking.date,
        start_time=booking.start_time,
        end_time=booking.end_time,
        hours=hours,
        total_price=booking.total_price,
    )


async def get_monthly_summary(
    db: AsyncSession, user_id: uuid.UUID, month: date
) -> StudyRecordSummaryResponse:
    year = month.year
    month_num = month.month

    month_condition = and_(
        Booking.user_id == str(user_id),
        Booking.status != "cancelled",
        extract("year", Booking.date) == year,
        extract("month", Booking.date) == month_num,
    )

    result = await db.execute(
        select(Booking).where(month_condition)
    )
    month_bookings = result.scalars().all()

    # Split into completed and upcoming
    completed_bookings = [b for b in month_bookings if b.status == "completed"]
    upcoming_bookings = [b for b in month_bookings if b.status != "completed"]

    seat_ids = {b.seat_id for b in month_bookings if b.seat_id}
    room_ids = {b.room_id for b in month_bookings}

    seat_map = {}
    if seat_ids:
        seats_result = await db.execute(select(Seat).where(Seat.id.in_(seat_ids)))
        seat_map = {s.id: s for s in seats_result.scalars().all()}

    room_map = {}
    if room_ids:
        rooms_result = await db.execute(select(StudyRoom).where(StudyRoom.id.in_(room_ids)))
        room_map = {r.id: r for r in rooms_result.scalars().all()}

    # Completed stats
    monthly_hours = 0.0
    monthly_bookings = len(completed_bookings)
    studied_dates = []
    for b in completed_bookings:
        hours = _calculate_hours(b.start_time, b.end_time)
        monthly_hours += hours
        studied_dates.append(b.date)

    # Upcoming stats
    monthly_upcoming_hours = 0.0
    monthly_upcoming_count = len(upcoming_bookings)
    upcoming_dates = []
    for b in upcoming_bookings:
        hours = _calculate_hours(b.start_time, b.end_time)
        monthly_upcoming_hours += hours
        upcoming_dates.append(b.date)

    # Total hours (all-time completed only)
    total_result = await db.execute(
        select(Booking.start_time, Booking.end_time).where(
            and_(
                Booking.user_id == str(user_id),
                Booking.status == "completed",
            )
        )
    )
    total_rows = total_result.all()
    total_hours = sum(_calculate_hours(r[0], r[1]) for r in total_rows)

    _, days_in_month = calendar.monthrange(year, month_num)
    studied_set = set(studied_dates)
    upcoming_set = set(upcoming_dates)
    calendar_mark = [
        CalendarMark(
            date=date(year, month_num, day),
            studied=(date(year, month_num, day) in studied_set),
            upcoming=(date(year, month_num, day) in upcoming_set),
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
        monthly_upcoming_hours=round(monthly_upcoming_hours, 1),
        monthly_upcoming_count=monthly_upcoming_count,
    )


async def list_study_records(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    month: date | None = None,
    status: str | None = None,
) -> StudyRecordListResponse:
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    conditions = [
        Booking.user_id == str(user_id),
        Booking.status != "cancelled",
    ]
    if month is not None:
        conditions.append(extract("year", Booking.date) == month.year)
        conditions.append(extract("month", Booking.date) == month.month)

    if status == "completed":
        conditions.append(Booking.status == "completed")
    elif status == "upcoming":
        conditions.append(Booking.status != "completed")

    where_clause = and_(*conditions)

    count_result = await db.execute(
        select(func.count()).select_from(Booking).where(where_clause)
    )
    total = count_result.scalar_one()

    # Sort: completed by date desc, upcoming by date asc
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
    course_ids = {b.course_id for b in bookings if getattr(b, "booking_type", None) == "course" and b.course_id}

    seat_map = {}
    if seat_ids:
        seats_result = await db.execute(select(Seat).where(Seat.id.in_(seat_ids)))
        seat_map = {s.id: s for s in seats_result.scalars().all()}

    room_map = {}
    if room_ids:
        rooms_result = await db.execute(select(StudyRoom).where(StudyRoom.id.in_(room_ids)))
        room_map = {r.id: r for r in rooms_result.scalars().all()}

    course_map = {}
    if course_ids:
        courses_result = await db.execute(select(Course).where(Course.id.in_(course_ids)))
        course_map = {c.id: c.name for c in courses_result.scalars().all()}

    items = []
    for b in bookings:
        record_status = "completed" if b.status == "completed" else "upcoming"
        booking_type = getattr(b, "booking_type", None) or "seat"

        if booking_type == "course":
            course_name = course_map.get(b.course_id) if b.course_id else None
            items.append(_build_course_record(b, course_name, record_status))
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
