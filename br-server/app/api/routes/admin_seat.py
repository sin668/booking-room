from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin
from app.core.database import get_db
from app.schemas.seat import (
    SeatAdminResponse,
    SeatBulkCreate,
    SeatCreate,
    SeatStatusUpdate,
    SeatUpdate,
)
from app.services import seat_service

# Nested routes: /api/v1/admin/rooms/{room_id}/seats/...
room_seats_router = APIRouter(
    prefix="/api/v1/admin/rooms/{room_id}/seats",
    tags=["admin-seats"],
    dependencies=[Depends(get_current_admin)],
)

# Flat routes: /api/v1/admin/seats/{seat_id}/...
flat_seats_router = APIRouter(
    prefix="/api/v1/admin/seats",
    tags=["admin-seats"],
    dependencies=[Depends(get_current_admin)],
)


# ---- Room-nested endpoints ----


@room_seats_router.post("", response_model=SeatAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_seat(
    room_id: int,
    data: SeatCreate,
    db: AsyncSession = Depends(get_db),
) -> SeatAdminResponse:
    try:
        return await seat_service.create_seat(db, room_id, data.model_dump())
    except ValueError as e:
        msg = str(e)
        if "已存在相同编号" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


@room_seats_router.post("/bulk/", status_code=status.HTTP_201_CREATED)
async def bulk_create_seats(
    room_id: int,
    data: SeatBulkCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, int]:
    try:
        created = await seat_service.bulk_create_seats(db, room_id, [z.model_dump() for z in data.seats])
        return {"created": created}
    except ValueError as e:
        msg = str(e)
        if "已存在" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


@room_seats_router.get("", response_model=list[SeatAdminResponse])
async def list_seats(
    room_id: int,
    zone: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[SeatAdminResponse]:
    try:
        return await seat_service.admin_list_seats(db, room_id, zone=zone, status=status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---- Flat seat endpoints ----


@flat_seats_router.get("/{seat_id}", response_model=SeatAdminResponse)
async def get_seat(seat_id: int, db: AsyncSession = Depends(get_db)) -> SeatAdminResponse:
    try:
        return await seat_service.admin_get_seat(db, seat_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@flat_seats_router.put("/{seat_id}", response_model=SeatAdminResponse)
async def update_seat(
    seat_id: int,
    data: SeatUpdate,
    db: AsyncSession = Depends(get_db),
) -> SeatAdminResponse:
    try:
        return await seat_service.update_seat(db, seat_id, data.model_dump(exclude_unset=True))
    except ValueError as e:
        msg = str(e)
        if "已存在相同编号" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


@flat_seats_router.delete("/{seat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seat(seat_id: int, db: AsyncSession = Depends(get_db)) -> None:
    try:
        await seat_service.delete_seat(db, seat_id)
    except ValueError as e:
        msg = str(e)
        if "活跃预约" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


@flat_seats_router.patch("/{seat_id}/status/", response_model=SeatAdminResponse)
async def toggle_seat_status(
    seat_id: int,
    data: SeatStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> SeatAdminResponse:
    try:
        return await seat_service.toggle_seat_status(db, seat_id, data.status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
