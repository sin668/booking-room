# -*- coding: utf-8 -*-
"""
迁移脚本：把存量用户的 IM 账号 UserID 从 username 换成 users.id 派生值。

IM UserID 不可修改，所以这里只能按新 ID 重新导入账号。旧 ID（username）对应的
账号默认保留，确认新账号可用后用 --delete-old 清理（会连带删除该账号的 IM 聊天记录）。

使用方式：
    cd br-server && conda activate booking-room
    python scripts/migrate_im_user_ids.py --dry-run      # 只列出将要做的事，不碰 IM
    python scripts/migrate_im_user_ids.py               # 按新 ID 导入
    python scripts/migrate_im_user_ids.py --delete-old  # 导入后删除旧 username 账号
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.core.im import to_im_user_id
from app.models.user import User
from app.services.im_sync_service import IMSyncService


async def main(dry_run: bool, delete_old: bool) -> int:
    if not dry_run:
        if not (settings.IM_SDK_APP_ID and settings.IM_SERVER_KEY and settings.IM_ADMIN_USER):
            print("IM 服务端同步未配置（IM_SDK_APP_ID / IM_SERVER_KEY / IM_ADMIN_USER），请检查 .env")
            return 1

    async with async_session() as db:
        users = (
            await db.execute(
                select(User).where(User.status != "deleted").order_by(User.created_at)
            )
        ).scalars().all()

    print(f"共 {len(users)} 个未注销用户")

    imported = failed = 0
    for index, user in enumerate(users, start=1):
        im_user_id = to_im_user_id(user.id)
        nickname = user.nickname or ""
        avatar_url = user.avatar or ""

        if dry_run:
            print(
                f"[{index}/{len(users)}] {im_user_id} "
                f"(username={user.username}, nickname={nickname}, avatar={bool(avatar_url)})"
            )
            continue

        ok = await IMSyncService.import_account(im_user_id, nickname, avatar_url)
        if ok:
            imported += 1
        else:
            failed += 1
            print(f"[{index}/{len(users)}] 导入失败: {im_user_id} (username={user.username})")

        if delete_old and ok and user.username:
            await IMSyncService.delete_account(user.username)

        await asyncio.sleep(0.1)

    if dry_run:
        print("dry-run 结束，未调用 IM 接口")
    else:
        print(f"导入成功 {imported}，失败 {failed}，旧账号清理={delete_old}")

    return 0 if failed == 0 else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="迁移存量用户 IM 账号到 users.id 派生 UserID")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不调用 IM 接口")
    parser.add_argument(
        "--delete-old",
        action="store_true",
        help="导入成功后删除旧 username 对应的 IM 账号（会丢失该账号聊天记录）",
    )
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.dry_run, args.delete_old)))
