from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin
from app.core.database import get_db
from app.schemas.activity import (
    ActivityAdminResponse,
    ActivityCreate,
    ActivityListResponse,
    ActivityStatusUpdate,
    ActivityUpdate,
)
from app.services import activity_service

router = APIRouter(prefix="/api/v1/admin/activities", tags=["admin-activities"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=ActivityListResponse)
async def list_activities(
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> ActivityListResponse:
    return await activity_service.list_activities(db, page=page, page_size=page_size, keyword=keyword, is_active=is_active)


@router.post("", response_model=ActivityAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(data: ActivityCreate, db: AsyncSession = Depends(get_db)) -> ActivityAdminResponse:
    activity = await activity_service.create_activity(db, data.model_dump())
    return activity


@router.get("/{activity_id}", response_model=ActivityAdminResponse)
async def get_activity(activity_id: int, db: AsyncSession = Depends(get_db)) -> ActivityAdminResponse:
    activity = await activity_service.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    return activity


@router.put("/{activity_id}", response_model=ActivityAdminResponse)
async def update_activity(activity_id: int, data: ActivityUpdate, db: AsyncSession = Depends(get_db)) -> ActivityAdminResponse:
    activity = await activity_service.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    return await activity_service.update_activity(db, activity, data.model_dump(exclude_unset=True))


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(activity_id: int, db: AsyncSession = Depends(get_db)) -> None:
    activity = await activity_service.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    await activity_service.delete_activity(db, activity)


@router.patch("/{activity_id}/status", response_model=ActivityAdminResponse)
async def toggle_status(activity_id: int, data: ActivityStatusUpdate, db: AsyncSession = Depends(get_db)) -> ActivityAdminResponse:
    activity = await activity_service.get_activity_by_id(db, activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    return await activity_service.toggle_activity_status(db, activity, data.is_active)
