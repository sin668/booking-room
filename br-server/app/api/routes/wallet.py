from typing import cast, get_args
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_db, get_redis
from app.core.config import settings
from app.schemas.wallet import (
    BalanceResponse,
    PromoCodeRequest,
    PromoCodeResponse,
    RechargeRequest,
    RechargeOrderResponse,
    RechargeResponse,
    WalletTransactionListResponse,
    WalletTransactionType,
)
from app.services.wallet_service import (
    InvalidPaymentCallbackError,
    InvalidPromoCodeError,
    OrderAlreadyProcessedError,
    OrderNotFoundError,
    PaymentProviderUnavailableError,
    PaymentSignatureError,
    SimulatedPaymentDisabledError,
    UnsupportedPaymentMethodError,
    UserNotFoundError,
    WalletService,
    WechatOpenIdRequiredError,
)

from app.services.wechat_pay_client import WechatPayClient


router = APIRouter(prefix="/api/v1/wallet", tags=["wallet"])


def _build_wechat_client():
    if not getattr(settings, "WECHAT_PAY_ENABLED", False):
        return None
    return WechatPayClient(settings)


def _service(db: AsyncSession, redis) -> WalletService:
    return WalletService(
        db=db,
        redis=redis,
        config=settings,
        wechat_client=_build_wechat_client(),
    )


def _notify_failure(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": "FAIL", "message": message},
    )


_TRANSACTION_TYPES = set(get_args(WalletTransactionType))


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
):
    service = _service(db, redis)
    try:
        return await service.create_recharge_order(
            user_id=user_id,
            amount=body.amount,
            payment_method=body.payment_method,
            promo_code=body.promo_code,
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)
    except (InvalidPromoCodeError, UnsupportedPaymentMethodError, WechatOpenIdRequiredError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.detail,
        )
    except PaymentProviderUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.detail,
        )


@router.get("/recharge/{order_id}", response_model=RechargeOrderResponse)
async def get_recharge_order(
    order_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    service = _service(db, redis)
    try:
        return await service.get_recharge_order(order_id=order_id, user_id=user_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)


@router.get("/transactions", response_model=WalletTransactionListResponse)
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    type: str = Query("all"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> WalletTransactionListResponse:
    if type not in _TRANSACTION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported wallet transaction type",
        )

    service = _service(db, redis)
    return await service.list_transactions(
        user_id=user_id,
        page=page,
        page_size=page_size,
        type=cast(WalletTransactionType, type),
    )


@router.post("/wechat/notify")
async def wechat_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    service = _service(db, redis)
    headers = {key: value for key, value in request.headers.items()}
    body = await request.body()
    try:
        return await service.handle_wechat_notify(headers=headers, body=body)
    except PaymentProviderUnavailableError as exc:
        return _notify_failure(status.HTTP_503_SERVICE_UNAVAILABLE, exc.detail)
    except PaymentSignatureError as exc:
        return _notify_failure(status.HTTP_401_UNAUTHORIZED, exc.detail)
    except InvalidPaymentCallbackError as exc:
        return _notify_failure(status.HTTP_400_BAD_REQUEST, exc.detail)
    except OrderNotFoundError as exc:
        return _notify_failure(status.HTTP_404_NOT_FOUND, exc.detail)
    except OrderAlreadyProcessedError as exc:
        return _notify_failure(status.HTTP_400_BAD_REQUEST, exc.detail)


@router.post("/recharge/{order_id}/confirm", response_model=RechargeResponse)
async def confirm_recharge(
    order_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> RechargeResponse:
    service = _service(db, redis)
    try:
        return await service.confirm_payment(order_id=order_id, user_id=user_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)
    except SimulatedPaymentDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.detail)
    except OrderAlreadyProcessedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail)


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> BalanceResponse:
    service = _service(db, redis)
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
    service = _service(db, redis)
    try:
        return await service.redeem_promo_code(code=body.code)
    except InvalidPromoCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.detail,
        )
