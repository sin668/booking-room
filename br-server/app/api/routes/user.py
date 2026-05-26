import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.services.user_profile_service import UserProfileService, UsernameCooldownError

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
