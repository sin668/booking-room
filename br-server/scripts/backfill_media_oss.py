"""回填历史消息的 OSS 地址。

对 im_messages 表中 oss_url 或 thumbnail_oss_url 为空的媒体消息，
重新下载并转存到 OSS。用于修复历史消息媒体无法显示的问题。

用法：python scripts/backfill_media_oss.py [--dry-run] [--limit N]
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# 让脚本可以从项目根目录运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.im_message import ImMessage
from app.services.im_media_service import fetch_and_upload

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def backfill(session: AsyncSession, dry_run: bool, limit: int) -> int:
    """回填媒体 OSS 地址，返回处理的消息数。"""
    # 找需要回填的消息：媒体类型且 oss_url 为空，或视频且 thumbnail_oss_url 为空
    result = await session.execute(
        select(ImMessage)
        .where(
            ImMessage.element_type.in_(["image", "video"]),
            (ImMessage.oss_url.is_(None)) | (ImMessage.oss_url == ""),
        )
        .limit(limit)
    )
    messages_to_fix = list(result.scalars().all())

    # 视频还需要检查 thumbnail_oss_url
    result2 = await session.execute(
        select(ImMessage)
        .where(
            ImMessage.element_type == "video",
            (ImMessage.thumbnail_oss_url.is_(None)) | (ImMessage.thumbnail_oss_url == ""),
        )
        .limit(limit)
    )
    videos_needing_thumb = list(result2.scalars().all())

    total = len(messages_to_fix) + len(videos_needing_thumb)
    if total == 0:
        logger.info("No messages need backfill")
        return 0

    logger.info("Found %d messages to backfill (%d media, %d video thumbnails)", total, len(messages_to_fix), len(videos_needing_thumb))

    if dry_run:
        for msg in messages_to_fix:
            logger.info("[DRY-RUN] Would backfill oss_url for msg_key=%s element_type=%s media_url=%s", msg.msg_key, msg.element_type, msg.media_url)
        for msg in videos_needing_thumb:
            # 从 raw_payload 取 ThumbUrl
            thumb_url = None
            if msg.raw_payload:
                msg_body = msg.raw_payload.get("MsgBody") or []
                if msg_body:
                    content = msg_body[0].get("MsgContent") or {}
                    thumb_url = content.get("ThumbUrl")
            logger.info("[DRY-RUN] Would backfill thumbnail_oss_url for msg_key=%s thumb_url=%s", msg.msg_key, thumb_url)
        return total

    # 回填 oss_url
    fixed = 0
    for msg in messages_to_fix:
        if not msg.media_url:
            continue
        kind = "image" if msg.element_type == "image" else "video"
        oss_url = await fetch_and_upload(kind, msg.media_url)
        if oss_url:
            await session.execute(
                update(ImMessage).where(ImMessage.id == msg.id).values(oss_url=oss_url)
            )
            await session.commit()
            fixed += 1
            logger.info("Fixed oss_url for msg_key=%s: %s", msg.msg_key, oss_url[:80])
        else:
            logger.warning("Failed to backfill oss_url for msg_key=%s", msg.msg_key)

    # 回填视频缩略图
    thumb_fixed = 0
    for msg in videos_needing_thumb:
        thumb_url = None
        if msg.raw_payload:
            msg_body = msg.raw_payload.get("MsgBody") or []
            if msg_body:
                content = msg_body[0].get("MsgContent") or {}
                thumb_url = content.get("ThumbUrl")
        if not thumb_url:
            continue
        thumb_oss_url = await fetch_and_upload("image", thumb_url)
        if thumb_oss_url:
            await session.execute(
                update(ImMessage).where(ImMessage.id == msg.id).values(thumbnail_oss_url=thumb_oss_url)
            )
            await session.commit()
            thumb_fixed += 1
            logger.info("Fixed thumbnail_oss_url for msg_key=%s: %s", msg.msg_key, thumb_oss_url[:80])
        else:
            logger.warning("Failed to backfill thumbnail_oss_url for msg_key=%s", msg.msg_key)

    logger.info("Backfill complete: fixed %d oss_url, %d thumbnail_oss_url", fixed, thumb_fixed)
    return fixed + thumb_fixed


async def main():
    parser = argparse.ArgumentParser(description="Backfill media OSS URLs for history messages")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--limit", type=int, default=100, help="Max messages to process (default: 100)")
    args = parser.parse_args()

    async with async_session() as session:
        count = await backfill(session, args.dry_run, args.limit)
        logger.info("Total processed: %d", count)


if __name__ == "__main__":
    asyncio.run(main())
