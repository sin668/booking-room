from __future__ import annotations

from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationPreference, NotificationType
from app.schemas.notification import (
    NotificationCreate,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
    NotificationTypeValue,
    NotificationUnreadSummaryResponse,
)


class NotificationNotFoundError(Exception):
    def __init__(self, detail: str = "Notification not found") -> None:
        self.detail = detail
        super().__init__(detail)


_NOTIFICATION_TYPES = {item.value for item in NotificationType}


def _validate_type(type_value: str) -> NotificationTypeValue:
    if type_value not in _NOTIFICATION_TYPES:
        raise ValueError("Unsupported notification type")
    return cast(NotificationTypeValue, type_value)


def _preference_enabled(preference: NotificationPreference, type_value: str) -> bool:
    return bool(getattr(preference, f"{type_value}_enabled"))


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_or_create_preferences(
        self,
        user_id: UUID,
    ) -> dict:
        preference = await self._get_or_create_preference_model(user_id)
        return NotificationPreferenceResponse.model_validate(preference).model_dump()

    async def update_preferences(
        self,
        user_id: UUID,
        data: NotificationPreferenceUpdate,
    ) -> dict:
        preference = await self._get_or_create_preference_model(user_id)
        updates = data.model_dump(exclude_unset=True)
        for key, value in updates.items():
            if value is not None:
                setattr(preference, key, value)
        preference.updated_at = datetime.now()
        await self._db.flush()
        await self._db.refresh(preference)
        return NotificationPreferenceResponse.model_validate(preference).model_dump()

    async def list_notifications(
        self,
        user_id: UUID,
        page: int,
        page_size: int,
        type: NotificationTypeValue | None = None,
    ) -> dict:
        conditions = [Notification.user_id == user_id]
        if type is not None:
            conditions.append(Notification.type == type)

        total_stmt = select(func.count()).select_from(Notification).where(*conditions)
        total_result = await self._db.execute(total_stmt)
        total = int(total_result.scalar_one() or 0)

        offset = (page - 1) * page_size
        stmt = (
            select(Notification)
            .where(*conditions)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._db.execute(stmt)
        notifications = result.scalars().all()

        return NotificationListResponse(
            items=[
                NotificationResponse.model_validate(notification)
                for notification in notifications
            ],
            total=total,
            page=page,
            page_size=page_size,
            has_more=offset + len(notifications) < total,
        ).model_dump()

    async def get_unread_summary(
        self,
        user_id: UUID,
    ) -> dict:
        preference = await self._get_or_create_preference_model(user_id)
        stmt = (
            select(Notification.type, func.count(Notification.id))
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .group_by(Notification.type)
        )
        result = await self._db.execute(stmt)
        counts = {type_value: int(count) for type_value, count in result.all()}

        booking_count = counts.get(NotificationType.BOOKING.value, 0)
        activity_count = counts.get(NotificationType.ACTIVITY.value, 0)
        report_count = counts.get(NotificationType.REPORT.value, 0)
        arrival_count = counts.get(NotificationType.ARRIVAL.value, 0)
        total_unread = sum(
            counts.get(type_value, 0)
            for type_value in _NOTIFICATION_TYPES
            if _preference_enabled(preference, type_value)
        )

        return NotificationUnreadSummaryResponse(
            total_unread=total_unread,
            booking_count=booking_count,
            activity_count=activity_count,
            report_count=report_count,
            arrival_count=arrival_count,
        ).model_dump()

    async def mark_read(
        self,
        user_id: UUID,
        notification_id: UUID,
    ) -> dict:
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        notification = result.scalar_one_or_none()
        if notification is None:
            raise NotificationNotFoundError()

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now()
            await self._db.flush()
            await self._db.refresh(notification)

        return NotificationResponse.model_validate(notification).model_dump()

    async def mark_all_read(
        self,
        user_id: UUID,
        type: NotificationTypeValue | None = None,
    ) -> int:
        conditions = [
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        ]
        if type is not None:
            conditions.append(Notification.type == type)

        stmt = (
            update(Notification)
            .where(*conditions)
            .values(is_read=True, read_at=datetime.now())
        )
        result = await self._db.execute(stmt)
        await self._db.flush()
        return int(result.rowcount or 0)

    async def create_notification(
        self,
        data: NotificationCreate,
    ) -> dict:
        type_value = _validate_type(data.type)
        notification = Notification(
            user_id=data.user_id,
            type=type_value,
            title=data.title,
            content=data.content,
            target_url=data.target_url,
            target_type=data.target_type,
            target_id=data.target_id,
            is_read=False,
        )
        self._db.add(notification)
        await self._db.flush()
        await self._db.refresh(notification)
        return NotificationResponse.model_validate(notification).model_dump()

    async def _get_or_create_preference_model(
        self,
        user_id: UUID,
    ) -> NotificationPreference:
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        result = await self._db.execute(stmt)
        preference = result.scalar_one_or_none()
        if preference is not None:
            return preference

        preference = NotificationPreference(user_id=user_id)
        self._db.add(preference)
        await self._db.flush()
        await self._db.refresh(preference)
        return preference
