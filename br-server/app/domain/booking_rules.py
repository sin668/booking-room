from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time


@dataclass(frozen=True)
class BookingCompletionInput:
    status: str
    payment_status: str
    booking_date: date
    start_time: time
    now: datetime


def calculate_booking_hours(start_time: time, end_time: time) -> float:
    start_seconds = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
    end_seconds = end_time.hour * 3600 + end_time.minute * 60 + end_time.second
    return (end_seconds - start_seconds) / 3600.0


def has_booking_started(
    *,
    booking_date: date,
    start_time: time,
    now: datetime,
) -> bool:
    return datetime.combine(booking_date, start_time) <= now


def can_cancel_paid_booking(
    *,
    status: str,
    payment_status: str,
    booking_date: date,
    start_time: time,
    now: datetime,
) -> bool:
    if status != "confirmed" or payment_status != "paid":
        return False
    return not has_booking_started(
        booking_date=booking_date,
        start_time=start_time,
        now=now,
    )


def should_mark_booking_completed(value: BookingCompletionInput) -> bool:
    return (
        value.status == "confirmed"
        and value.payment_status == "paid"
        and has_booking_started(
            booking_date=value.booking_date,
            start_time=value.start_time,
            now=value.now,
        )
    )
