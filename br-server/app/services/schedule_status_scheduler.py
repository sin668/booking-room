"""排课状态定时任务

定时扫描课程排课列表中状态为"进行中"（in_progress）的排课记录：
- 当前日期 > 课程结束日期（end_date）→ schedule_status 变更为 completed（已完成）

默认每天 00:00（Asia/Shanghai）运行一次，运行时间由
settings.SCHEDULE_STATUS_CHECK_TIME 配置（格式 "HH:MM"）。
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.models.course_schedule import CourseSchedule
from app.core.database import async_session
from app.core.config import settings

logger = logging.getLogger(__name__)


async def check_and_update_schedule_statuses() -> dict:
    """
    定时扫描"进行中"的排课记录，将当前日期已超过结课日期的记录标记为已完成。

    返回: {"total_scanned": N, "schedule_completed": N}
    """
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    today = now.date()

    stats = {
        "total_scanned": 0,
        "schedule_completed": 0,
    }

    async with async_session() as session:
        # 只扫描进行中的排课记录（已完成的无需重复处理）
        result = await session.execute(
            select(CourseSchedule).where(CourseSchedule.schedule_status == "in_progress")
        )
        schedules = result.scalars().all()
        stats["total_scanned"] = len(schedules)

        if settings.SCHEDULER_LOG_ENABLED:
            logger.info(
                "[排课状态定时任务] 开始扫描：共 %d 条进行中排课记录，当前日期=%s",
                len(schedules), today,
            )

        for schedule in schedules:
            try:
                is_expired = schedule.end_date is not None and today > schedule.end_date
                if settings.SCHEDULER_LOG_ENABLED:
                    logger.info(
                        "[排课记录 %d] status=%s, end_date=%s | today=%s | end_cmp=%s",
                        schedule.id, schedule.schedule_status, schedule.end_date,
                        today,
                        "today > end_date" if is_expired else "today <= end_date 或无结课日期",
                    )

                if is_expired:
                    # 进行中 → 已完成
                    schedule.schedule_status = "completed"
                    stats["schedule_completed"] += 1
                    if settings.SCHEDULER_LOG_ENABLED:
                        logger.info(
                            "Course schedule %d: in_progress → completed (end_date=%s)",
                            schedule.id, schedule.end_date,
                        )
            except Exception:
                if settings.SCHEDULER_LOG_ENABLED:
                    logger.exception(f"Error processing schedule {schedule.id}")

        await session.commit()

    if settings.SCHEDULER_LOG_ENABLED:
        logger.info(
            "[排课状态定时任务] 扫描完成：共 %d 条进行中排课，标记完成 %d 条",
            stats["total_scanned"], stats["schedule_completed"],
        )

    return stats
