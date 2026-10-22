"""会话媒体转存对象存储。

下载回调里的 IM/COS 媒体地址，复用 app/services/upload_service.py 的存储适配器写入 OSS。
不改对外图片上传接口（scope 白名单与"仅支持图片"校验保持原样），
直接走 StorageAdapter 协议，所以语音也能复用同一套 OSS 配置。
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import PurePosixPath

import httpx

from app.services.upload_service import UploadObject, get_storage_adapter

logger = logging.getLogger(__name__)

MAX_MEDIA_BYTES = 10 * 1024 * 1024


class MediaTooLarge(Exception):
    """流式读取时超过大小上限，按转存失败降级处理。"""

_DEFAULT_EXT = {"image": ".jpg", "audio": ".mp3"}
_ALLOWED_EXTS = {
    "image": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
    "audio": {".mp3", ".wav", ".aac", ".m4a", ".amr"},
}
_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".aac": "audio/aac",
    ".m4a": "audio/mp4",
    ".amr": "audio/amr",
}


def _object_key(kind: str, ext: str) -> str:
    now = datetime.now()
    return f"chat/{kind}/{now:%Y/%m/%d}/{uuid.uuid4().hex}{ext}"


def _extension(kind: str, media_url: str) -> str:
    suffix = PurePosixPath(media_url.split("?")[0]).suffix.lower()
    return suffix if suffix in _ALLOWED_EXTS[kind] else _DEFAULT_EXT[kind]


async def fetch_and_upload(kind: str, media_url: str) -> str | None:
    """转存一条媒体，返回 OSS 公开地址；任何失败返回 None，由调用方保留 IM 原地址。"""
    try:
        data = await _download(media_url)
    except Exception as exc:
        # InvalidURL 等不属于 httpx.HTTPError，转存任何异常都不能影响已落库的消息
        logger.warning(
            "IM media download failed kind=%s error=%s url=%s", kind, type(exc).__name__, media_url[:120]
        )
        return None

    if not data:
        logger.warning("IM media skipped, empty: url=%s", media_url[:120])
        return None

    ext = _extension(kind, media_url)
    upload = UploadObject(
        content=data,
        object_key=_object_key(kind, ext),
        content_type=_CONTENT_TYPES[ext],
        size=len(data),
    )
    try:
        # oss2 是同步 SDK，放到线程里避免阻塞事件循环
        result = await asyncio.to_thread(get_storage_adapter().upload, upload)
    except Exception as exc:
        logger.warning("IM media OSS upload failed kind=%s error=%s", kind, type(exc).__name__)
        return None

    return result.url


async def _download(media_url: str, transport: httpx.AsyncBaseTransport | None = None) -> bytes:
    """流式下载并边读边限长，避免超大响应先占满内存。transport 仅用于测试注入。"""
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, transport=transport) as client:
        async with client.stream("GET", media_url) as response:
            response.raise_for_status()
            chunks: list[bytes] = []
            size = 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > MAX_MEDIA_BYTES:
                    raise MediaTooLarge(f"{size} bytes exceeds {MAX_MEDIA_BYTES}")
                chunks.append(chunk)
            return b"".join(chunks)
