"""API tests for current-user notification routes."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.models.notification import Notification, NotificationPreference
from app.models.user import User


USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
NOW = datetime.now(UTC)


@pytest.fixture
async def auth_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def seed_notification_data(db_session: AsyncSession) -> dict[str, Notification]:
    db_session.add_all(
        [
            User(
                id=USER_ID,
                phone="13800138011",
                nickname="当前用户",
                password_hash="hashed",
                username="api_notify_1",
            ),
            User(
                id=OTHER_USER_ID,
                phone="13800138012",
                nickname="其他用户",
                password_hash="hashed",
                username="api_notify_2",
            ),
        ]
    )
    await db_session.flush()

    notifications = {
        "booking_new": Notification(
            user_id=USER_ID,
            type="booking",
            title="预约成功",
            content="预约成功内容",
            target_url="/pages/booking/detail?id=1",
            target_type="booking",
            target_id="1",
            is_read=False,
            created_at=NOW,
        ),
        "report": Notification(
            user_id=USER_ID,
            type="report",
            title="学习报告",
            content="学习报告内容",
            is_read=False,
            created_at=NOW - timedelta(minutes=1),
        ),
        "booking_old": Notification(
            user_id=USER_ID,
            type="booking",
            title="预约提醒",
            content="预约提醒内容",
            is_read=False,
            created_at=NOW - timedelta(minutes=2),
        ),
        "activity_read": Notification(
            user_id=USER_ID,
            type="activity",
            title="活动通知",
            content="活动通知内容",
            is_read=True,
            read_at=NOW - timedelta(minutes=3),
            created_at=NOW - timedelta(minutes=3),
        ),
        "other_user": Notification(
            user_id=OTHER_USER_ID,
            type="booking",
            title="其他用户通知",
            content="不应泄露",
            is_read=False,
            created_at=NOW + timedelta(minutes=1),
        ),
    }
    db_session.add_all(notifications.values())
    await db_session.flush()
    return notifications


def _items(data: dict[str, Any]) -> list[dict[str, Any]]:
    assert "items" in data
    return data["items"]


@pytest.mark.asyncio
async def test_list_notifications_returns_only_current_user(
    auth_client: AsyncClient,
    seed_notification_data: dict[str, Notification],
) -> None:
    response = await auth_client.get("/api/v1/notifications")

    assert response.status_code == 200
    data = response.json()
    items = _items(data)
    assert data["total"] == 4
    assert data["page"] == 1
    assert data["page_size"] <= 50
    assert [item["title"] for item in items] == [
        "预约成功",
        "学习报告",
        "预约提醒",
        "活动通知",
    ]
    assert "其他用户通知" not in [item["title"] for item in items]
    assert all("user_id" not in item for item in items)


@pytest.mark.asyncio
async def test_list_notifications_supports_type_filter_and_pagination(
    auth_client: AsyncClient,
    seed_notification_data: dict[str, Notification],
) -> None:
    response = await auth_client.get(
        "/api/v1/notifications",
        params={"type": "booking", "page": 2, "page_size": 1},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["page"] == 2
    assert data["page_size"] == 1
    items = _items(data)
    assert len(items) == 1
    assert items[0]["type"] == "booking"
    assert items[0]["title"] == "预约提醒"


@pytest.mark.asyncio
async def test_mark_notification_read_only_allows_current_user_notification(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_notification_data: dict[str, Notification],
) -> None:
    notification = seed_notification_data["booking_new"]

    response = await auth_client.post(f"/api/v1/notifications/{notification.id}/read")

    assert response.status_code == 200
    await db_session.refresh(notification)
    assert notification.is_read is True
    assert notification.read_at is not None


@pytest.mark.asyncio
async def test_mark_cross_user_notification_read_is_rejected_and_not_modified(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_notification_data: dict[str, Notification],
) -> None:
    other_notification = seed_notification_data["other_user"]

    response = await auth_client.post(
        f"/api/v1/notifications/{other_notification.id}/read"
    )

    assert response.status_code in {403, 404}
    await db_session.refresh(other_notification)
    assert other_notification.is_read is False
    assert other_notification.read_at is None


@pytest.mark.asyncio
async def test_mark_all_read_marks_only_current_user_notifications(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_notification_data: dict[str, Notification],
) -> None:
    response = await auth_client.post("/api/v1/notifications/read-all")

    assert response.status_code == 200
    result = await db_session.execute(select(Notification))
    notifications = {item.title: item for item in result.scalars().all()}
    assert notifications["预约成功"].is_read is True
    assert notifications["学习报告"].is_read is True
    assert notifications["预约提醒"].is_read is True
    assert notifications["活动通知"].is_read is True
    assert notifications["其他用户通知"].is_read is False
    assert notifications["其他用户通知"].read_at is None


@pytest.mark.asyncio
async def test_mark_all_read_supports_type_filter_for_current_user_only(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_notification_data: dict[str, Notification],
) -> None:
    response = await auth_client.post(
        "/api/v1/notifications/read-all",
        params={"type": "booking"},
    )

    assert response.status_code == 200
    result = await db_session.execute(select(Notification))
    notifications = {item.title: item for item in result.scalars().all()}
    assert notifications["预约成功"].is_read is True
    assert notifications["预约提醒"].is_read is True
    assert notifications["学习报告"].is_read is False
    assert notifications["其他用户通知"].is_read is False


@pytest.mark.asyncio
async def test_preferences_default_enabled_and_update_round_trip(
    auth_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    response = await auth_client.get("/api/v1/notifications/preferences")

    assert response.status_code == 200
    data = response.json()
    assert data["booking_enabled"] is True
    assert data["activity_enabled"] is True
    assert data["report_enabled"] is True
    assert data["arrival_enabled"] is True
    assert "user_id" not in data

    expected = {
        "booking_enabled": True,
        "activity_enabled": True,
        "report_enabled": True,
        "arrival_enabled": True,
    }
    for key, value in expected.items():
        assert data[key] is value

    update_response = await auth_client.put(
        "/api/v1/notifications/preferences",
        json={
            "booking_enabled": False,
            "activity_enabled": True,
            "report_enabled": False,
            "arrival_enabled": True,
            "user_id": str(OTHER_USER_ID),
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["booking_enabled"] is False
    assert updated["activity_enabled"] is True
    assert updated["report_enabled"] is False
    assert updated["arrival_enabled"] is True
    assert "user_id" not in updated

    expected_updated = {
        "booking_enabled": False,
        "activity_enabled": True,
        "report_enabled": False,
        "arrival_enabled": True,
    }
    for key, value in expected_updated.items():
        assert updated[key] is value
    result = await db_session.execute(select(NotificationPreference))
    saved = result.scalar_one()
    assert saved.user_id == USER_ID
    assert saved.booking_enabled is False
    assert saved.report_enabled is False


@pytest.mark.asyncio
async def test_unread_summary_excludes_disabled_type_from_total(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_notification_data: dict[str, Notification],
) -> None:
    db_session.add(
        NotificationPreference(
            user_id=USER_ID,
            booking_enabled=True,
            activity_enabled=True,
            report_enabled=False,
            arrival_enabled=True,
        )
    )
    await db_session.flush()

    response = await auth_client.get("/api/v1/notifications/unread-summary")

    assert response.status_code == 200
    data = response.json()
    assert data["booking_count"] == 2
    assert data["report_count"] == 1
    assert data["activity_count"] == 0
    assert data["arrival_count"] == 0
    assert data["total_unread"] == 2
