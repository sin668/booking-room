import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.schemas.booking import (
    BookingCreate,
    BookingListResponse,
    BookingResponse,
)
from app.services import booking_service

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BookingResponse:
    try:
        return await booking_service.create_booking(db, user_id, data)
    except ValueError as e:
        msg = str(e)
        if msg == "座位不存在":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        if msg == "该座位该时段已被预约":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
        if msg == "该座位正在维护中":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        if "时间" in msg:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BookingListResponse:
    return await booking_service.list_bookings(
        db, user_id, page=page, page_size=page_size, status=status_filter
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BookingResponse:
    try:
        return await booking_service.get_booking(db, booking_id, user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BookingResponse:
    try:
        return await booking_service.cancel_booking(db, booking_id, user_id)
    except ValueError as e:
        msg = str(e)
        if msg == "该预约已取消":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
