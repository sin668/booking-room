import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, func, or_, select
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
    peer_uuid = from_im_user_id(peer)
    if peer_uuid is None:
        raise HTTPException(status_code=400, detail="peer 不是合法的会话对象")
    # 库里存的是 uuid.hex（小写无连字符），先把入参归一成同一形态再比较
    peer_account = to_im_user_id(peer_uuid)

    self_account = to_im_user_id(user_id)
    conditions = [
        or_(
            and_(
                ImMessage.im_from_account == self_account,
                ImMessage.im_to_account == peer_account,
            ),
            and_(
                ImMessage.im_from_account == peer_account,
                ImMessage.im_to_account == self_account,
            ),
        )
    ]
    if before is not None:
        conditions.append(ImMessage.msg_time < before)

    result = await db.execute(
        select(ImMessage)
        .where(*conditions)
        # 与 IM 单聊排序口径一致：先按秒级 MsgTime，同秒再按 MsgSeq
        .order_by(
            ImMessage.msg_time.desc(),
            ImMessage.msg_seq.desc(),
            ImMessage.id.desc(),
        )
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
                "thumbnail_oss_url": row.thumbnail_oss_url,
                "elements": (row.raw_payload or {}).get("MsgBody") or [],
                "cloud_custom_data": row.cloud_custom_data,
                "is_revoked": row.is_revoked,
                "msg_seq": row.msg_seq,
                "im_from_account": row.im_from_account,
                "im_to_account": row.im_to_account,
                "is_read": row.is_read,
                "msg_time": row.msg_time,
                "direction": "send" if row.im_from_account == self_account else "receive",
            }
            for row in reversed(rows)
        ],
        "has_more": len(rows) == limit,
    }


@router.get("/conversations")
async def get_conversation_list(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """返回当前用户的所有会话（从 DB 聚合），用于补齐 SDK 7 天漫游之外的历史会话。

    返回每个会话对象的最后一条消息时间、摘要和对端用户信息。
    """
    self_account = to_im_user_id(user_id)

    # 取所有与当前用户有消息往来的对端账号
    result = await db.execute(
        select(
            func.distinct(
                case(
                    (ImMessage.im_from_account == self_account, ImMessage.im_to_account),
                    else_=ImMessage.im_from_account,
                )
            ).label("peer_account")
        )
        .where(
            or_(
                ImMessage.im_from_account == self_account,
                ImMessage.im_to_account == self_account,
            )
        )
    )
    peer_accounts = [row.peer_account for row in result]

    if not peer_accounts:
        return {"conversations": []}

    # 为每个对端取最新消息时间和用户信息
    conversations = []
    for peer_account in peer_accounts:
        # 取最新消息时间
        time_result = await db.execute(
            select(func.max(ImMessage.msg_time))
            .where(
                or_(
                    and_(
                        ImMessage.im_from_account == self_account,
                        ImMessage.im_to_account == peer_account,
                    ),
                    and_(
                        ImMessage.im_from_account == peer_account,
                        ImMessage.im_to_account == self_account,
                    ),
                )
            )
        )
        last_msg_time = time_result.scalar()

        # 取最后一条消息用于摘要
        msg_result = await db.execute(
            select(ImMessage.element_type, ImMessage.content)
            .where(
                or_(
                    and_(
                        ImMessage.im_from_account == self_account,
                        ImMessage.im_to_account == peer_account,
                    ),
                    and_(
                        ImMessage.im_from_account == peer_account,
                        ImMessage.im_to_account == self_account,
                    ),
                )
            )
            .order_by(ImMessage.msg_time.desc(), ImMessage.msg_seq.desc())
            .limit(1)
        )
        last_msg = msg_result.first()

        # 取对端用户信息
        peer_uuid = from_im_user_id(peer_account)
        user_result = await db.execute(
            select(User.nickname, User.avatar)
            .where(User.id == peer_uuid)
            if peer_uuid else select(User.nickname, User.avatar).where(False)
        )
        user_row = user_result.first()

        summary = _format_summary(last_msg.element_type if last_msg else None, last_msg.content if last_msg else None)
        conversations.append({
            "peer_im_account": peer_account,
            "peer_user_id": str(peer_uuid) if peer_uuid else None,
            "last_msg_time": last_msg_time,
            "summary": summary,
            "name": user_row.nickname if user_row else (str(peer_uuid)[:8] if peer_uuid else peer_account),
            "avatar": user_row.avatar if user_row else "",
        })

    # 按最后消息时间降序排序
    conversations.sort(key=lambda x: x["last_msg_time"] or 0, reverse=True)
    return {"conversations": conversations}


def _format_summary(element_type: str | None, content: str | None) -> str:
    """把最后一条消息格式化成会话列表摘要。"""
    if not element_type:
        return ""
    if element_type == "text":
        return content or ""
    if element_type == "image":
        return "[图片]"
    if element_type == "sound":
        return "[语音]"
    if element_type == "video":
        return "[视频]"
    if element_type == "file":
        return "[文件]"
    if element_type == "face":
        return "[表情]"
    if element_type == "custom":
        return "[自定义消息]"
    return ""

