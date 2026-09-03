"""业务时区单一事实源（Design Doc §2.3）。

契约：所有领域纯函数的 now/today/current_time 参数一律为 naive 的
settings.BOOKING_TIMEZONE（Asia/Shanghai）本地时间；时区转换只在服务层入口做一次。
"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings

CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")


def booking_now(timezone: str | None = None) -> datetime:
    """返回 naive 的业务本地时间（默认 settings.BOOKING_TIMEZONE）。"""
    return datetime.now(ZoneInfo(timezone or settings.BOOKING_TIMEZONE)).replace(tzinfo=None)


def ensure_booking_timezone(value: datetime) -> datetime:
    """naive 补 Asia/Shanghai；aware 转换到 Asia/Shanghai。

    从 booking_verification_service 的 _ensure_booking_timezone 提升，语义须逐条一致。
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=CHINA_TIMEZONE)
    return value.astimezone(CHINA_TIMEZONE)
