import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin, get_current_user_id
from app.core.database import get_db
from app.schemas.booking_verification import (
    BookingVerificationConfirmResponse,
    BookingVerificationDetailResponse,
    BookingVerificationTokenResponse,
)
from app.services import booking_verification_service

router = APIRouter(prefix="/api/v1/booking-verifications", tags=["booking-verifications"])


@router.post("/token", response_model=BookingVerificationTokenResponse)
async def issue_verification_token(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> BookingVerificationTokenResponse:
    try:
        return await booking_verification_service.issue_verification_token(
            db,
            user_id,
        )
    except booking_verification_service.NoVerifiableBookingError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="暂无可核销预约")
    except booking_verification_service.VerificationTokenConfigurationError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="核销码服务未配置")


@router.get("/{token}", response_model=BookingVerificationDetailResponse)
async def inspect_verification_token(
    token: str,
    db: AsyncSession = Depends(get_db),
    _admin: None = Depends(get_current_admin),
) -> BookingVerificationDetailResponse:
    try:
        return await booking_verification_service.inspect_verification_token(db, token)
    except booking_verification_service.ExpiredVerificationTokenError:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="核销码已过期")
    except booking_verification_service.InvalidVerificationTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的核销码")
    except booking_verification_service.NoVerifiableBookingError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="暂无可核销预约")
    except booking_verification_service.VerificationTokenConfigurationError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="核销码服务未配置")


@router.post("/{token}/confirm", response_model=BookingVerificationConfirmResponse)
async def confirm_verification(
    token: str,
    db: AsyncSession = Depends(get_db),
    _admin: None = Depends(get_current_admin),
) -> BookingVerificationConfirmResponse:
    try:
        return await booking_verification_service.confirm_verification(db, token)
    except booking_verification_service.ExpiredVerificationTokenError:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="核销码已过期")
    except booking_verification_service.InvalidVerificationTokenError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的核销码")
    except booking_verification_service.NoVerifiableBookingError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="暂无可核销预约")
    except booking_verification_service.BookingAlreadyVerifiedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="预约已核销")
    except booking_verification_service.BookingNotVerifiableError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="预约状态不可核销")
    except booking_verification_service.VerificationTokenConfigurationError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="核销码服务未配置")
