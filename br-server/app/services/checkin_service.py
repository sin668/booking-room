import calendar
import uuid
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkin import CheckinRecord, UserCheckinStats
from app.schemas.checkin import (
    CheckinActionResponse,
    CheckinCalendarMark,
    CheckinSummaryResponse,
)

CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")
INITIAL_MAKEUP_CARDS = 2
DAILY_REWARD_POINTS = 5
WEEKLY_BONUS_POINTS = 20
WEEKLY_BONUS_INTERVAL = 7
CARD_REWARD_INTERVAL = 30
MAKEUP_WINDOW_DAYS = 30


def _today() -> date:
    return datetime.now(CHINA_TIMEZONE).date()


async def _get_or_create_stats(
    db: AsyncSession, user_id: uuid.UUID
) -> UserCheckinStats:
    stats = await db.get(UserCheckinStats, user_id)
    if stats is None:
        stats = UserCheckinStats(
            user_id=user_id,
            points=0,
            makeup_cards=INITIAL_MAKEUP_CARDS,
        )
        db.add(stats)
        await db.flush()
    return stats


async def _get_signed_dates(db: AsyncSession, user_id: uuid.UUID) -> set[date]:
    result = await db.execute(
        select(CheckinRecord.checkin_date).where(CheckinRecord.user_id == user_id)
    )
    return set(result.scalars().all())


def _calculate_streak(signed_dates: set[date], today: date) -> int:
    cursor = today if today in signed_dates else today - timedelta(days=1)
    streak = 0
    while cursor in signed_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _is_missed(
    day: date, signed_dates: set[date], first_date: date | None, today: date
) -> bool:
    return (
        first_date is not None
        and first_date <= day < today
        and day not in signed_dates
    )


def _collect_makeup_dates(
    signed_dates: set[date], first_date: date | None, today: date
) -> list[date]:
    if first_date is None:
        return []
    cursor = max(first_date, today - timedelta(days=MAKEUP_WINDOW_DAYS))
    dates: list[date] = []
    while cursor < today:
        if cursor not in signed_dates:
            dates.append(cursor)
        cursor += timedelta(days=1)
    return dates


def _build_summary(
    signed_dates: set[date],
    stats: UserCheckinStats,
    today: date,
    month: date,
) -> CheckinSummaryResponse:
    first_date = min(signed_dates) if signed_dates else None
    _, days_in_month = calendar.monthrange(month.year, month.month)

    calendar_mark = []
    for day_number in range(1, days_in_month + 1):
        day = date(month.year, month.month, day_number)
        missed = _is_missed(day, signed_dates, first_date, today)
        calendar_mark.append(
            CheckinCalendarMark(
                date=day,
                signed=day in signed_dates,
                missed=missed,
                makeup_eligible=missed
                and (today - day).days <= MAKEUP_WINDOW_DAYS,
            )
        )

    return CheckinSummaryResponse(
        today=today,
        today_signed=today in signed_dates,
        streak=_calculate_streak(signed_dates, today),
        total_days=len(signed_dates),
        points=stats.points,
        makeup_cards=stats.makeup_cards,
        calendar_mark=calendar_mark,
        missed_dates=_collect_makeup_dates(signed_dates, first_date, today),
    )


async def get_summary(
    db: AsyncSession, user_id: uuid.UUID, month: date
) -> CheckinSummaryResponse:
    stats = await _get_or_create_stats(db, user_id)
    signed_dates = await _get_signed_dates(db, user_id)
    return _build_summary(signed_dates, stats, _today(), month)


async def check_in(
    db: AsyncSession, user_id: uuid.UUID
) -> CheckinActionResponse:
    today = _today()
    stats = await _get_or_create_stats(db, user_id)

    existing = await db.execute(
        select(CheckinRecord.id).where(
            CheckinRecord.user_id == user_id,
            CheckinRecord.checkin_date == today,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="今日已签到",
        )

    db.add(CheckinRecord(user_id=user_id, checkin_date=today, source="daily"))
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="今日已签到",
        )

    signed_dates = await _get_signed_dates(db, user_id)
    streak = _calculate_streak(signed_dates, today)

    reward_points = DAILY_REWARD_POINTS
    if streak % WEEKLY_BONUS_INTERVAL == 0:
        reward_points += WEEKLY_BONUS_POINTS

    reward_cards = 0
    if streak % CARD_REWARD_INTERVAL == 0:
        reward_cards = 1
        stats.makeup_cards += reward_cards

    stats.points += reward_points
    await db.flush()

    return CheckinActionResponse(
        summary=_build_summary(signed_dates, stats, today, today.replace(day=1)),
        reward_points=reward_points,
        reward_cards=reward_cards,
    )


async def make_up(
    db: AsyncSession, user_id: uuid.UUID, dates: list[date]
) -> CheckinActionResponse:
    today = _today()
    unique_dates = set(dates)
    if len(unique_dates) != len(dates):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="补签日期不能重复",
        )

    stats = await _get_or_create_stats(db, user_id)
    signed_dates = await _get_signed_dates(db, user_id)
    first_date = min(signed_dates) if signed_dates else None
    if first_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="暂无可补签的漏签日期",
        )

    ordered_dates = sorted(unique_dates)
    for day in ordered_dates:
        if day >= today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{day.isoformat()} 不是可补签的历史日期",
            )
        if (today - day).days > MAKEUP_WINDOW_DAYS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{day.isoformat()} 超出近 {MAKEUP_WINDOW_DAYS} 天补签范围",
            )
        if day < first_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{day.isoformat()} 早于首次签到日期",
            )
        if day in signed_dates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{day.isoformat()} 已签到",
            )

    if stats.makeup_cards < len(ordered_dates):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="补签卡不足",
        )

    db.add_all(
        [
            CheckinRecord(user_id=user_id, checkin_date=day, source="makeup")
            for day in ordered_dates
        ]
    )
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="补签日期已存在签到记录",
        )

    stats.makeup_cards -= len(ordered_dates)
    await db.flush()

    signed_dates |= unique_dates
    return CheckinActionResponse(
        summary=_build_summary(signed_dates, stats, today, today.replace(day=1)),
        restored_dates=ordered_dates,
    )
