import uuid
from typing import Literal

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

_BOOKING_STATUS = Literal["confirmed", "cancelled", "completed"]


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BookingResponse:
    try:
        return await booking_service.create_booking(db, user_id, data)
    except booking_service.SeatNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="座位不存在")
    except booking_service.SeatMaintenanceError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该座位正在维护中")
    except booking_service.BookingConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该座位该时段已被预约")
    except booking_service.InvalidTimeRangeError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="结束时间必须晚于开始时间")
    except booking_service.BookingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    status_filter: _BOOKING_STATUS | None = Query(None, alias="status"),
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
    except booking_service.BookingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BookingResponse:
    try:
        return await booking_service.cancel_booking(db, booking_id, user_id)
    except booking_service.BookingAlreadyCancelledError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该预约已取消")
    except booking_service.BookingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
