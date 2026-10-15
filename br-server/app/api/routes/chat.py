import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.config import settings
from app.core.database import get_db
from app.core.im import gen_user_sig, to_im_user_id
from app.models.user import User

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.get("/user-sig")
async def get_user_sig(
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Return IM SDKAppID, userID and UserSig for the current user."""
    if not settings.IM_SDK_APP_ID or not settings.IM_SERVER_KEY:
        raise HTTPException(status_code=503, detail="IM service not configured")

    im_user_id = to_im_user_id(user_id)
    user_sig = gen_user_sig(im_user_id)
    return {
        "sdk_app_id": settings.IM_SDK_APP_ID,
        "user_id": im_user_id,
        "user_sig": user_sig,
    }


@router.get("/publisher-username")
async def get_publisher_username(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return the publisher's IM user ID for a given listing."""
    from app.models.edu_listing import EduListing

    result = await db.execute(
        select(User.id)
        .join(EduListing, EduListing.user_id == User.id)
        .where(EduListing.id == listing_id)
    )
    publisher_id = result.scalar_one_or_none()
    if not publisher_id:
        raise HTTPException(status_code=404, detail="Publisher not found")
    return {"publisher_im_user_id": to_im_user_id(publisher_id)}
