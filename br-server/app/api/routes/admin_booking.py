from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin
from app.core.database import get_db
from app.schemas.booking import BookingAdminListResponse, BookingAdminResponse
from app.services import booking_service

router = APIRouter(prefix="/api/v1/admin/bookings", tags=["admin-bookings"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=BookingAdminListResponse)
async def list_bookings(
    page: int = 1,
    page_size: int = 10,
    status: str | None = None,
    room_id: int | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
    db: AsyncSession = Depends(get_db),
) -> BookingAdminListResponse:
    return await booking_service.admin_list_bookings(
        db, page=page, page_size=page_size, status=status, room_id=room_id, date_start=date_start, date_end=date_end
    )


@router.get("/{booking_id}", response_model=BookingAdminResponse)
async def get_booking(booking_id: int, db: AsyncSession = Depends(get_db)) -> BookingAdminResponse:
    try:
        return await booking_service.admin_get_booking(db, booking_id)
    except booking_service.BookingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")


@router.post("/{booking_id}/cancel", response_model=BookingAdminResponse)
async def cancel_booking(booking_id: int, db: AsyncSession = Depends(get_db)) -> BookingAdminResponse:
    try:
        return await booking_service.admin_cancel_booking(db, booking_id)
    except booking_service.BookingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    except booking_service.BookingAlreadyCancelledError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该预约已取消")
