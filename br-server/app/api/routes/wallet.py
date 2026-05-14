from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_db, get_redis
from app.core.config import settings
from app.schemas.wallet import (
    BalanceResponse,
    PromoCodeRequest,
    PromoCodeResponse,
    RechargeRequest,
    RechargeResponse,
)
from app.services.wallet_service import (
    InvalidPromoCodeError,
    OrderAlreadyProcessedError,
    OrderNotFoundError,
    UserNotFoundError,
    WalletService,
)

router = APIRouter(prefix="/api/v1/wallet", tags=["wallet"])


@router.post(
    "/recharge",
    response_model=RechargeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recharge(
    body: RechargeRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> RechargeResponse:
    service = WalletService(db=db, redis=redis, config=settings)
    try:
        return await service.create_recharge_order(
            user_id=user_id,
            amount=body.amount,
            payment_method=body.payment_method,
            promo_code=body.promo_code,
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)
    except InvalidPromoCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.detail,
        )


@router.post("/recharge/{order_id}/confirm", response_model=RechargeResponse)
async def confirm_recharge(
    order_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> RechargeResponse:
    service = WalletService(db=db, redis=redis, config=settings)
    try:
        return await service.confirm_payment(order_id=order_id, user_id=user_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)
    except OrderAlreadyProcessedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail)


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> BalanceResponse:
    service = WalletService(db=db, redis=redis, config=settings)
    try:
        return await service.get_balance(user_id=user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.post("/promo-code", response_model=PromoCodeResponse)
async def redeem_promo_code(
    body: PromoCodeRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> PromoCodeResponse:
    service = WalletService(db=db, redis=redis, config=settings)
    try:
        return await service.redeem_promo_code(code=body.code)
    except InvalidPromoCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.detail,
        )
