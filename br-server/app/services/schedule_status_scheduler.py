"""排课状态定时任务

定时扫描课程排课列表并按当前日期推进 schedule_status：
- pending_start（待开始）：今天 >= 开课日期(start_date) → in_progress（进行中）
- in_progress（进行中）：今天 > 结课日期(end_date) → completed（已完成）

默认每天 00:00（Asia/Shanghai）运行一次，运行时间由
settings.SCHEDULE_STATUS_CHECK_TIME 配置（格式 "HH:MM"）。

状态推进复用订单域公用方法 resolve_course_transition（与 order_status_scheduler、
预约确认同源）：排课 start_date 对应第一课时日期、end_date 对应结课日期，
保证排课域 pending_start/in_progress/completed 语义与订单域完全一致。
"""
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session
from app.domain.booking_status import BookingStatus, resolve_course_transition
from app.models.course_schedule import CourseSchedule

logger = logging.getLogger(__name__)


async def _update_schedule_statuses(session: AsyncSession, today: date) -> dict:
    """扫描 pending_start / in_progress 排课并按 today 推进状态（不 commit，由调用方决定）。

    状态推进复用订单域公用纯函数 resolve_course_transition：
    - pending_start 且 today >= start_date → in_progress
    - in_progress 且 today > end_date → completed
    - completed 不在扫描范围（无需重复处理）

    可注入 session 与 today，便于确定性测试。

    返回: {"total_scanned": N, "schedule_started": N, "schedule_completed": N}
    """
    stats = {
        "total_scanned": 0,
        "schedule_started": 0,
        "schedule_completed": 0,
    }

    result = await session.execute(
        select(CourseSchedule).where(
            CourseSchedule.schedule_status.in_(
                [BookingStatus.PENDING_START.value, BookingStatus.IN_PROGRESS.value]
            )
        )
    )
    schedules = result.scalars().all()
    stats["total_scanned"] = len(schedules)

    for schedule in schedules:
        try:
            # 复用订单域状态转换纯函数（与 order_status_scheduler 同源）：
            # 排课 start_date ↔ 第一课时日期、end_date ↔ 结课日期
            transition = resolve_course_transition(
                status=BookingStatus(schedule.schedule_status),
                today=today,
                first_lesson_date=schedule.start_date,
                last_lesson_date=schedule.end_date,
            )
            if transition.new_status is None:
                continue
            schedule.schedule_status = transition.new_status.value
            if transition.new_status == BookingStatus.IN_PROGRESS:
                stats["schedule_started"] += 1
            elif transition.new_status == BookingStatus.COMPLETED:
                stats["schedule_completed"] += 1
        except Exception:
            if settings.SCHEDULER_LOG_ENABLED:
                logger.exception("Error processing schedule %s", schedule.id)

    return stats


async def check_and_update_schedule_statuses() -> dict:
    """定时扫描并推进排课状态：pending_start → in_progress → completed。

    仅负责取当前日期、执行推进与提交；扫描结果汇总日志由调用方（main.py 定时任务）
    统一输出，与 order_status_scheduler 的分工保持一致，避免重复日志。

    返回: {"total_scanned": N, "schedule_started": N, "schedule_completed": N}
    """
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()

    async with async_session() as session:
        stats = await _update_schedule_statuses(session, today)
        await session.commit()

    return stats
