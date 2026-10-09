import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.config import settings
from app.core.database import get_db
from app.core.im import gen_user_sig
from app.models.user import User

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.get("/user-sig")
async def get_user_sig(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Return IM SDKAppID, userID and UserSig for the current user."""
    if not settings.IM_SDK_APP_ID or not settings.IM_SERVER_KEY:
        raise HTTPException(status_code=503, detail="IM service not configured")

    result = await db.execute(select(User.username).where(User.id == user_id))
    username = result.scalar_one_or_none()
    if not username:
        raise HTTPException(status_code=400, detail="User has no username")

    user_sig = gen_user_sig(username)
    return {
        "sdk_app_id": settings.IM_SDK_APP_ID,
        "user_id": username,
        "user_sig": user_sig,
    }


@router.get("/publisher-username")
async def get_publisher_username(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return the publisher's username (IM userID) for a given listing."""
    from app.models.edu_listing import EduListing

    result = await db.execute(
        select(User.username)
        .join(EduListing, EduListing.user_id == User.id)
        .where(EduListing.id == listing_id)
    )
    username = result.scalar_one_or_none()
    if not username:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return {"publisher_username": username}
