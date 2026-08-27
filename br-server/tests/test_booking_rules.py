from datetime import date, datetime, time

from app.domain.booking_rules import (
    BookingCompletionInput,
    calculate_booking_hours,
    can_cancel_paid_booking,
    has_booking_started,
    should_mark_booking_completed,
)


def test_calculate_booking_hours_returns_fractional_hours():
    result = calculate_booking_hours(time(8, 30), time(11, 0))

    assert result == 2.5


def test_has_booking_started_uses_booking_date_and_start_time():
    result = has_booking_started(
        booking_date=date(2026, 5, 30),
        start_time=time(9, 0),
        now=datetime(2026, 5, 30, 9, 0),
    )

    assert result is True


def test_can_cancel_paid_booking_requires_confirmed_paid_and_not_started():
    result = can_cancel_paid_booking(
        status="confirmed",
        payment_status="paid",
        booking_date=date(2026, 5, 30),
        start_time=time(10, 0),
        now=datetime(2026, 5, 30, 9, 0),
    )

    assert result is True


def test_can_cancel_paid_booking_rejects_started_booking():
    result = can_cancel_paid_booking(
        status="confirmed",
        payment_status="paid",
        booking_date=date(2026, 5, 30),
        start_time=time(9, 0),
        now=datetime(2026, 5, 30, 9, 0),
    )

    assert result is False


def test_should_mark_booking_completed_when_now_at_or_after_end_time():
    result = should_mark_booking_completed(
        BookingCompletionInput(
            status="confirmed",
            payment_status="paid",
            booking_date=date(2026, 5, 30),
            start_time=time(9, 0),
            end_time=time(11, 0),
            now=datetime(2026, 5, 30, 11, 0),
        )
    )

    assert result is True


def test_should_not_mark_booking_completed_when_now_between_start_and_end_time():
    result = should_mark_booking_completed(
        BookingCompletionInput(
            status="confirmed",
            payment_status="paid",
            booking_date=date(2026, 5, 30),
            start_time=time(9, 0),
            end_time=time(11, 0),
            now=datetime(2026, 5, 30, 10, 0),
        )
    )

    assert result is False


def test_should_not_mark_booking_completed_before_start_time():
    result = should_mark_booking_completed(
        BookingCompletionInput(
            status="confirmed",
            payment_status="paid",
            booking_date=date(2026, 5, 30),
            start_time=time(9, 0),
            end_time=time(11, 0),
            now=datetime(2026, 5, 30, 8, 59),
        )
    )

    assert result is False
