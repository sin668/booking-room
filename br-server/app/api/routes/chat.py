import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.config import settings
from app.core.database import get_db
from app.core.im import from_im_user_id, gen_user_sig, to_im_user_id
from app.models.im_message import ImMessage
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


@router.get("/messages")
async def get_chat_messages(
    peer: str,
    limit: int = Query(default=50, ge=1, le=200),
    before: int | None = Query(default=None, description="msg_time 游标（秒），取更早的一页"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """返回当前用户与 peer 之间的单聊历史（由 IM 服务端回调落库），按时间正序。"""
    if from_im_user_id(peer) is None:
        raise HTTPException(status_code=400, detail="peer 不是合法的会话对象")

    self_account = to_im_user_id(user_id)
    conditions = [
        or_(
            and_(
                ImMessage.im_from_account == self_account,
                ImMessage.im_to_account == peer,
            ),
            and_(
                ImMessage.im_from_account == peer,
                ImMessage.im_to_account == self_account,
            ),
        )
    ]
    if before is not None:
        conditions.append(ImMessage.msg_time < before)

    result = await db.execute(
        select(ImMessage)
        .where(*conditions)
        .order_by(ImMessage.msg_time.desc(), ImMessage.id.desc())
        .limit(limit)
    )
    rows = list(result.scalars().all())
    return {
        "messages": [
            {
                "id": row.id,
                "msg_key": row.msg_key,
                "element_type": row.element_type,
                "content": row.content,
                "media_url": row.media_url,
                "oss_url": row.oss_url,
                "is_read": row.is_read,
                "msg_time": row.msg_time,
                "direction": "send" if row.im_from_account == self_account else "receive",
            }
            for row in reversed(rows)
        ],
        "has_more": len(rows) == limit,
    }
