"""培训课程列表 API 路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.course import CourseListResponse, TrainingRoomListResponse
from app.services import training_service

router = APIRouter(prefix="/api/v1/training", tags=["training"])


@router.get("/rooms", response_model=TrainingRoomListResponse)
async def list_training_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    city_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
) -> TrainingRoomListResponse:
    return await training_service.list_training_rooms(
        db, page=page, page_size=page_size, city_id=city_id
    )


@router.get("/courses", response_model=CourseListResponse)
async def list_training_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    category: str | None = Query(
        None,
        pattern="^(primaryschool|middleschool|postgraduate|civil_service|language|skills|professional)$",
    ),
    db: AsyncSession = Depends(get_db),
) -> CourseListResponse:
    return await training_service.list_courses(
        db, page=page, page_size=page_size, category=category
    )
