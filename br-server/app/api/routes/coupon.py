from datetime import date, time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.schemas.coupon import AvailableCouponsForBookingListResponse, CouponResponse
from app.services import coupon_service

router = APIRouter(prefix="/api/v1/coupons", tags=["coupons"])

CouponStatusQuery = Literal["available", "used", "expired"]


@router.get("", response_model=list[CouponResponse])
async def list_coupons(
    status_filter: CouponStatusQuery | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    user_id=Depends(get_current_user_id),
) -> list[CouponResponse]:
    return await coupon_service.list_user_coupons(db, user_id, status=status_filter)


@router.get("/available-for-booking", response_model=AvailableCouponsForBookingListResponse)
async def list_available_coupons_for_booking(
    seat_id: int = Query(..., ge=1),
    date: date = Query(...),
    start_time: time = Query(...),
    end_time: time = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id=Depends(get_current_user_id),
) -> AvailableCouponsForBookingListResponse:
    try:
        return await coupon_service.list_available_coupons_for_booking(db, user_id, seat_id, date, start_time, end_time)
    except coupon_service.CouponNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="座位不存在")
    except coupon_service.CouponError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

