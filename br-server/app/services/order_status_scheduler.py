"""订单状态定时转换服务

定时检查并更新所有已支付的待开始/进行中订单状态：
- 自习室座位预约：pending → confirmed（当前时间 >= 开始时间），confirmed → completed（当前时间 >= 结束时间）
- 培训课程预约：pending → confirmed（当前日期 >= 第一课时日期），confirmed 推进高亮课时，today > 最后一课时日期 → completed
"""
import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo

from sqlalchemy import select, and_
from app.models.booking import Booking
from app.models.lesson_schedule import LessonSchedule
from app.models.course_schedule import CourseSchedule
from app.core.database import async_session

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

    if booking.status == "pending" and now >= booking_start:
        # 待开始 → 进行中
        booking.status = "confirmed"
        stats["seat_started"] += 1
        logger.info(f"Seat booking {booking.id}: pending → confirmed (started)")

    elif booking.status == "confirmed" and now >= booking_end:
        # 进行中 → 已完成
        booking.status = "completed"
        stats["seat_completed"] += 1
        logger.info(f"Seat booking {booking.id}: confirmed → completed (ended)")


async def _process_course_booking(session, booking: Booking, today: date, stats: dict):
    """处理培训课程预约订单

    状态转换：
    - pending + today >= 第一课时日期 → confirmed，高亮当前课时
    - confirmed + today > 最后一课时日期 → completed
    - confirmed + 需要推进高亮 → 更新 highlighted_lesson_id
    """
    if not booking.lesson_ids:
        return

    # 查询该订单的课时安排（按 sort_order 排序）
    # 通过 course_id 找到 course_schedules，再找 lesson_schedules，按 lesson_ids 过滤
    result = await session.execute(
        select(LessonSchedule)
        .join(CourseSchedule, LessonSchedule.schedule_id == CourseSchedule.id)
        .where(
            and_(
                CourseSchedule.course_id == booking.course_id,
                LessonSchedule.lesson_id.in_(booking.lesson_ids),
            )
        )
        .order_by(LessonSchedule.sort_order)
    )
    lessons = result.scalars().all()

    if not lessons:
        return

    if booking.status == "pending":
        # 待开始：检查当前日期是否 >= 第一课时的上课日期
        first_lesson = lessons[0]
        if today >= first_lesson.lesson_date:
            booking.status = "confirmed"
            # 高亮当前课时（第一个 lesson_date >= today 的课时）
            _update_highlight(booking, lessons, today, stats, is_new_start=True)
            logger.info(f"Course booking {booking.id}: pending → confirmed, highlighting lesson")

    elif booking.status == "confirmed":
        # 进行中：检查是否需要推进高亮或完成
        last_lesson = lessons[-1]

        if today > last_lesson.lesson_date:
            # 当前日期超过最后一门课时的日期 → 已完成
            booking.status = "completed"
            booking.highlighted_lesson_id = None
            stats["course_completed"] += 1
            logger.info(f"Course booking {booking.id}: confirmed → completed (all lessons done)")
        else:
            # 检查是否需要推进高亮
            _update_highlight(booking, lessons, today, stats, is_new_start=False)


def _update_highlight(booking: Booking, lessons, today: date, stats: dict, is_new_start: bool = False):
    """更新课时高亮

    找到当前应该高亮的课时：第一个 lesson_date >= today 的课时
    如果所有课时都已过去，高亮最后一门
    """
    target_lesson = None
    for lesson in lessons:
        if lesson.lesson_date >= today:
            target_lesson = lesson
            break

    if target_lesson is None:
        # 所有课时都已过去，高亮最后一门
        target_lesson = lessons[-1]

    if booking.highlighted_lesson_id != target_lesson.lesson_id:
        booking.highlighted_lesson_id = target_lesson.lesson_id
        if not is_new_start:
            stats["course_highlight_updated"] += 1
            logger.info(f"Course booking {booking.id}: highlight moved to lesson {target_lesson.lesson_id}")
    elif is_new_start:
        stats["course_started"] += 1
