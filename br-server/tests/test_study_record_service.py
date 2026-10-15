"""Unit tests for study_record_service."""

import uuid
from datetime import date, timedelta, time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.services.study_record_service import (
    _calculate_streak_days,
    get_monthly_summary,
    list_study_records,
)

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
async def seed_data(db_session: AsyncSession):
    room = StudyRoom(name="Test Room", address="123 Test St", status="open", min_price=10.00)
    db_session.add(room)
    await db_session.flush()

    seat = Seat(
        room_id=room.id, seat_number="A-01", zone="quiet", position="window",
        floor=3, price_per_hour=15.00, status="available", row=1, col=1,
    )
    db_session.add(seat)
    await db_session.flush()

    return {"room": room, "seat": seat}


async def _add_booking(db_session, seat, room, user_id, d, start, end, status="completed", price=45.00):
    b = Booking(
        seat_id=seat.id, user_id=str(user_id), room_id=room.id,
        date=d, start_time=start, end_time=end, status=status, total_price=price,
    )
    db_session.add(b)
    await db_session.flush()
    return b


class TestCalculateStreakDays:
    def test_empty_list(self):
        assert _calculate_streak_days([]) == 0

    def test_single_day(self):
        assert _calculate_streak_days([date(2026, 5, 1)]) == 1

    def test_consecutive_days(self):
        days = [date(2026, 5, 1), date(2026, 5, 2), date(2026, 5, 3)]
        assert _calculate_streak_days(days) == 3

    def test_gap_breaks_streak(self):
        days = [date(2026, 5, 1), date(2026, 5, 2), date(2026, 5, 5)]
        assert _calculate_streak_days(days) == 2

    def test_unsorted_input(self):
        days = [date(2026, 5, 3), date(2026, 5, 1), date(2026, 5, 2)]
        assert _calculate_streak_days(days) == 3

    def test_duplicate_dates(self):
        days = [date(2026, 5, 1), date(2026, 5, 1), date(2026, 5, 2)]
        assert _calculate_streak_days(days) == 2

    def test_weekend_gap(self):
        days = [date(2026, 5, 1), date(2026, 5, 4)]
        assert _calculate_streak_days(days) == 1

    def test_max_streak_in_middle(self):
        days = [date(2026, 5, 1), date(2026, 5, 3), date(2026, 5, 4), date(2026, 5, 5), date(2026, 5, 7)]
        assert _calculate_streak_days(days) == 3


class TestGetMonthlySummary:
    @pytest.mark.asyncio
    async def test_month_with_completed_bookings(self, db_session: AsyncSession, seed_data):
        seat, room = seed_data["seat"], seed_data["room"]
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 1), time(9, 0), time(12, 0))
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 2), time(9, 0), time(12, 0))

        result = await get_monthly_summary(db_session, USER_ID, date(2026, 5, 1))

        assert result.monthly_hours == 6.0
        assert result.monthly_bookings == 2
        assert result.max_streak_days == 2
        assert result.total_hours == 6.0
        assert len(result.calendar_mark) == 31
        studied_dates = [m.date for m in result.calendar_mark if m.studied]
        assert date(2026, 5, 1) in studied_dates
        assert date(2026, 5, 2) in studied_dates
        assert date(2026, 5, 3) not in studied_dates

    @pytest.mark.asyncio
    async def test_month_with_no_completed_bookings(self, db_session: AsyncSession, seed_data):
        result = await get_monthly_summary(db_session, USER_ID, date(2026, 6, 1))

        assert result.monthly_hours == 0.0
        assert result.monthly_bookings == 0
        assert result.max_streak_days == 0
        assert result.total_hours == 0.0
        assert len(result.calendar_mark) == 30
        assert all(not m.studied for m in result.calendar_mark)

    @pytest.mark.asyncio
    async def test_confirmed_bookings_counted_as_studied(self, db_session: AsyncSession, seed_data):
        """confirmed (in_progress) bookings are counted as 已学习, same as completed."""
        seat, room = seed_data["seat"], seed_data["room"]
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 1), time(9, 0), time(12, 0), status="in_progress")

        result = await get_monthly_summary(db_session, USER_ID, date(2026, 5, 1))

        assert result.monthly_bookings == 1
        assert result.monthly_hours == 3.0

    @pytest.mark.asyncio
    async def test_total_hours_across_months(self, db_session: AsyncSession, seed_data):
        seat, room = seed_data["seat"], seed_data["room"]
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 4, 15), time(9, 0), time(12, 0))
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 1), time(9, 0), time(12, 0))

        result = await get_monthly_summary(db_session, USER_ID, date(2026, 5, 1))

        assert result.monthly_hours == 3.0
        assert result.total_hours == 6.0

    @pytest.mark.asyncio
    async def test_streak_days_calculation(self, db_session: AsyncSession, seed_data):
        seat, room = seed_data["seat"], seed_data["room"]
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 1), time(9, 0), time(12, 0))
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 2), time(9, 0), time(12, 0))
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 3), time(9, 0), time(12, 0))
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 5), time(9, 0), time(12, 0))

        result = await get_monthly_summary(db_session, USER_ID, date(2026, 5, 1))

        assert result.max_streak_days == 3

    @pytest.mark.asyncio
    async def test_calendar_mark_upcoming_excluded_from_stats(self, db_session: AsyncSession, seed_data):
        """未开始订单在 calendar_mark 标记 upcoming=True，但不计入统计口径。"""
        seat, room = seed_data["seat"], seed_data["room"]
        future = date.today() + timedelta(days=3)
        month_first = date(future.year, future.month, 1)
        await _add_booking(db_session, seat, room, USER_ID, future, time(9, 0), time(12, 0), status="pending_start")

        result = await get_monthly_summary(db_session, USER_ID, month_first)

        mark = next(m for m in result.calendar_mark if m.date == future)
        assert mark.studied is False
        assert mark.upcoming is True
        assert result.monthly_bookings == 0
        assert result.monthly_hours == 0.0


class TestListStudyRecords:
    @pytest.mark.asyncio
    async def test_list_with_records(self, db_session: AsyncSession, seed_data):
        seat, room = seed_data["seat"], seed_data["room"]
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 1), time(9, 0), time(12, 0))
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 2), time(14, 0), time(17, 0))

        result = await list_study_records(db_session, USER_ID)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.items[0].date == date(2026, 5, 2)
        assert result.items[0].hours == 3.0
        assert result.items[0].room_name == "Test Room"
        assert result.items[0].seat_number == "A-01"

    @pytest.mark.asyncio
    async def test_list_empty(self, db_session: AsyncSession, seed_data):
        result = await list_study_records(db_session, USER_ID)

        assert result.total == 0
        assert result.items == []

    @pytest.mark.asyncio
    async def test_list_filter_by_month(self, db_session: AsyncSession, seed_data):
        seat, room = seed_data["seat"], seed_data["room"]
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 4, 15), time(9, 0), time(12, 0))
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 1), time(9, 0), time(12, 0))

        result = await list_study_records(db_session, USER_ID, month=date(2026, 5, 1))

        assert result.total == 1
        assert result.items[0].date == date(2026, 5, 1)

    @pytest.mark.asyncio
    async def test_list_filter_by_date(self, db_session: AsyncSession, seed_data):
        seat, room = seed_data["seat"], seed_data["room"]
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 1), time(9, 0), time(12, 0))
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 1), time(14, 0), time(17, 0))
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 2), time(9, 0), time(12, 0))

        result = await list_study_records(
            db_session, USER_ID, month=date(2026, 5, 1), record_date=date(2026, 5, 1)
        )

        assert result.total == 2
        assert all(item.date == date(2026, 5, 1) for item in result.items)

    @pytest.mark.asyncio
    async def test_list_pagination(self, db_session: AsyncSession, seed_data):
        seat, room = seed_data["seat"], seed_data["room"]
        for i in range(5):
            await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 1 + i), time(9, 0), time(12, 0))

        result = await list_study_records(db_session, USER_ID, page=1, page_size=3)

        assert result.total == 5
        assert len(result.items) == 3
        assert result.page == 1
        assert result.page_size == 3

        page2 = await list_study_records(db_session, USER_ID, page=2, page_size=3)
        assert len(page2.items) == 2

    @pytest.mark.asyncio
    async def test_list_excludes_non_studied(self, db_session: AsyncSession, seed_data):
        seat, room = seed_data["seat"], seed_data["room"]
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 1), time(9, 0), time(12, 0), status="completed")
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 2), time(9, 0), time(12, 0), status="in_progress")
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 3), time(9, 0), time(12, 0), status="pending_start")
        await _add_booking(db_session, seat, room, USER_ID, date(2026, 5, 4), time(9, 0), time(12, 0), status="cancelled")

        result = await list_study_records(db_session, USER_ID)

        # completed/in_progress -> studied; pending_start -> upcoming; cancelled excluded
        assert result.total == 3
        by_date = {item.date: item for item in result.items}
        assert by_date[date(2026, 5, 1)].status == "completed"
        assert by_date[date(2026, 5, 2)].status == "completed"
        assert by_date[date(2026, 5, 3)].status == "upcoming"

        completed_only = await list_study_records(db_session, USER_ID, status="completed")
        assert completed_only.total == 2

        upcoming_only = await list_study_records(db_session, USER_ID, status="upcoming")
        assert upcoming_only.total == 1
        assert upcoming_only.items[0].date == date(2026, 5, 3)

    @pytest.mark.asyncio
    async def test_list_upcoming_seat_status_and_date_filter(self, db_session: AsyncSession, seed_data):
        """待开始自习室订单进入未开始记录，并可按单日过滤。"""
        seat, room = seed_data["seat"], seed_data["room"]
        future = date.today() + timedelta(days=3)
        month_first = date(future.year, future.month, 1)
        await _add_booking(db_session, seat, room, USER_ID, future, time(9, 0), time(12, 0), status="pending_start")

        merged = await list_study_records(db_session, USER_ID, month=month_first)
        assert merged.total == 1
        assert merged.items[0].status == "upcoming"
        assert merged.items[0].date == future

        upcoming_only = await list_study_records(db_session, USER_ID, status="upcoming")
        assert upcoming_only.total == 1
        completed_only = await list_study_records(db_session, USER_ID, status="completed")
        assert completed_only.total == 0

        filtered = await list_study_records(
            db_session, USER_ID, month=month_first, record_date=future
        )
        assert filtered.total == 1
        assert filtered.items[0].status == "upcoming"
