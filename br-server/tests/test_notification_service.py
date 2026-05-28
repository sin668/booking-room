"""Service tests for user message notifications."""

from __future__ import annotations

import inspect
import uuid
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationPreference
from app.models.user import User
from app.schemas.notification import NotificationCreate
from app.schemas.notification import NotificationPreferenceUpdate
from app.services.notification_service import NotificationService


USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
async def users(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            User(
                id=USER_ID,
                phone="13800138001",
                nickname="通知用户",
                password_hash="hashed",
                username="notify_user_1",
            ),
            User(
                id=OTHER_USER_ID,
                phone="13800138002",
                nickname="其他用户",
                password_hash="hashed",
                username="notify_user_2",
            ),
        ]
    )
    await db_session.flush()


def _service(db_session: AsyncSession) -> NotificationService:
    return NotificationService(db_session)


async def _call(obj: Any, names: tuple[str, ...], *args: Any, **kwargs: Any) -> Any:
    for name in names:
        method = getattr(obj, name, None)
        if method is None:
            continue
        try:
            result = method(*args, **kwargs)
        except TypeError:
            continue
        if inspect.isawaitable(result):
            return await result
        return result
    raise AssertionError(f"NotificationService is missing one of: {', '.join(names)}")


def _get_attr(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj[key]
    return getattr(obj, key)


def _user_id_equals(value: Any, expected: uuid.UUID) -> bool:
    return value == expected or str(value) == str(expected)


def _type_value(value: Any) -> str:
    return getattr(value, "value", value)


async def _create_notification(
    db_session: AsyncSession,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    content: str,
    is_read: bool = False,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        content=content,
        is_read=is_read,
    )
    db_session.add(notification)
    await db_session.flush()
    return notification


@pytest.mark.asyncio
async def test_default_preferences_are_all_enabled(
    db_session: AsyncSession,
    users: None,
) -> None:
    preferences = await _call(
        _service(db_session),
        ("get_or_create_preferences", "get_preferences"),
        USER_ID,
    )

    assert _get_attr(preferences, "booking_enabled") is True
    assert _get_attr(preferences, "activity_enabled") is True
    assert _get_attr(preferences, "report_enabled") is True
    assert _get_attr(preferences, "arrival_enabled") is True

    result = await db_session.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == USER_ID
        )
    )
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_update_preferences_persists_all_enabled_flags(
    db_session: AsyncSession,
    users: None,
) -> None:
    payload = NotificationPreferenceUpdate(
        booking_enabled=False,
        activity_enabled=True,
        report_enabled=False,
        arrival_enabled=True,
    )

    updated = await _call(
        _service(db_session),
        ("update_preferences", "update_notification_preferences"),
        USER_ID,
        payload,
    )

    assert _get_attr(updated, "booking_enabled") is False
    assert _get_attr(updated, "activity_enabled") is True
    assert _get_attr(updated, "report_enabled") is False
    assert _get_attr(updated, "arrival_enabled") is True

    result = await db_session.execute(
        select(NotificationPreference).where(
            NotificationPreference.user_id == USER_ID
        )
    )
    saved = result.scalar_one()
    assert saved.booking_enabled is False
    assert saved.activity_enabled is True
    assert saved.report_enabled is False
    assert saved.arrival_enabled is True


@pytest.mark.asyncio
async def test_unread_summary_excludes_disabled_types_from_total_unread(
    db_session: AsyncSession,
    users: None,
) -> None:
    db_session.add(
        NotificationPreference(
            user_id=USER_ID,
            booking_enabled=True,
            activity_enabled=False,
            report_enabled=True,
            arrival_enabled=True,
        )
    )
    await _create_notification(db_session, USER_ID, "booking", "预约提醒", "预约内容")
    await _create_notification(db_session, USER_ID, "activity", "活动通知", "活动内容")
    await _create_notification(db_session, USER_ID, "report", "学习报告", "报告内容")
    await _create_notification(db_session, USER_ID, "arrival", "到店提醒", "到店内容")
    await _create_notification(db_session, OTHER_USER_ID, "booking", "他人通知", "隔离")
    await db_session.flush()

    summary = await _call(
        _service(db_session),
        ("get_unread_summary", "get_notification_unread_summary"),
        USER_ID,
    )

    assert _get_attr(summary, "booking_count") == 1
    assert _get_attr(summary, "activity_count") == 1
    assert _get_attr(summary, "report_count") == 1
    assert _get_attr(summary, "arrival_count") == 1
    assert _get_attr(summary, "total_unread") == 3


@pytest.mark.asyncio
async def test_create_notification_creates_unread_notification(
    db_session: AsyncSession,
    users: None,
) -> None:
    created = await _call(
        _service(db_session),
        ("create_notification",),
        NotificationCreate(
            user_id=USER_ID,
            type="booking",
            title="预约成功",
            content="您的预约已确认",
            target_url="/pages/booking/detail?id=1",
            target_type="booking",
            target_id="1",
        ),
    )

    assert _type_value(_get_attr(created, "type")) == "booking"
    assert _get_attr(created, "title") == "预约成功"
    assert _get_attr(created, "content") == "您的预约已确认"
    assert _get_attr(created, "is_read") is False
    assert _get_attr(created, "read_at") is None

    result = await db_session.execute(select(Notification))
    saved = result.scalar_one()
    assert _user_id_equals(saved.user_id, USER_ID)
    assert _type_value(saved.type) == "booking"
    assert saved.is_read is False
