from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.study_room import StudyRoomListResponse
from app.services import study_room_service

router = APIRouter(prefix="/api/v1/rooms", tags=["rooms"])


@router.get("", response_model=StudyRoomListResponse)
async def list_study_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> StudyRoomListResponse:
    return await study_room_service.list_study_rooms(db, page=page, page_size=page_size)
