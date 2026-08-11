import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_optional_current_user_id
from app.core.database import get_db
from app.schemas.activity import ActivityCouponClaimResponse, ActivityDetailResponse, ActivityResponse
from app.services import activity_service

router = APIRouter(prefix="/api/v1/activities", tags=["activities"])


@router.get("", response_model=list[ActivityResponse])
async def list_activities(db: AsyncSession = Depends(get_db)) -> list[ActivityResponse]:
    return await activity_service.list_active_activities(db)


@router.get("/{activity_id}", response_model=ActivityDetailResponse)
async def get_activity_detail(
    activity_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_optional_current_user_id),
) -> ActivityDetailResponse:
    detail = await activity_service.get_activity_detail(db, activity_id, user_id=user_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在或未上架")
    return detail


@router.post(
    "/{activity_id}/coupons/{activity_coupon_id}/claim",
    response_model=ActivityCouponClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
async def claim_activity_coupon(
    activity_id: int,
    activity_coupon_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ActivityCouponClaimResponse:
    try:
        return await activity_service.claim_activity_coupon_response(
            db,
            activity_id=activity_id,
            activity_coupon_id=activity_coupon_id,
            user_id=user_id,
        )
    except activity_service.ActivityCouponClaimError as exc:
        message = str(exc)
        if "不存在" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)
