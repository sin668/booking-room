from typing import cast, get_args
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_db
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationReadAllResponse,
    NotificationResponse,
    NotificationTypeValue,
    NotificationUnreadSummaryResponse,
)
from app.services.notification_service import (
    NotificationNotFoundError,
    NotificationService,
)


router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

_NOTIFICATION_TYPES = set(get_args(NotificationTypeValue))


def _parse_notification_type(type_value: str | None) -> NotificationTypeValue | None:
    if type_value is None:
        return None
    if type_value not in _NOTIFICATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported notification type",
        )
    return cast(NotificationTypeValue, type_value)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> NotificationListResponse:
    service = NotificationService(db)
    return await service.list_notifications(
        user_id=user_id,
        page=page,
        page_size=page_size,
        type=_parse_notification_type(type),
    )


@router.get("/unread-summary", response_model=NotificationUnreadSummaryResponse)
async def get_unread_summary(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> NotificationUnreadSummaryResponse:
    service = NotificationService(db)
    return await service.get_unread_summary(user_id=user_id)


@router.post("/read-all", response_model=NotificationReadAllResponse)
async def mark_all_notifications_read(
    type: str | None = Query(None),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> NotificationReadAllResponse:
    service = NotificationService(db)
    updated_count = await service.mark_all_read(
        user_id=user_id,
        type=_parse_notification_type(type),
    )
    return NotificationReadAllResponse(updated_count=updated_count)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    service = NotificationService(db)
    try:
        return await service.mark_read(
            user_id=user_id,
            notification_id=notification_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> NotificationPreferenceResponse:
    service = NotificationService(db)
    return await service.get_or_create_preferences(user_id=user_id)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    body: NotificationPreferenceUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> NotificationPreferenceResponse:
    service = NotificationService(db)
    return await service.update_preferences(user_id=user_id, data=body)
