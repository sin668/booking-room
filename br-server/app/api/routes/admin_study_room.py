from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminContext, get_current_admin, require_admin_permission
from app.core.database import get_db
from app.models.study_room import StudyRoom
from app.schemas.study_room import (
    RoomAdminListResponse,
    RoomAdminResponse,
    RoomCreate,
    RoomMapSuggestionResponse,
    RoomReverseGeocodeResponse,
    RoomStatusUpdate,
    RoomUpdate,
)
from app.services import study_room_service, tencent_map_service
from app.services.data_scope import creator_id, ensure_writable

router = APIRouter(
    prefix="/api/v1/admin/rooms",
    tags=["admin-study-rooms"],
)


@router.get("", response_model=RoomAdminListResponse, dependencies=[Depends(require_admin_permission("room:view"))])
async def list_rooms(
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
    room_type: str | None = Query(None, pattern="^(study|training|comprehensive)$"),
    city_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
    context: AdminContext | None = Depends(get_current_admin),
) -> RoomAdminListResponse:
    return await study_room_service.admin_list_rooms(
        db, page=page, page_size=page_size, status=status, room_type=room_type, city_id=city_id,
        viewer=context,
    )


@router.post(
    "",
    response_model=RoomAdminResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_permission("room:create"))],
)
async def create_room(
    data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    context: AdminContext | None = Depends(get_current_admin),
) -> RoomAdminResponse:
    return await study_room_service.create_room(db, data.model_dump(), created_by=creator_id(context))


@router.get(
    "/geocode/suggest",
    response_model=RoomMapSuggestionResponse,
    dependencies=[Depends(require_admin_permission("room:view"))],
)
async def suggest_room_location(
    keyword: str = Query(..., min_length=1, max_length=50),
) -> RoomMapSuggestionResponse:
    """服务端转发腾讯位置服务搜索，避免浏览器端 WebServiceAPI 鉴权失败。"""
    return RoomMapSuggestionResponse(
        items=await tencent_map_service.suggest_places(keyword)
    )


@router.get(
    "/geocode/reverse",
    response_model=RoomReverseGeocodeResponse,
    dependencies=[Depends(require_admin_permission("room:view"))],
)
async def reverse_room_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
) -> RoomReverseGeocodeResponse:
    return RoomReverseGeocodeResponse(
        address=await tencent_map_service.reverse_geocode(latitude, longitude)
    )


@router.get("/{room_id}", response_model=RoomAdminResponse, dependencies=[Depends(require_admin_permission("room:view"))])
async def get_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    context: AdminContext | None = Depends(get_current_admin),
) -> RoomAdminResponse:
    try:
        return await study_room_service.admin_get_room(db, room_id, viewer=context)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{room_id}", response_model=RoomAdminResponse, dependencies=[Depends(require_admin_permission("room:update"))])
async def update_room(
    room_id: int,
    data: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    context: AdminContext | None = Depends(get_current_admin),
) -> RoomAdminResponse:
    await ensure_writable(db, StudyRoom, room_id, context)
    try:
        return await study_room_service.update_room(db, room_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_permission("room:delete"))])
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    context: AdminContext | None = Depends(get_current_admin),
) -> None:
    await ensure_writable(db, StudyRoom, room_id, context)
    try:
        await study_room_service.delete_room(db, room_id)
    except ValueError as e:
        msg = str(e)
        if "活跃预约" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


@router.patch("/{room_id}/status", response_model=RoomAdminResponse, dependencies=[Depends(require_admin_permission("room:status"))])
async def toggle_room_status(
    room_id: int,
    data: RoomStatusUpdate,
    db: AsyncSession = Depends(get_db),
    context: AdminContext | None = Depends(get_current_admin),
) -> RoomAdminResponse:
    await ensure_writable(db, StudyRoom, room_id, context)
    try:
        return await study_room_service.toggle_room_status(db, room_id, data.status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
