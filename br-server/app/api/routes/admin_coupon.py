from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin_permission
from app.core.database import get_db
from app.schemas.coupon_admin import (
    AdminCouponCreate,
    AdminCouponListResponse,
    AdminCouponResponse,
    AdminCouponStatusUpdate,
    AdminCouponUpdate,
)
from app.services import admin_coupon_service

router = APIRouter(prefix="/api/v1/admin/coupons", tags=["admin-coupons"])


def _service_error(exc: admin_coupon_service.AdminCouponError) -> HTTPException:
    status_code = (
        status.HTTP_404_NOT_FOUND
        if isinstance(exc, admin_coupon_service.AdminCouponNotFoundError)
        else status.HTTP_422_UNPROCESSABLE_ENTITY
    )
    return HTTPException(status_code=status_code, detail=str(exc))


@router.get("", response_model=AdminCouponListResponse, dependencies=[Depends(require_admin_permission("coupon:view"))])
async def list_coupons(
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    type: str | None = None,
    scope: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> AdminCouponListResponse:
    return await admin_coupon_service.list_coupons(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        type=type,
        scope=scope,
        is_active=is_active,
    )


@router.post(
    "",
    response_model=AdminCouponResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_permission("coupon:create"))],
)
async def create_coupon(data: AdminCouponCreate, db: AsyncSession = Depends(get_db)) -> AdminCouponResponse:
    try:
        return await admin_coupon_service.create_coupon(db, data.model_dump())
    except admin_coupon_service.AdminCouponError as exc:
        raise _service_error(exc) from exc


@router.get("/{coupon_id}", response_model=AdminCouponResponse, dependencies=[Depends(require_admin_permission("coupon:view"))])
async def get_coupon(coupon_id: int, db: AsyncSession = Depends(get_db)) -> AdminCouponResponse:
    coupon = await admin_coupon_service.get_coupon(db, coupon_id)
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="卡券不存在")
    return coupon


@router.put("/{coupon_id}", response_model=AdminCouponResponse, dependencies=[Depends(require_admin_permission("coupon:update"))])
async def update_coupon(coupon_id: int, data: AdminCouponUpdate, db: AsyncSession = Depends(get_db)) -> AdminCouponResponse:
    try:
        return await admin_coupon_service.update_coupon(db, coupon_id, data.model_dump(exclude_unset=True))
    except admin_coupon_service.AdminCouponError as exc:
        raise _service_error(exc) from exc


@router.patch("/{coupon_id}/status", response_model=AdminCouponResponse, dependencies=[Depends(require_admin_permission("coupon:update"))])
async def toggle_coupon_status(
    coupon_id: int,
    data: AdminCouponStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> AdminCouponResponse:
    try:
        return await admin_coupon_service.toggle_status(db, coupon_id, data.is_active)
    except admin_coupon_service.AdminCouponError as exc:
        raise _service_error(exc) from exc


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_permission("coupon:delete"))])
async def delete_coupon(coupon_id: int, db: AsyncSession = Depends(get_db)) -> None:
    try:
        await admin_coupon_service.delete_coupon(db, coupon_id)
    except admin_coupon_service.AdminCouponError as exc:
        raise _service_error(exc) from exc
