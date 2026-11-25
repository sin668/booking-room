"""学习月报通知定时任务测试。"""

import uuid
from datetime import date, datetime, time
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.notification import Notification, NotificationPreference
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.user import User
from app.schemas.study_record import StudyRecordSummaryResponse
from app.services.monthly_study_report_scheduler import (
    _send_monthly_study_reports,
    next_monthly_study_report_run,
    parse_monthly_study_report_schedule,
)
from app.services.notification_service import NotificationService

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
REPORT_MONTH = date(2026, 11, 1)


def _summary(
    *,
    monthly_hours: float = 18.5,
    monthly_bookings: int = 6,
    max_streak_days: int = 2,
    total_hours: float = 161.27,
) -> StudyRecordSummaryResponse:
    return StudyRecordSummaryResponse(
        monthly_hours=monthly_hours,
        monthly_bookings=monthly_bookings,
        max_streak_days=max_streak_days,
        total_hours=total_hours,
        calendar_mark=[],
    )


@pytest.fixture
async def seed_user(db_session: AsyncSession) -> User:
    user = User(
        id=USER_ID,
        phone="18800000001",
        nickname="Report User",
        password_hash="hash",
        user_source="app",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def seed_room(db_session: AsyncSession) -> dict:
    room = StudyRoom(name="Report Room", address="123 Test St", status="open", min_price=10)
    db_session.add(room)
    await db_session.flush()
    seat = Seat(
        room_id=room.id,
        seat_number="A-01",
        zone="quiet",
        position="window",
        floor=3,
        price_per_hour=Decimal("15.00"),
        status="available",
        row=1,
        col=1,
    )
    db_session.add(seat)
    await db_session.flush()
    return {"room": room, "seat": seat}


def _add_completed_booking(db: AsyncSession, seed_room: dict, day: date) -> Booking:
    booking = Booking(
        seat_id=seed_room["seat"].id,
        user_id=str(USER_ID),
        room_id=seed_room["room"].id,
        date=day,
        start_time=time(9, 0),
        end_time=time(12, 0),
        status="completed",
        total_price=Decimal("45.00"),
    )
    db.add(booking)
    return booking


@pytest.mark.asyncio
async def test_notify_monthly_study_report_content_and_dedupe(
    db_session: AsyncSession, seed_user: User
) -> None:
    service = NotificationService(db_session)

    notification = await service.notify_monthly_study_report(
        USER_ID, REPORT_MONTH, _summary()
    )

    assert notification is not None
    assert notification["title"] == "本月学习报告已生成"
    assert notification["content"] == (
        "您本月已累计学习 18.50 小时，完成学习 6 次，"
        "连续学习 2 天，总累计学习 161.27 小时。"
    )
    assert notification["target_url"] == "/pages-sub/study-record/index"
    assert notification["target_type"] == "monthly_study_report"
    assert notification["target_id"] == "2026-11"

    again = await service.notify_monthly_study_report(USER_ID, REPORT_MONTH, _summary())
    assert again is None


@pytest.mark.asyncio
async def test_notify_monthly_study_report_respects_disabled_preference(
    db_session: AsyncSession, seed_user: User
) -> None:
    db_session.add(NotificationPreference(user_id=USER_ID, report_enabled=False))
    await db_session.flush()

    notification = await NotificationService(db_session).notify_monthly_study_report(
        USER_ID, REPORT_MONTH, _summary()
    )

    assert notification is None
    count = (
        await db_session.execute(select(func.count()).select_from(Notification))
    ).scalar_one()
    assert count == 0


def test_parse_monthly_study_report_schedule_reads_valid_config(monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "MONTHLY_STUDY_REPORT_DAY_OF_WEEK", "Sunday")
    monkeypatch.setattr(settings, "MONTHLY_STUDY_REPORT_TIME", "21:30")

    assert parse_monthly_study_report_schedule() == ("sun", 21, 30)


def test_parse_monthly_study_report_schedule_falls_back(monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "MONTHLY_STUDY_REPORT_DAY_OF_WEEK", "funday")
    monkeypatch.setattr(settings, "MONTHLY_STUDY_REPORT_TIME", "25:99")

    assert parse_monthly_study_report_schedule() == ("mon", 9, 0)


def test_next_monthly_study_report_run_same_day_and_next_week() -> None:
    monday_morning = datetime(2026, 11, 23, 8, 0)
    assert next_monthly_study_report_run(monday_morning, "mon", 9, 0) == datetime(
        2026, 11, 23, 9, 0
    )

    monday_noon = datetime(2026, 11, 23, 12, 0)
    assert next_monthly_study_report_run(monday_noon, "mon", 9, 0) == datetime(
        2026, 11, 30, 9, 0
    )

    wednesday = datetime(2026, 11, 25, 10, 0)
    assert next_monthly_study_report_run(wednesday, "mon", 9, 0) == datetime(
        2026, 11, 30, 9, 0
    )


@pytest.mark.asyncio
async def test_send_reports_skips_user_without_study(
    db_session: AsyncSession, seed_user: User
) -> None:
    stats = await _send_monthly_study_reports(db_session, REPORT_MONTH)

    assert stats == {"total_scanned": 1, "sent": 0, "skipped": 1, "failed": 0}
    count = (
        await db_session.execute(select(func.count()).select_from(Notification))
    ).scalar_one()
    assert count == 0


@pytest.mark.asyncio
async def test_send_reports_sends_once_and_dedupes(
    db_session: AsyncSession, seed_user: User, seed_room: dict
) -> None:
    _add_completed_booking(db_session, seed_room, date(2026, 11, 2))
    await db_session.flush()

    first = await _send_monthly_study_reports(db_session, REPORT_MONTH)
    second = await _send_monthly_study_reports(db_session, REPORT_MONTH)

    assert first == {"total_scanned": 1, "sent": 1, "skipped": 0, "failed": 0}
    assert second == {"total_scanned": 1, "sent": 0, "skipped": 1, "failed": 0}

    notifications = (
        (await db_session.execute(select(Notification))).scalars().all()
    )
    assert len(notifications) == 1
    assert notifications[0].content == (
        "您本月已累计学习 3.00 小时，完成学习 1 次，"
        "连续学习 1 天，总累计学习 3.00 小时。"
    )


@pytest.mark.asyncio
async def test_send_reports_skips_disabled_user(
    db_session: AsyncSession, seed_user: User, seed_room: dict
) -> None:
    _add_completed_booking(db_session, seed_room, date(2026, 11, 2))
    db_session.add(NotificationPreference(user_id=USER_ID, report_enabled=False))
    await db_session.flush()

    stats = await _send_monthly_study_reports(db_session, REPORT_MONTH)

    assert stats == {"total_scanned": 1, "sent": 0, "skipped": 1, "failed": 0}
    count = (
        await db_session.execute(select(func.count()).select_from(Notification))
    ).scalar_one()
    assert count == 0
