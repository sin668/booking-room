"""排课状态定时任务测试。

覆盖 schedule_status_scheduler 的状态推进：
- pending_start（待开始）：今天 >= 开课日期(start_date) → in_progress（进行中）
- in_progress（进行中）：今天 > 结课日期(end_date) → completed（已完成）
- 未到开课日期的 pending_start 保持不变
- 已超结课日期的 pending_start 先转 in_progress，下一次扫描再转 completed（与订单域两步推进一致）

内层函数 _update_schedule_statuses(session, today) 可注入 session 与 today，便于确定性测试；
公开入口 check_and_update_schedule_statuses() 用真实 async_session + 当前日期调用它。
状态推进复用订单域公用方法 resolve_course_transition（与 order_status_scheduler、预约确认同源）。
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.course import Course
from app.models.course_schedule import CourseSchedule
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.services.schedule_status_scheduler import _update_schedule_statuses

TODAY = date(2026, 9, 4)


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def _seed_base(db: AsyncSession) -> None:
    db.add(StudyRoom(id=1, name="Room 1", address="Address", status="open"))
    db.add(Course(id=1, room_id=1, name="高考冲刺班", category="training", status="active"))
    db.add(Teacher(id=1, name="张老师"))


def _add_schedule(
    db: AsyncSession,
    schedule_id: int,
    *,
    schedule_type: str = "custom",
    start_date: date | None,
    end_date: date | None,
    status: str,
) -> CourseSchedule:
    s = CourseSchedule(
        id=schedule_id,
        course_id=1,
        teacher_id=1,
        start_date=start_date,
        end_date=end_date,
        time_slots='[{"weekday": 3, "time_slot": "10:00-12:00"}]',
        price=Decimal("20.00"),
        custom_price=Decimal("20.00"),
        schedule_type=schedule_type,
        schedule_status=status,
    )
    db.add(s)
    return s


async def _status(db: AsyncSession, schedule_id: int) -> str:
    row = (
        await db.execute(select(CourseSchedule).where(CourseSchedule.id == schedule_id))
    ).scalar_one()
    return row.schedule_status


@pytest.mark.asyncio
async def test_pending_start_promoted_when_today_reaches_start_date(db_session: AsyncSession):
    """待开始排课：今天 == 开课日期 → 进行中。"""
    _seed_base(db_session)
    _add_schedule(
        db_session, 1, start_date=TODAY, end_date=TODAY.replace(day=20), status="pending_start"
    )
    await db_session.flush()

    stats = await _update_schedule_statuses(db_session, TODAY)
    await db_session.flush()

    assert await _status(db_session, 1) == "in_progress"
    assert stats["schedule_started"] == 1
    assert stats["schedule_completed"] == 0


@pytest.mark.asyncio
async def test_pending_start_stays_when_start_date_in_future(db_session: AsyncSession):
    """待开始排课：开课日期在未来 → 保持待开始。"""
    _seed_base(db_session)
    _add_schedule(
        db_session, 1, start_date=date(2026, 9, 10), end_date=date(2026, 9, 20),
        status="pending_start",
    )
    await db_session.flush()

    stats = await _update_schedule_statuses(db_session, TODAY)
    await db_session.flush()

    assert await _status(db_session, 1) == "pending_start"
    assert stats["schedule_started"] == 0


@pytest.mark.asyncio
async def test_pending_start_past_end_date_converges_via_in_progress(db_session: AsyncSession):
    """待开始排课：今天已超结课日期时，复用 resolve_course_transition 先转进行中，
    下一次扫描（进行中 + 今天 > 结课日期）再转已完成——与订单域两步推进一致。

    正常运行时调度器每天扫描，pending_start 只会在开课当天转 in_progress（此时未超结课）；
    本用例覆盖调度器长时间停摆后一次性追赶的收敛路径。
    """
    _seed_base(db_session)
    _add_schedule(
        db_session, 1, start_date=date(2026, 8, 1), end_date=date(2026, 9, 1),
        status="pending_start",
    )
    await db_session.flush()

    # 第一次扫描：pending_start 且 today >= start_date → in_progress
    stats1 = await _update_schedule_statuses(db_session, TODAY)
    await db_session.flush()
    assert await _status(db_session, 1) == "in_progress"
    assert stats1["schedule_started"] == 1
    assert stats1["schedule_completed"] == 0

    # 第二次扫描：in_progress 且 today > end_date → completed
    stats2 = await _update_schedule_statuses(db_session, TODAY)
    await db_session.flush()
    assert await _status(db_session, 1) == "completed"
    assert stats2["schedule_completed"] == 1


@pytest.mark.asyncio
async def test_in_progress_completed_when_past_end_date(db_session: AsyncSession):
    """进行中排课：今天 > 结课日期 → 已完成（既有行为保持）。"""
    _seed_base(db_session)
    _add_schedule(
        db_session, 1, schedule_type="fixed", start_date=date(2026, 8, 1),
        end_date=date(2026, 9, 1), status="in_progress",
    )
    await db_session.flush()

    stats = await _update_schedule_statuses(db_session, TODAY)
    await db_session.flush()

    assert await _status(db_session, 1) == "completed"
    assert stats["schedule_completed"] == 1


@pytest.mark.asyncio
async def test_in_progress_stays_when_end_date_in_future(db_session: AsyncSession):
    """进行中排课：结课日期在未来 → 保持进行中。"""
    _seed_base(db_session)
    _add_schedule(
        db_session, 1, schedule_type="fixed", start_date=date(2026, 8, 1),
        end_date=date(2026, 9, 20), status="in_progress",
    )
    await db_session.flush()

    stats = await _update_schedule_statuses(db_session, TODAY)
    await db_session.flush()

    assert await _status(db_session, 1) == "in_progress"
    assert stats["schedule_completed"] == 0


@pytest.mark.asyncio
async def test_completed_not_scanned(db_session: AsyncSession):
    """已完成排课不在扫描范围内（total_scanned 不计入）。"""
    _seed_base(db_session)
    _add_schedule(
        db_session, 1, start_date=date(2026, 8, 1), end_date=date(2026, 9, 1), status="completed"
    )
    await db_session.flush()

    stats = await _update_schedule_statuses(db_session, TODAY)

    assert stats["total_scanned"] == 0
    assert await _status(db_session, 1) == "completed"
