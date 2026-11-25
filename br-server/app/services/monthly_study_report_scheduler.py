"""学习月报通知定时任务

每周一按配置时间运行，统计 App 用户本月学习数据，并通过公共发送消息方法推送。
"""
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session
from app.models.user import User
from app.services.notification_service import NotificationService
from app.services.study_record_service import get_monthly_summary
from app.utils.timezone import booking_now

logger = logging.getLogger(__name__)

WEEKDAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DEFAULT_REPORT_DAY_OF_WEEK = "mon"
DEFAULT_REPORT_HOUR = 9
DEFAULT_REPORT_MINUTE = 0


def parse_monthly_study_report_schedule() -> tuple[str, int, int]:
    """解析学习月报配置，非法值回退到 mon / 09:00。"""
    raw_day = getattr(
        settings, "MONTHLY_STUDY_REPORT_DAY_OF_WEEK", DEFAULT_REPORT_DAY_OF_WEEK
    )
    day_of_week = DEFAULT_REPORT_DAY_OF_WEEK
    candidate_day = str(raw_day).strip().lower()[:3] if raw_day else ""
    if candidate_day in WEEKDAY_KEYS:
        day_of_week = candidate_day
    else:
        logger.warning(
            "Invalid MONTHLY_STUDY_REPORT_DAY_OF_WEEK=%r, fallback to %s",
            raw_day,
            DEFAULT_REPORT_DAY_OF_WEEK,
        )

    hour, minute = DEFAULT_REPORT_HOUR, DEFAULT_REPORT_MINUTE
    raw_time = getattr(settings, "MONTHLY_STUDY_REPORT_TIME", "09:00")
    try:
        hour_str, minute_str = str(raw_time).split(":")
        parsed_hour, parsed_minute = int(hour_str), int(minute_str)
        if 0 <= parsed_hour <= 23 and 0 <= parsed_minute <= 59:
            hour, minute = parsed_hour, parsed_minute
        else:
            raise ValueError
    except (TypeError, ValueError):
        logger.warning(
            "Invalid MONTHLY_STUDY_REPORT_TIME=%r, fallback to %02d:%02d",
            raw_time,
            DEFAULT_REPORT_HOUR,
            DEFAULT_REPORT_MINUTE,
        )

    return day_of_week, hour, minute


def next_monthly_study_report_run(
    now: datetime,
    day_of_week: str,
    hour: int,
    minute: int,
) -> datetime:
    """计算 now 之后最近一次运行时间（含今天未到点的情况）。"""
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    target += timedelta(days=(WEEKDAY_KEYS.index(day_of_week) - now.weekday()) % 7)
    if target <= now:
        target += timedelta(days=7)
    return target


async def send_monthly_study_reports(today: date | None = None) -> dict:
    """向本月有已完成学习的 App 用户发送学习月报通知（真实会话 + 运行日期）。"""
    report_date = today or booking_now(settings.BOOKING_TIMEZONE).date()
    async with async_session() as session:
        stats = await _send_monthly_study_reports(session, report_date)
        await session.commit()
    return stats


async def _send_monthly_study_reports(
    session: AsyncSession, report_date: date
) -> dict:
    """统计并发送学习月报；同一用户同一月份由通知服务去重，重复运行不会重复发送。"""
    stats = {"total_scanned": 0, "sent": 0, "skipped": 0, "failed": 0}

    user_ids = list(
        (
            await session.execute(
                select(User.id).where(
                    User.user_source == "app",
                    User.status != "deleted",
                )
            )
        )
        .scalars()
        .all()
    )
    stats["total_scanned"] = len(user_ids)

    service = NotificationService(session)
    for user_id in user_ids:
        try:
            summary = await get_monthly_summary(session, user_id, report_date)
            if summary.monthly_bookings == 0:
                stats["skipped"] += 1
                continue
            notification = await service.notify_monthly_study_report(
                user_id, report_date, summary
            )
            if notification is None:
                stats["skipped"] += 1
            else:
                stats["sent"] += 1
        except Exception:
            stats["failed"] += 1
            logger.exception("Monthly study report failed for user %s", user_id)

    return stats
