import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.config import settings
from app.core.database import get_db
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.user import User
from app.schemas.booking import (
    BookingCreate,
    BookingListResponse,
    BookingResponse,
    CreateBookingResponse,
    PayPendingBooking,
    PaymentMethodEnum,
    PaymentStatusResponse,
)
from app.services import booking_service
from app.services.booking_payment_service import (
    BookingPaymentAlreadyProcessedError,
    BookingPaymentNotFoundError,
    BookingPaymentService,
    BookingPaymentSignatureError,
    InvalidBookingPaymentCallbackError,
    PaymentProviderUnavailableError,
    WechatOpenIdRequiredError,
)
from app.services.wechat_pay_client import WechatPayClient

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])

_BOOKING_STATUS = Literal["confirmed", "cancelled", "completed"]


def _build_wechat_client():
    if not getattr(settings, "WECHAT_PAY_ENABLED", False):
        return None
    return WechatPayClient(settings)


def _payment_service(db: AsyncSession) -> BookingPaymentService:
    return BookingPaymentService(db, wechat_client=_build_wechat_client())


def _notify_failure(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": "FAIL", "message": message},
    )


@router.post("", response_model=CreateBookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CreateBookingResponse:
    try:
        response = await booking_service.create_booking(db, user_id, data)
        if data.payment_method != PaymentMethodEnum.wechat:
            return CreateBookingResponse.model_validate(response.model_dump())

        user = await db.get(User, user_id)
        if user is None:
            raise booking_service.BookingError("User not found")
        booking = await db.get(Booking, response.id)
        if booking is None:
            raise booking_service.BookingError("Booking not found")
        payment_params = await _payment_service(db).create_booking_payment(booking, user)
        response = booking_service._build_booking_response(
            booking,
            await db.get(Seat, booking.seat_id),
            await db.get(StudyRoom, booking.room_id),
        )
        return CreateBookingResponse.model_validate(
            {**response.model_dump(), "payment_params": payment_params}
        )
    except booking_service.SeatNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="座位不存在")
    except booking_service.SeatMaintenanceError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该座位正在维护中")
    except booking_service.BookingConflictError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该座位该时段已被预约")
    except booking_service.WalletBalanceInsufficientError:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Wallet balance is insufficient",
        )
    except booking_service.InvalidTimeRangeError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="结束时间必须晚于开始时间")
    except booking_service.BookingCouponUnavailableError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="卡券不可用，请重新选择")
    except WechatOpenIdRequiredError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except PaymentProviderUnavailableError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
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


@router.post("/wechat/notify")
async def wechat_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    headers = {key: value for key, value in request.headers.items()}
    body = await request.body()
    try:
        return await _payment_service(db).process_wechat_notify(
            headers=headers,
            body=body,
        )
    except PaymentProviderUnavailableError as exc:
        return _notify_failure(status.HTTP_503_SERVICE_UNAVAILABLE, exc.detail)
    except BookingPaymentSignatureError as exc:
        return _notify_failure(status.HTTP_401_UNAUTHORIZED, exc.detail)
    except InvalidBookingPaymentCallbackError as exc:
        return _notify_failure(status.HTTP_400_BAD_REQUEST, exc.detail)
    except BookingPaymentNotFoundError as exc:
        return _notify_failure(status.HTTP_404_NOT_FOUND, exc.detail)
    except BookingPaymentAlreadyProcessedError as exc:
        return _notify_failure(status.HTTP_400_BAD_REQUEST, exc.detail)


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


@router.get("/{booking_id}/payment-status", response_model=PaymentStatusResponse)
async def get_payment_status(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> PaymentStatusResponse:
    try:
        return await _payment_service(db).query_payment_status(booking_id, user_id)
    except BookingPaymentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")


@router.post("/{booking_id}/pay", response_model=CreateBookingResponse)
async def pay_pending_booking_route(
    booking_id: int,
    data: PayPendingBooking,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CreateBookingResponse:
    try:
        if data.payment_method == PaymentMethodEnum.wechat:
            booking = await db.get(Booking, booking_id)
            if booking is None:
                raise booking_service.BookingNotFoundError("预约不存在")
            user = await db.get(User, user_id)
            if user is None:
                raise booking_service.BookingError("User not found")
            payment_params = await _payment_service(db).create_booking_payment(booking, user)
            response = await booking_service.pay_pending_booking(
                db, booking_id, user_id, data.payment_method,
                wechat_payment_params=payment_params,
            )
        else:
            response = await booking_service.pay_pending_booking(
                db, booking_id, user_id, data.payment_method,
            )
        return CreateBookingResponse.model_validate(response.model_dump())
    except booking_service.BookingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    except booking_service.WalletBalanceInsufficientError:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Wallet balance is insufficient",
        )
    except WechatOpenIdRequiredError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except PaymentProviderUnavailableError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except booking_service.BookingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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
    except booking_service.BookingCancellationNotAllowedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except booking_service.BookingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
