from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.study_room import StudyRoomListResponse, StudyRoomResponse
from app.services import study_room_service

router = APIRouter(prefix="/api/v1/rooms", tags=["rooms"])


@router.get("", response_model=StudyRoomListResponse)
async def list_study_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    city_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
) -> StudyRoomListResponse:
    return await study_room_service.list_study_rooms(
        db, page=page, page_size=page_size, city_id=city_id
    )


@router.get("/{room_id}", response_model=StudyRoomResponse)
async def get_study_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
) -> StudyRoomResponse:
    try:
        return await study_room_service.get_study_room(db, room_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Room {room_id} not found")
