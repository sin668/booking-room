"""预约生命周期与活动群发通知测试。"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.booking_status import PaymentMethod
from app.models.activity import Activity, ActivityCoupon
from app.models.booking import Booking
from app.models.coupon import Coupon
from app.models.course import Course
from app.models.lesson_schedule import LessonSchedule
from app.models.notification import Notification, NotificationPreference
from app.models.study_room import StudyRoom
from app.models.user import User
from app.services import activity_service, booking_service
from app.services.notification_service import NotificationService
from app.services.order_status_scheduler import (
    _is_within_reminder_window,
    _lesson_start_at,
    _maybe_notify_course_start_reminder,
    _maybe_notify_seat_start_reminder,
    _process_seat_booking,
)
from app.utils.timezone import booking_now

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
DISABLED_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
ADMIN_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")
DELETED_ID = uuid.UUID("55555555-5555-5555-5555-555555555555")


@pytest.fixture
async def base_data(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            User(
                id=USER_ID,
                phone="13800138001",
                nickname="张三",
                password_hash="hashed",
                username="notify_user_1",
                balance=Decimal("100.00"),
            ),
            StudyRoom(id=1, name="光谷自习室", address="测试地址", status="open"),
            Course(id=2, room_id=1, name="雅思冲刺班", category="training", status="active"),
        ]
    )
    await db_session.flush()


def _seat_booking(
    booking_id: int = 1,
    *,
    booking_date: date = date(2026, 6, 1),
    start_time: time = time(9, 0),
    end_time: time = time(11, 0),
    status: str = "pending_start",
    payment_status: str = "paid",
) -> Booking:
    return Booking(
        id=booking_id,
        user_id=str(USER_ID),
        room_id=1,
        seat_id=1,
        date=booking_date,
        start_time=start_time,
        end_time=end_time,
        status=status,
        payment_status=payment_status,
        total_price=Decimal("10.00"),
        booking_type="seat",
    )


def _course_booking(booking_id: int = 2) -> Booking:
    return Booking(
        id=booking_id,
        user_id=str(USER_ID),
        room_id=1,
        date=date(2026, 6, 1),
        start_time=time(9, 0),
        end_time=time(11, 0),
        status="pending_start",
        payment_status="paid",
        total_price=Decimal("20.00"),
        booking_type="course",
        course_id=2,
        lesson_ids=[11],
    )


async def _notifications(db_session: AsyncSession, user_id: uuid.UUID) -> list[Notification]:
    result = await db_session.execute(
        select(Notification).where(Notification.user_id == user_id)
    )
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_booking_paid_notification_content_and_dedupe(
    db_session: AsyncSession, base_data: None
) -> None:
    booking = _seat_booking()
    db_session.add(booking)
    await db_session.flush()

    service = NotificationService(db_session)
    await service.notify_booking_paid(booking)
    await service.notify_booking_paid(booking)

    items = await _notifications(db_session, USER_ID)
    assert len(items) == 1
    item = items[0]
    assert item.type == "booking"
    assert item.title == "预约成功通知"
    assert "光谷自习室" in item.content
    assert item.target_url == "/pages-sub/orders/index"
    assert item.target_type == "booking"
    assert item.target_id == "1"


@pytest.mark.asyncio
async def test_booking_notification_respects_disabled_preference(
    db_session: AsyncSession, base_data: None
) -> None:
    db_session.add(NotificationPreference(user_id=USER_ID, booking_enabled=False))
    booking = _seat_booking()
    db_session.add(booking)
    await db_session.flush()

    result = await NotificationService(db_session).notify_booking_paid(booking)

    assert result is None
    assert await _notifications(db_session, USER_ID) == []


@pytest.mark.asyncio
async def test_booking_completed_notification(db_session: AsyncSession, base_data: None) -> None:
    booking = _seat_booking(status="in_progress")
    db_session.add(booking)
    await db_session.flush()

    await NotificationService(db_session).notify_booking_completed(booking)

    items = await _notifications(db_session, USER_ID)
    assert len(items) == 1
    assert items[0].title == "离店核销完成"


@pytest.mark.asyncio
async def test_course_start_reminder_uses_lesson_target(
    db_session: AsyncSession, base_data: None
) -> None:
    booking = _course_booking()
    db_session.add(booking)
    await db_session.flush()
    lesson = LessonSchedule(
        schedule_id=1,
        lesson_id=11,
        lesson_date=date(2026, 6, 1),
        lesson_time_slot="09:10-11:00",
        sort_order=0,
    )

    await NotificationService(db_session).notify_booking_start_soon(booking, lesson)

    items = await _notifications(db_session, USER_ID)
    assert len(items) == 1
    assert items[0].title == "预约开始提醒"
    assert items[0].target_id == "2-11"
    assert "雅思冲刺班" in items[0].content
    assert "09:10-11:00" in items[0].content


def test_reminder_window_helpers() -> None:
    now = datetime(2026, 6, 1, 9, 0)
    assert _is_within_reminder_window(datetime(2026, 6, 1, 9, 10), now)
    assert not _is_within_reminder_window(datetime(2026, 6, 1, 8, 0), now)
    assert not _is_within_reminder_window(datetime(2026, 6, 1, 9, 20), now)
    assert not _is_within_reminder_window(None, now)

    lesson = SimpleNamespace(
        lesson_date=date(2026, 6, 1), lesson_time_slot="09:10-11:00"
    )
    assert _lesson_start_at(lesson) == datetime(2026, 6, 1, 9, 10)
    assert _lesson_start_at(SimpleNamespace(lesson_date=date(2026, 6, 1), lesson_time_slot="")) is None


@pytest.mark.asyncio
async def test_seat_start_reminder_only_inside_window(
    db_session: AsyncSession, base_data: None
) -> None:
    booking = _seat_booking(start_time=time(9, 10), end_time=time(11, 0))
    db_session.add(booking)
    await db_session.flush()

    await _maybe_notify_seat_start_reminder(
        db_session, booking, datetime(2026, 6, 1, 8, 40)
    )
    assert await _notifications(db_session, USER_ID) == []

    await _maybe_notify_seat_start_reminder(
        db_session, booking, datetime(2026, 6, 1, 9, 0)
    )
    items = await _notifications(db_session, USER_ID)
    assert len(items) == 1
    assert items[0].title == "预约开始提醒"
    assert "光谷自习室" in items[0].content


@pytest.mark.asyncio
async def test_course_start_reminder_sends_for_due_lesson(
    db_session: AsyncSession, base_data: None
) -> None:
    booking = _course_booking()
    db_session.add(booking)
    await db_session.flush()
    due_lesson = LessonSchedule(
        schedule_id=1,
        lesson_id=11,
        lesson_date=date(2026, 6, 1),
        lesson_time_slot="09:10-11:00",
        sort_order=0,
    )
    later_lesson = LessonSchedule(
        schedule_id=1,
        lesson_id=12,
        lesson_date=date(2026, 6, 2),
        lesson_time_slot="09:10-11:00",
        sort_order=1,
    )

    await _maybe_notify_course_start_reminder(
        db_session, booking, [due_lesson, later_lesson], datetime(2026, 6, 1, 9, 0)
    )

    items = await _notifications(db_session, USER_ID)
    assert len(items) == 1
    assert items[0].target_id == "2-11"


@pytest.mark.asyncio
async def test_scheduler_completes_booking_and_notifies(
    db_session: AsyncSession, base_data: None
) -> None:
    booking = _seat_booking(status="in_progress", end_time=time(11, 0))
    db_session.add(booking)
    await db_session.flush()
    stats = {
        "total_scanned": 0,
        "seat_started": 0,
        "seat_completed": 0,
        "course_started": 0,
        "course_highlight_updated": 0,
        "course_completed": 0,
    }

    await _process_seat_booking(
        db_session, booking, datetime(2026, 6, 1, 11, 5), stats
    )

    assert booking.status == "completed"
    items = await _notifications(db_session, USER_ID)
    assert len(items) == 1
    assert items[0].title == "离店核销完成"


@pytest.mark.asyncio
async def test_balance_payment_sends_booking_success(
    db_session: AsyncSession, base_data: None
) -> None:
    booking = _seat_booking(status="pending_start", payment_status="pending")
    db_session.add(booking)
    await db_session.flush()

    await booking_service.pay_pending_booking(
        db_session, booking.id, USER_ID, PaymentMethod.BALANCE
    )

    items = await _notifications(db_session, USER_ID)
    assert len(items) == 1
    assert items[0].title == "预约成功通知"


@pytest.mark.asyncio
async def test_activity_broadcast_scope_and_dedupe(
    db_session: AsyncSession, base_data: None
) -> None:
    db_session.add_all(
        [
            User(
                id=OTHER_ID,
                phone="13800138002",
                nickname="李四",
                password_hash="hashed",
                username="notify_user_2",
            ),
            User(
                id=DISABLED_ID,
                phone="13800138003",
                nickname="王五",
                password_hash="hashed",
                username="notify_user_3",
            ),
            User(
                id=ADMIN_ID,
                phone="13800138004",
                nickname="管理员",
                password_hash="hashed",
                username="notify_admin",
                user_source="admin",
            ),
            User(
                id=DELETED_ID,
                phone="13800138005",
                nickname="已删除",
                password_hash="hashed",
                username="notify_deleted",
                status="deleted",
            ),
            NotificationPreference(user_id=OTHER_ID, activity_enabled=True),
            NotificationPreference(user_id=DISABLED_ID, activity_enabled=False),
        ]
    )
    await db_session.flush()
    activity = Activity(id=10, title="双十一活动", description="满减优惠", is_active=True)

    service = NotificationService(db_session)
    sent = await service.broadcast_activity(activity)
    assert sent == 2

    recipient_ids = {
        row.user_id
        for row in (
            await db_session.execute(select(Notification))
        ).scalars().all()
    }
    assert recipient_ids == {USER_ID, OTHER_ID}

    first = (await _notifications(db_session, USER_ID))[0]
    assert first.type == "activity"
    assert first.title == "双十一活动"
    assert first.content == "满减优惠"
    assert first.target_url == "/pages-sub/activity/detail?id=10"
    assert first.target_type == "activity"
    assert first.target_id == "10"

    assert await service.broadcast_activity(activity) == 0


@pytest.mark.asyncio
async def test_activity_save_broadcasts_only_when_published_with_coupons(
    db_session: AsyncSession, base_data: None
) -> None:
    db_session.add(
        Coupon(
            id=1,
            name="满减券",
            type="discount",
            discount_amount=Decimal("10.00"),
            min_order_amount=Decimal("0.00"),
            valid_from=datetime(2026, 1, 1),
            expires_at=datetime(2027, 1, 1),
            is_active=True,
        )
    )
    await db_session.flush()

    created = await activity_service.create_activity(
        db_session,
        {
            "title": "未上架活动",
            "description": "不应发送",
            "content_html": "<p>内容</p>",
            "is_active": False,
            "activity_coupons": [{"coupon_id": 1, "total_quantity": 10}],
        },
    )
    assert await _notifications(db_session, USER_ID) == []

    activity = await activity_service.get_activity_by_id(db_session, created.id)
    assert activity is not None
    await activity_service.update_activity(db_session, activity, {"is_active": True})

    items = await _notifications(db_session, USER_ID)
    assert len(items) == 1
    assert items[0].title == "未上架活动"
    assert items[0].content == "不应发送"
    assert items[0].target_url == f"/pages-sub/activity/detail?id={created.id}"
