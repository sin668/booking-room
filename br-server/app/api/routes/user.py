import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.core.redis import get_redis
from app.schemas.user import (
    AccountDeactivationResponse,
    AccountSecuritySummary,
    ChangePasswordRequest,
    ChangePasswordResponse,
    IdentityVerificationRequest,
    IdentityVerificationResponse,
    UserProfileResponse,
    UserProfileUpdate,
)
from app.core.config import settings
from app.services.user_profile_service import UserProfileService, UsernameCooldownError
from app.services.user_security_service import UserSecurityService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_me(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """Get the current authenticated user's info."""
    user = await UserProfileService(db).get_current_user(user_id)
    return UserProfileResponse.model_validate(user)


@router.patch("/me", response_model=UserProfileResponse)
async def update_me(
    data: UserProfileUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse | JSONResponse:
    """Update the current authenticated user's safe profile fields."""
    try:
        user = await UserProfileService(db).update_profile(user_id, data)
    except UsernameCooldownError as exc:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": exc.detail,
                "retry_after_seconds": exc.retry_after_seconds,
            },
        )
    return UserProfileResponse.model_validate(user)


@router.get("/me/security", response_model=AccountSecuritySummary)
async def get_account_security(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> AccountSecuritySummary:
    """Get current user's account security summary."""
    return await UserSecurityService(db, redis, settings).get_security_summary(user_id)


@router.post("/me/password", response_model=ChangePasswordResponse)
async def change_password(
    data: ChangePasswordRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> ChangePasswordResponse:
    """Change current user's password after validating the old password."""
    return await UserSecurityService(db, redis, settings).change_password(user_id, data)


@router.post("/me/identity-verification", response_model=IdentityVerificationResponse)
async def submit_identity_verification(
    data: IdentityVerificationRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> IdentityVerificationResponse:
    """Submit current user's real-name verification data."""
    return await UserSecurityService(db, redis, settings).submit_identity(user_id, data)


@router.post("/me/deactivation", response_model=AccountDeactivationResponse)
async def deactivate_account(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> AccountDeactivationResponse:
    """Logically delete current user's account after risk checks."""
    return await UserSecurityService(db, redis, settings).deactivate_account(user_id)
