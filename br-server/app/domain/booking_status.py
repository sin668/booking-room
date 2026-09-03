"""订单状态词表 —— 全仓唯一权威定义处（Design Doc §2）。

契约：本模块所有纯函数的 now/today 参数一律为 naive 的 Asia/Shanghai 本地时间；
本模块不依赖 models / schemas / services 三层，也不做 tzinfo 处理。
Phase 2 期间枚举成员值仍为旧字面量，Phase 4 Task 4.1 统一翻转。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class BookingStatus(str, Enum):
    PENDING_CONFIRM = "pending_confirm"
    PENDING_START = "pending"      # Phase 4 翻转为 "pending_start"
    IN_PROGRESS = "confirmed"      # Phase 4 翻转为 "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class PaymentMethod(str, Enum):
    BALANCE = "balance"
    WECHAT = "wechat"


@dataclass(frozen=True, slots=True)
class SeatTransition:
    new_status: BookingStatus | None
    stat_key: str | None


@dataclass(frozen=True, slots=True)
class CourseTransition:
    new_status: BookingStatus | None
    stat_key: str | None
    highlight_only: bool


def _parse_time(value):
    if isinstance(value, str):
        return datetime.strptime(value, "%H:%M").time()
    return value


def resolve_seat_status(*, now: datetime, booking_date: date | None, start_time) -> BookingStatus:
    """booking_service.py:286-288 / :762-764、booking_payment_service.py:292-299。"""
    if booking_date is None or start_time is None:
        return BookingStatus.IN_PROGRESS
    booking_start = datetime.combine(booking_date, _parse_time(start_time))
    return BookingStatus.IN_PROGRESS if now >= booking_start else BookingStatus.PENDING_START


def resolve_course_status(*, today: date, first_lesson_date: date | None) -> BookingStatus:
    """booking_payment_service.py:288-290、course_booking_service.py:433、booking_service.py:1244。"""
    if first_lesson_date is None:
        return BookingStatus.IN_PROGRESS
    return BookingStatus.IN_PROGRESS if first_lesson_date <= today else BookingStatus.PENDING_START


def resolve_seat_transition(*, status, now, booking_date, start_time, end_time) -> SeatTransition:
    """order_status_scheduler.py:89-101。"""
    if status == BookingStatus.PENDING_START:
        if now >= datetime.combine(booking_date, _parse_time(start_time)):
            return SeatTransition(BookingStatus.IN_PROGRESS, "seat_started")
    elif status == BookingStatus.IN_PROGRESS:
        if now >= datetime.combine(booking_date, _parse_time(end_time)):
            return SeatTransition(BookingStatus.COMPLETED, "seat_completed")
    return SeatTransition(None, None)


def resolve_course_transition(*, status, today, first_lesson_date, last_lesson_date) -> CourseTransition:
    """order_status_scheduler.py:164-184。完成条件 today > last_lesson_date 为严格大于。"""
    if status == BookingStatus.PENDING_START:
        if first_lesson_date is not None and today >= first_lesson_date:
            return CourseTransition(BookingStatus.IN_PROGRESS, "course_started", False)
    elif status == BookingStatus.IN_PROGRESS:
        if last_lesson_date is not None and today > last_lesson_date:
            return CourseTransition(BookingStatus.COMPLETED, "course_completed", False)
        return CourseTransition(None, None, True)
    return CourseTransition(None, None, False)


def is_cancellable(*, status, payment_status) -> bool:
    """booking_service.py:654-658 的状态+支付前置部分（不含时间判定）。"""
    return (
        status in (BookingStatus.IN_PROGRESS, BookingStatus.PENDING_START)
        and payment_status == PaymentStatus.PAID
    )


def is_unpaid_cancellable(*, status, payment_status) -> bool:
    """booking_service.py:644 的「双 pending」：未支付待开始可直接取消（无退款逻辑）。"""
    return status == BookingStatus.PENDING_START and payment_status == PaymentStatus.PENDING


def is_payable(*, status, payment_status) -> bool:
    """booking_service.py:744 的「双 pending」：仅待开始且待支付可发起支付。"""
    return status == BookingStatus.PENDING_START and payment_status == PaymentStatus.PENDING


def is_full_refund_cancellation(*, booking_type, status) -> bool:
    """booking_service.py:1158-1161 的 is_course_pending_start。"""
    return booking_type == "course" and status in (
        BookingStatus.PENDING_START,
        BookingStatus.PENDING_CONFIRM,
    )


def build_status_filter_conditions(status_column, payment_status_column, status: str | None) -> list:
    """C 端 list_bookings 派生口径（§2.6，Q5 行为零变更）。

    status 是 C 端 API 的「虚拟状态」查询参数，取值 "in_progress"/"pending_start" 是稳定的
    API 契约，与枚举成员的值无关（Phase 2 枚举值仍旧字面量，Phase 4 翻转后二者恰好重合）。
    """
    if status is None:
        return []
    if status == "in_progress":
        return [status_column == BookingStatus.IN_PROGRESS, payment_status_column == PaymentStatus.PAID]
    if status == "pending_start":
        return [
            status_column.in_([BookingStatus.PENDING_START, BookingStatus.PENDING_CONFIRM]),
            payment_status_column == PaymentStatus.PAID,
        ]
    return [status_column == status]
