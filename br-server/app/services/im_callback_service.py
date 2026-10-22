"""腾讯云 IM 第三方回调解析与落库。

只处理服务端回调（C2C.CallbackAfterSendMsg / C2C.CallbackAfterMsgReport），
客户端不做上报，避免两套写入来源。回调体字段参考官方文档 269/2716 与 269/61696。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.im import from_im_user_id
from app.models.im_message import ImMessage

logger = logging.getLogger(__name__)

_ELEMENT_TYPES = {
    "TIMTextElem": "text",
    "TIMImageElem": "image",
    "TIMSoundElem": "sound",
    "TIMFileElem": "file",
    "TIMVideoElem": "video",
    "TIMFaceElem": "face",
    "TIMCustomElem": "custom",
}
# 仅这两类媒体需要转存 OSS（用户确认的范围）
_MEDIA_KINDS = {"image": "image", "sound": "audio"}


@dataclass(frozen=True)
class ParsedMessage:
    element_type: str
    content: str | None
    media_url: str | None


def parse_message(msg_body: list[dict[str, Any]] | None) -> ParsedMessage:
    """取第一个消息元素决定类型与内容；未知类型只存 JSON 摘要。"""
    for element in msg_body or []:
        msg_type = element.get("MsgType") or ""
        element_type = _ELEMENT_TYPES.get(msg_type, "other")
        content = element.get("MsgContent") or {}

        if element_type == "text":
            return ParsedMessage("text", content.get("Text") or None, None)
        if element_type == "image":
            return ParsedMessage("image", None, _image_url(content))
        if element_type == "sound":
            # 注意语音地址字段是 Url（小写 r）
            return ParsedMessage(
                "sound",
                str(content["Second"]) if content.get("Second") else None,
                content.get("Url") or None,
            )
        if element_type == "other":
            continue
        return ParsedMessage(element_type, json.dumps(content, ensure_ascii=False), None)

    return ParsedMessage("other", None, None)


def _image_url(content: dict[str, Any]) -> str | None:
    """优先取原图（Type==1），没有则取第一张。"""
    info_array = content.get("ImageInfoArray") or []
    for info in info_array:
        if info.get("Type") == 1 and info.get("URL"):
            return info["URL"]
    for info in info_array:
        if info.get("URL"):
            return info["URL"]
    return None


async def save_send_msg_callback(session: AsyncSession, payload: dict[str, Any]) -> ImMessage | None:
    """C2C.CallbackAfterSendMsg 落库，按 msg_key 幂等。返回新写入的记录。"""
    msg_key = payload.get("MsgKey")
    from_account = payload.get("From_Account")
    to_account = payload.get("To_Account")
    if not (msg_key and from_account and to_account):
        logger.warning("IM callback AfterSendMsg missing keys: %s", msg_key)
        return None

    # SendMsgResult 非 0 表示消息发送失败，不入库
    if payload.get("SendMsgResult", 0) != 0:
        return None

    existing = await session.execute(select(ImMessage.id).where(ImMessage.msg_key == msg_key))
    if existing.scalar_one_or_none() is not None:
        return None

    parsed = parse_message(payload.get("MsgBody"))
    record = ImMessage(
        msg_key=msg_key,
        im_from_account=from_account,
        im_to_account=to_account,
        from_user_id=from_im_user_id(from_account),
        to_user_id=from_im_user_id(to_account),
        msg_seq=payload.get("MsgSeq"),
        msg_time=int(payload.get("MsgTime") or 0),
        element_type=parsed.element_type,
        content=parsed.content,
        media_url=parsed.media_url,
        raw_payload={"MsgBody": payload.get("MsgBody") or []},
    )
    session.add(record)
    await session.flush()
    return record


def media_kind_for(record: ImMessage) -> str | None:
    """需要转存 OSS 的媒体类型；非媒体消息或无地址返回 None。"""
    if record.media_url and record.element_type in _MEDIA_KINDS:
        return _MEDIA_KINDS[record.element_type]
    return None


async def apply_msg_report(session: AsyncSession, payload: dict[str, Any]) -> int:
    """C2C.CallbackAfterMsgReport 回写已读：对端在 LastReadTime 之前发给我的消息置为已读。"""
    report_account = payload.get("Report_Account")
    peer_account = payload.get("Peer_Account")
    last_read_time = int(payload.get("LastReadTime") or 0)
    if not (report_account and peer_account and last_read_time):
        return 0

    result = await session.execute(
        update(ImMessage)
        .where(
            ImMessage.im_from_account == peer_account,
            ImMessage.im_to_account == report_account,
            ImMessage.msg_time <= last_read_time,
            ImMessage.is_read.is_(False),
        )
        .values(is_read=True, read_at=func.now())
    )
    return int(result.rowcount or 0)
