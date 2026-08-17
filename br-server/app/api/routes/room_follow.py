import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.schemas.room_follow import FollowedRoomListResponse, FollowedRoomResponse
from app.services import room_follow_service

router = APIRouter(prefix="/api/v1/room-follows", tags=["room-follows"])


@router.get("", response_model=FollowedRoomListResponse)
async def list_followed_rooms(
    follow_type: str = Query("room", pattern="^(room|course)$"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> FollowedRoomListResponse:
    return await room_follow_service.list_followed_rooms(db, user_id, follow_type=follow_type)


@router.post("/{room_id}", response_model=FollowedRoomResponse)
async def follow_room(
    room_id: int,
    response: Response,
    follow_type: str = Query("room", pattern="^(room|course)$"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> FollowedRoomResponse:
    try:
        room, created = await room_follow_service.follow_room(
            db, user_id, room_id, follow_type=follow_type
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Target not found")

    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_room(
    room_id: int,
    follow_type: str = Query("room", pattern="^(room|course)$"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    await room_follow_service.unfollow_room(db, user_id, room_id, follow_type=follow_type)
