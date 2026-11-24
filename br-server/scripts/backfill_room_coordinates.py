"""回填学习室存量地址的 GCJ-02 坐标。

对 study_rooms 中 latitude/longitude 为空、但 address 非空的房间调用腾讯位置服务
地理编码并写回。未配置 TENCENT_MAP_KEY 时不做任何写入。

用法：python scripts/backfill_room_coordinates.py [--dry-run] [--limit N]
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.models.city import City
from app.models.study_room import StudyRoom
from app.services.tencent_map_service import geocode_address

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def backfill(dry_run: bool, limit: int) -> tuple[int, int]:
    """返回 (成功数量, 跳过数量)。"""
    if not settings.TENCENT_MAP_KEY:
        raise SystemExit("TENCENT_MAP_KEY 未配置，无法执行地理编码回填")

    fixed = 0
    skipped = 0
    async with async_session() as session:
        result = await session.execute(
            select(StudyRoom, City.name.label("city_name"))
            .outerjoin(City, StudyRoom.city_id == City.id)
            .where(
                StudyRoom.latitude.is_(None),
                StudyRoom.longitude.is_(None),
                StudyRoom.address.is_not(None),
                StudyRoom.address != "",
            )
            .order_by(StudyRoom.id.asc())
            .limit(limit)
        )
        rows = result.all()

        for room, city_name in rows:
            coordinates = await geocode_address(room.address, city_name)
            if not coordinates:
                skipped += 1
                logger.warning("跳过 room_id=%s address=%s", room.id, room.address)
                continue

            latitude, longitude = coordinates
            logger.info(
                "room_id=%s address=%s -> (%s, %s)%s",
                room.id,
                room.address,
                latitude,
                longitude,
                " [dry-run]" if dry_run else "",
            )
            if not dry_run:
                room.latitude = latitude
                room.longitude = longitude
                await session.commit()
            fixed += 1

    return fixed, skipped


async def main() -> None:
    parser = argparse.ArgumentParser(description="回填学习室地址坐标")
    parser.add_argument("--dry-run", action="store_true", help="只打印结果，不写入数据库")
    parser.add_argument("--limit", type=int, default=100, help="最多处理房间数（默认 100）")
    args = parser.parse_args()

    fixed, skipped = await backfill(args.dry_run, args.limit)
    logger.info("回填完成：成功 %d，跳过 %d", fixed, skipped)


if __name__ == "__main__":
    asyncio.run(main())
