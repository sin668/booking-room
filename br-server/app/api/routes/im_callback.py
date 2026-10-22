"""腾讯云 IM 第三方回调接收端。

由腾讯云服务端调用，无登录态：靠 URL 上的 SdkAppid + Sign 判定来源。
腾讯云要求 2s 内响应，因此这里只解析入队，落库与媒体转存放在响应后的后台任务里完成。
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Query, Request

from app.core.database import async_session
from app.core.im import verify_callback_sign
from app.services.im_callback_service import (
    apply_msg_report,
    media_kind_for,
    save_send_msg_callback,
)
from app.services.im_media_service import fetch_and_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/im", tags=["im"])

CALLBACK_OK = {"ActionStatus": "OK", "ErrorInfo": "", "ErrorCode": 0}


async def _persist_send_msg(payload: dict[str, Any]) -> None:
    try:
        async with async_session() as session:
            record = await save_send_msg_callback(session, payload)
            kind = media_kind_for(record) if record else None
            if kind:
                oss_url = await fetch_and_upload(kind, record.media_url)
                if oss_url:
                    record.oss_url = oss_url
            await session.commit()
    except Exception:
        logger.exception("IM callback AfterSendMsg persist failed: %s", payload.get("MsgKey"))


async def _persist_msg_report(payload: dict[str, Any]) -> None:
    try:
        async with async_session() as session:
            await apply_msg_report(session, payload)
            await session.commit()
    except Exception:
        logger.exception("IM callback AfterMsgReport persist failed: %s", payload.get("Report_Account"))


@router.post("/callback")
async def im_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    sdk_appid: str | None = Query(default=None, alias="SdkAppid"),
    sign: str | None = Query(default=None, alias="Sign"),
    request_time: str | None = Query(default=None, alias="RequestTime"),
) -> dict[str, Any]:
    """URL 参数：SdkAppid / Sign / RequestTime / CallbackCommand。"""
    query = request.query_params
    if not verify_callback_sign(sdk_appid, request_time, sign):
        logger.warning("IM callback rejected: sdkappid=%s sign_present=%s", sdk_appid, bool(sign))
        return CALLBACK_OK

    try:
        body = await request.json()
    except Exception:
        logger.warning("IM callback body is not JSON from %s", query.get("CallbackCommand"))
        return CALLBACK_OK

    command = body.get("CallbackCommand") or query.get("CallbackCommand") or ""
    if command == "C2C.CallbackAfterSendMsg":
        background_tasks.add_task(_persist_send_msg, body)
    elif command == "C2C.CallbackAfterMsgReport":
        background_tasks.add_task(_persist_msg_report, body)
    elif command:
        logger.info("IM callback ignored (unsupported command): %s", command)

    return CALLBACK_OK
