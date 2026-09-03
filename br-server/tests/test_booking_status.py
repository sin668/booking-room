from datetime import date, datetime, time

from app.domain.booking_status import (
    BookingStatus,
    CourseTransition,
    PaymentStatus,
    SeatTransition,
    build_status_filter_conditions,
    is_cancellable,
    is_full_refund_cancellation,
    is_payable,
    is_unpaid_cancellable,
    resolve_course_status,
    resolve_course_transition,
    resolve_seat_status,
    resolve_seat_transition,
)
from app.models.booking import Booking


# resolve_seat_status: now < start -> PENDING_START; now >= start -> IN_PROGRESS; None -> IN_PROGRESS
def test_seat_before_start():
    assert resolve_seat_status(now=datetime(2026, 9, 3, 9, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0)) == BookingStatus.PENDING_START
def test_seat_at_start():
    assert resolve_seat_status(now=datetime(2026, 9, 3, 10, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0)) == BookingStatus.IN_PROGRESS
def test_seat_after_start():
    assert resolve_seat_status(now=datetime(2026, 9, 3, 11, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0)) == BookingStatus.IN_PROGRESS
def test_seat_none_date_fallback_in_progress():
    assert resolve_seat_status(now=datetime(2026, 9, 3, 9, 0), booking_date=None, start_time=time(10, 0)) == BookingStatus.IN_PROGRESS
def test_seat_string_start_time():
    assert resolve_seat_status(now=datetime(2026, 9, 3, 9, 0), booking_date=date(2026, 9, 3), start_time="10:00") == BookingStatus.PENDING_START


# resolve_course_status: first <= today -> IN_PROGRESS; first > today -> PENDING_START; None -> IN_PROGRESS
def test_course_first_before_today():
    assert resolve_course_status(today=date(2026, 9, 3), first_lesson_date=date(2026, 9, 1)) == BookingStatus.IN_PROGRESS
def test_course_first_equals_today():
    assert resolve_course_status(today=date(2026, 9, 3), first_lesson_date=date(2026, 9, 3)) == BookingStatus.IN_PROGRESS
def test_course_first_after_today():
    assert resolve_course_status(today=date(2026, 9, 3), first_lesson_date=date(2026, 9, 10)) == BookingStatus.PENDING_START
def test_course_none_first_fallback_in_progress():
    assert resolve_course_status(today=date(2026, 9, 3), first_lesson_date=None) == BookingStatus.IN_PROGRESS


# resolve_seat_transition（order_status_scheduler.py:89-101）
def test_seat_transition_start():
    assert resolve_seat_transition(status=BookingStatus.PENDING_START, now=datetime(2026, 9, 3, 10, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0), end_time=time(12, 0)) == SeatTransition(BookingStatus.IN_PROGRESS, "seat_started")
def test_seat_transition_complete():
    assert resolve_seat_transition(status=BookingStatus.IN_PROGRESS, now=datetime(2026, 9, 3, 12, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0), end_time=time(12, 0)) == SeatTransition(BookingStatus.COMPLETED, "seat_completed")
def test_seat_transition_pending_before_start_noop():
    assert resolve_seat_transition(status=BookingStatus.PENDING_START, now=datetime(2026, 9, 3, 9, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0), end_time=time(12, 0)) == SeatTransition(None, None)
def test_seat_transition_in_progress_before_end_noop():
    assert resolve_seat_transition(status=BookingStatus.IN_PROGRESS, now=datetime(2026, 9, 3, 11, 0), booking_date=date(2026, 9, 3), start_time=time(10, 0), end_time=time(12, 0)) == SeatTransition(None, None)


# resolve_course_transition（order_status_scheduler.py:164-184；完成为 today > last 严格大于）
def test_course_transition_start():
    assert resolve_course_transition(status=BookingStatus.PENDING_START, today=date(2026, 9, 3), first_lesson_date=date(2026, 9, 3), last_lesson_date=date(2026, 9, 10)) == CourseTransition(BookingStatus.IN_PROGRESS, "course_started", False)
def test_course_transition_complete_strictly_greater():
    assert resolve_course_transition(status=BookingStatus.IN_PROGRESS, today=date(2026, 9, 11), first_lesson_date=date(2026, 9, 1), last_lesson_date=date(2026, 9, 10)) == CourseTransition(BookingStatus.COMPLETED, "course_completed", False)
def test_course_transition_today_equals_last_not_completed():
    assert resolve_course_transition(status=BookingStatus.IN_PROGRESS, today=date(2026, 9, 10), first_lesson_date=date(2026, 9, 1), last_lesson_date=date(2026, 9, 10)) == CourseTransition(None, None, True)
def test_course_transition_pending_before_first_noop():
    assert resolve_course_transition(status=BookingStatus.PENDING_START, today=date(2026, 9, 2), first_lesson_date=date(2026, 9, 3), last_lesson_date=date(2026, 9, 10)) == CourseTransition(None, None, False)


# is_cancellable（booking_service.py:654-658 的状态+支付前置部分）
def test_cancellable_in_progress_paid():
    assert is_cancellable(status=BookingStatus.IN_PROGRESS, payment_status=PaymentStatus.PAID) is True
def test_cancellable_pending_start_paid():
    assert is_cancellable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PAID) is True
def test_cancellable_completed_paid_false():
    assert is_cancellable(status=BookingStatus.COMPLETED, payment_status=PaymentStatus.PAID) is False
def test_cancellable_in_progress_unpaid_false():
    assert is_cancellable(status=BookingStatus.IN_PROGRESS, payment_status=PaymentStatus.PENDING) is False


# is_unpaid_cancellable / is_payable：均为「双 pending」（status=PENDING_START 且 payment=PENDING）
def test_unpaid_cancellable_double_pending():
    assert is_unpaid_cancellable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PENDING) is True
def test_unpaid_cancellable_paid_false():
    assert is_unpaid_cancellable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PAID) is False
def test_payable_double_pending():
    assert is_payable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PENDING) is True
def test_payable_paid_false():
    assert is_payable(status=BookingStatus.PENDING_START, payment_status=PaymentStatus.PAID) is False


# is_full_refund_cancellation（booking_service.py:1158-1161）
def test_full_refund_course_pending_start():
    assert is_full_refund_cancellation(booking_type="course", status=BookingStatus.PENDING_START) is True
def test_full_refund_course_pending_confirm():
    assert is_full_refund_cancellation(booking_type="course", status=BookingStatus.PENDING_CONFIRM) is True
def test_full_refund_seat_false():
    assert is_full_refund_cancellation(booking_type="seat", status=BookingStatus.PENDING_START) is False
def test_full_refund_course_in_progress_false():
    assert is_full_refund_cancellation(booking_type="course", status=BookingStatus.IN_PROGRESS) is False


# build_status_filter_conditions：派生口径分支形状（§2.6；行为等价由红名单恒等 + 既有 API 测试保证）
def test_filter_none_empty():
    assert build_status_filter_conditions(Booking.status, Booking.payment_status, None) == []
def test_filter_in_progress_two_conditions():
    assert len(build_status_filter_conditions(Booking.status, Booking.payment_status, "in_progress")) == 2
def test_filter_pending_start_two_conditions():
    assert len(build_status_filter_conditions(Booking.status, Booking.payment_status, "pending_start")) == 2
def test_filter_other_one_condition():
    assert len(build_status_filter_conditions(Booking.status, Booking.payment_status, "completed")) == 1
