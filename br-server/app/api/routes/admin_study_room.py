from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin
from app.core.database import get_db
from app.schemas.study_room import (
    RoomAdminListResponse,
    RoomAdminResponse,
    RoomCreate,
    RoomStatusUpdate,
    RoomUpdate,
)
from app.services import study_room_service

router = APIRouter(
    prefix="/api/v1/admin/rooms",
    tags=["admin-study-rooms"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("", response_model=RoomAdminListResponse)
async def list_rooms(
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> RoomAdminListResponse:
    return await study_room_service.admin_list_rooms(db, page=page, page_size=page_size, status=status)


@router.post("", response_model=RoomAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_room(data: RoomCreate, db: AsyncSession = Depends(get_db)) -> RoomAdminResponse:
    return await study_room_service.create_room(db, data.model_dump())


@router.get("/{room_id}", response_model=RoomAdminResponse)
async def get_room(room_id: int, db: AsyncSession = Depends(get_db)) -> RoomAdminResponse:
    try:
        return await study_room_service.admin_get_room(db, room_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{room_id}", response_model=RoomAdminResponse)
async def update_room(room_id: int, data: RoomUpdate, db: AsyncSession = Depends(get_db)) -> RoomAdminResponse:
    try:
        return await study_room_service.update_room(db, room_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(room_id: int, db: AsyncSession = Depends(get_db)) -> None:
    try:
        await study_room_service.delete_room(db, room_id)
    except ValueError as e:
        msg = str(e)
        if "活跃预约" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


@router.patch("/{room_id}/status/", response_model=RoomAdminResponse)
async def toggle_room_status(room_id: int, data: RoomStatusUpdate, db: AsyncSession = Depends(get_db)) -> RoomAdminResponse:
    try:
        return await study_room_service.toggle_room_status(db, room_id, data.status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
