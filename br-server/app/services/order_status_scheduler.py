"""订单状态定时转换服务

定时检查并更新所有已支付的待开始/进行中订单状态：
- 自习室座位预约：pending → confirmed（当前时间 >= 开始时间），confirmed → completed（当前时间 >= 结束时间）
- 培训课程预约：pending → confirmed（当前日期 >= 开课日期），confirmed 推进高亮课时，today > 最后一课时日期 → completed；
  开课日期统一取第一课时日期（first_lesson.lesson_date），定制订单与固定班课口径一致
"""
import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo

from sqlalchemy import select, and_
from app.models.booking import Booking
from app.models.lesson_schedule import LessonSchedule
from app.models.course_schedule import CourseSchedule
from app.core.database import async_session
from app.core.config import settings

logger = logging.getLogger(__name__)


async def check_and_update_order_statuses() -> dict:
    """
    定时检查并更新所有已支付的待开始/进行中订单状态。

    返回: {"seat_started": N, "seat_completed": N, "course_started": N, "course_highlight_updated": N, "course_completed": N}
    """
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    today = now.date()
    current_time = now.time()

    stats = {
        "total_scanned": 0,
        "seat_started": 0,
        "seat_completed": 0,
        "course_started": 0,
        "course_highlight_updated": 0,
        "course_completed": 0,
    }

    async with async_session() as session:
        # 查询所有已支付的待开始和进行中订单
        result = await session.execute(
            select(Booking).where(
                and_(
                    Booking.payment_status == "paid",
                    Booking.status.in_(["pending", "confirmed"]),
                    Booking.booking_type.in_(["seat", "course"]),
                )
            )
        )
        bookings = result.scalars().all()
        stats["total_scanned"] = len(bookings)

        for booking in bookings:
            try:
                if booking.booking_type == "seat":
                    await _process_seat_booking(session, booking, today, current_time, stats)
                elif booking.booking_type == "course":
                    await _process_course_booking(session, booking, today, stats)
            except Exception:
                if settings.SCHEDULER_LOG_ENABLED:
                    logger.exception(f"Error processing booking {booking.id}")

        await session.commit()

    return stats


async def _process_seat_booking(session, booking: Booking, today: date, current_time, stats: dict):
    """处理自习室座位预约订单

    状态转换：
    - pending + now >= date+start_time → confirmed（进行中）
    - confirmed + now >= date+end_time → completed（已完成）
    """
    booking_start = datetime.combine(booking.date, booking.start_time)
    booking_end = datetime.combine(booking.date, booking.end_time)
    now = datetime.combine(today, current_time)

    if settings.SCHEDULER_LOG_ENABLED:
        logger.info(
            "[自习室订单 %d] status=%s, date=%s, start=%s, end=%s | now=%s | start_cmp=%s",
            booking.id, booking.status, booking.date, booking.start_time, booking.end_time,
            now.strftime("%Y-%m-%d %H:%M:%S"),
            "now >= booking_start" if now >= booking_start else "now < booking_start",
        )

    if booking.status == "pending" and now >= booking_start:
        # 待开始 → 进行中
        booking.status = "confirmed"
        stats["seat_started"] += 1
        if settings.SCHEDULER_LOG_ENABLED:
            logger.info("Seat booking %d: pending → confirmed (started)", booking.id)

    elif booking.status == "confirmed" and now >= booking_end:
        # 进行中 → 已完成
        booking.status = "completed"
        stats["seat_completed"] += 1
        if settings.SCHEDULER_LOG_ENABLED:
            logger.info("Seat booking %d: confirmed → completed (ended)", booking.id)


async def _process_course_booking(session, booking: Booking, today: date, stats: dict):
    """处理培训课程预约订单

    状态转换：
    - pending + today >= 开课日期 → confirmed，高亮当前课时（开课日期统一取第一课时日期，定制订单与固定班课口径一致）
    - confirmed + today > 最后一课时日期 → completed
    - confirmed + 需要推进高亮 → 更新 highlighted_lesson_id
    """
    if not booking.lesson_ids:
        return

    # 查询该订单的课时安排（按 sort_order 排序）
    # 优先按订单关联的排课记录（schedule_id）精确查询，避免同一课程下
    # 多个排课（固定班课/多个定制排课）的相同 lesson_id 记录互相混入；
    # 旧订单无 schedule_id 时回退按 course_id + lesson_ids 查询
    if booking.schedule_id:
        result = await session.execute(
            select(LessonSchedule)
            .where(
                and_(
                    LessonSchedule.schedule_id == booking.schedule_id,
                    LessonSchedule.lesson_id.in_(booking.lesson_ids),
                )
            )
            .order_by(LessonSchedule.sort_order)
        )
    else:
        fallback_conditions = [
            CourseSchedule.course_id == booking.course_id,
            LessonSchedule.lesson_id.in_(booking.lesson_ids),
        ]
        # 旧订单无 schedule_id 时，按订单排课类型过滤排课记录，
        # 避免同课程 fixed/custom 排课的相同 lesson_id 记录互相混入
        if booking.schedule_type:
            fallback_conditions.append(CourseSchedule.schedule_type == booking.schedule_type)
        result = await session.execute(
            select(LessonSchedule)
            .join(CourseSchedule, LessonSchedule.schedule_id == CourseSchedule.id)
            .where(and_(*fallback_conditions))
            .order_by(LessonSchedule.sort_order)
        )
    lessons = result.scalars().all()

    if not lessons:
        if settings.SCHEDULER_LOG_ENABLED:
            logger.info("[课程订单 %d] status=%s, 但未找到课时安排 (course_id=%s, lesson_ids=%s)", booking.id, booking.status, booking.course_id, booking.lesson_ids)
        return

    first_lesson = lessons[0]
    last_lesson = lessons[-1]
    # 开课日期统一以第一课时日期为准（定制订单与固定班课口径一致）
    start_date = first_lesson.lesson_date
    if settings.SCHEDULER_LOG_ENABLED:
        logger.info(
            "[课程订单 %d] status=%s, today=%s | start_date=%s, first_lesson=%s, last_lesson=%s | highlighted=%s",
            booking.id, booking.status, today,
            start_date, first_lesson.lesson_date, last_lesson.lesson_date,
            booking.highlighted_lesson_id,
        )

    if booking.status == "pending":
        # 待开始：检查当前日期是否 >= 开课日期
        if today >= start_date:
            booking.status = "confirmed"
            # 高亮当前课时（第一个 lesson_date >= today 的课时）
            _update_highlight(booking, lessons, today, stats, is_new_start=True)
            if settings.SCHEDULER_LOG_ENABLED:
                logger.info(f"Course booking {booking.id}: pending → confirmed, highlighting lesson")

    elif booking.status == "confirmed":
        # 进行中：检查是否需要推进高亮或完成
        if today > last_lesson.lesson_date:
            # 当前日期超过最后一门课时的日期 → 已完成
            booking.status = "completed"
            booking.highlighted_lesson_id = None
            stats["course_completed"] += 1
            if settings.SCHEDULER_LOG_ENABLED:
                logger.info(f"Course booking {booking.id}: confirmed → completed (all lessons done)")
        else:
            # 检查是否需要推进高亮
            _update_highlight(booking, lessons, today, stats, is_new_start=False)


def _update_highlight(booking: Booking, lessons, today: date, stats: dict, is_new_start: bool = False):
    """更新课时高亮

    找到当前应该高亮的课时：当前日期所在课时，
    即最后一个 lesson_date <= today 的课时（当前日期落在该课时的时间范围内）。
    若所有课时都未开始（理论上不会进入本函数），高亮第一课时。
    """
    target_lesson = None
    for lesson in lessons:
        if lesson.lesson_date <= today:
            target_lesson = lesson
        else:
            break

    if target_lesson is None:
        target_lesson = lessons[0]

    if booking.highlighted_lesson_id != target_lesson.lesson_id:
        booking.highlighted_lesson_id = target_lesson.lesson_id
        if not is_new_start:
            stats["course_highlight_updated"] += 1
            if settings.SCHEDULER_LOG_ENABLED:
                logger.info(f"Course booking {booking.id}: highlight moved to lesson {target_lesson.lesson_id}")
    elif is_new_start:
        stats["course_started"] += 1
