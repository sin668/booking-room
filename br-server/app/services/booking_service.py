import uuid
from datetime import date, datetime, timedelta, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.booking_rules import (
    BookingCompletionInput,
    calculate_booking_hours,
    can_cancel_paid_booking,
    should_mark_booking_completed,
)
from app.models.booking import Booking
from app.models.coupon import Coupon, UserCoupon
from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.course_schedule import CourseSchedule
from app.models.lesson_schedule import LessonSchedule
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.repositories.booking_repository import BookingRepository
from app.schemas.booking import (
    AdminCouponBrief,
    AdminCourseBrief,
    AdminLessonScheduleItem,
    AdminRefundTransaction,
    AdminScheduleBrief,
    AdminTeacherBrief,
    AdminUserBrief,
    BookingAdminDetailResponse,
    BookingAdminListResponse,
    BookingAdminResponse,
    BookingCreate,
    BookingListResponse,
    BookingResponse,
    LessonScheduleBrief,
    PaymentMethodEnum,
    RoomBrief,
    SeatBrief,
)
from app.core.config import settings
from app.services import coupon_service
from app.services.booking_cancellation_policy import (
    booking_now,
    calculate_cancellation_policy,
)

MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10


class BookingError(ValueError):
    """Base exception for booking operations."""


class SeatNotFoundError(BookingError):
    pass


class SeatMaintenanceError(BookingError):
    pass


class BookingConflictError(BookingError):
    pass


class InvalidTimeRangeError(BookingError):
    pass


class BookingNotFoundError(BookingError):
    pass


class BookingAlreadyCancelledError(BookingError):
    pass


class BookingCancellationNotAllowedError(BookingError):
    pass


class BookingCouponUnavailableError(BookingError):
    pass


class WalletBalanceInsufficientError(BookingError):
    pass


def _calculate_hours(start_time: time, end_time: time) -> float:
    return calculate_booking_hours(start_time, end_time)


def _sync_booking_completion(booking: Booking, now: datetime | None = None) -> bool:
    current_time = now or booking_now(settings.BOOKING_TIMEZONE)
    should_complete = should_mark_booking_completed(
        BookingCompletionInput(
            status=booking.status,
            payment_status=booking.payment_status,
            booking_date=booking.date,
            start_time=booking.start_time,
            end_time=booking.end_time,
            now=current_time,
        )
    )
    if should_complete:
        booking.status = "completed"
        return True
    return False


async def _sync_user_booking_completions(
    db: AsyncSession,
    user_id: uuid.UUID,
    now: datetime | None = None,
) -> None:
    result = await db.execute(
        select(Booking).where(
            Booking.user_id == str(user_id),
            Booking.status == "confirmed",
            Booking.payment_status == "paid",
            Booking.booking_type != "course",
        )
    )
    changed = False
    for booking in result.scalars().all():
        changed = _sync_booking_completion(booking, now) or changed
    if changed:
        await db.flush()


def _can_cancel_booking(booking: Booking, now: datetime | None = None) -> bool:
    current_time = now or booking_now(settings.BOOKING_TIMEZONE)
    return can_cancel_paid_booking(
        status=booking.status,
        payment_status=booking.payment_status,
        booking_date=booking.date,
        start_time=booking.start_time,
        now=current_time,
    )


def _build_cancellation_preview(
    booking: Booking,
    now: datetime,
) -> tuple[Decimal, Decimal, bool]:
    can_cancel = _can_cancel_booking(booking, now)
    if not can_cancel:
        return Decimal("0.00"), Decimal("0.00"), False
    policy = calculate_cancellation_policy(
        total_price=Decimal(str(booking.total_price)),
        booking_date=booking.date,
        start_time=booking.start_time,
        now=now,
    )
    return policy.penalty_amount, policy.refund_amount, policy.can_cancel


def _build_booking_response(
    booking: Booking,
    seat: Seat | None,
    room: StudyRoom,
    refund_transaction_id: uuid.UUID | None = None,
) -> BookingResponse:
    now = booking_now(settings.BOOKING_TIMEZONE)
    cancel_penalty_amount, cancel_refund_amount, can_cancel = _build_cancellation_preview(
        booking,
        now,
    )
    return BookingResponse(
        id=booking.id,
        seat_id=booking.seat_id,
        user_id=booking.user_id,
        room_id=booking.room_id,
        date=booking.date,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        original_price=booking.original_price,
        discount_amount=booking.discount_amount,
        total_price=booking.total_price,
        coupon_id=booking.coupon_id,
        payment_method=booking.payment_method,
        payment_status=booking.payment_status,
        payment_provider=booking.payment_provider,
        paid_at=booking.paid_at,
        cancelled_at=booking.cancelled_at,
        penalty_amount=booking.penalty_amount,
        refund_amount=booking.refund_amount,
        cancel_policy=booking.cancel_policy,
        refund_transaction_id=refund_transaction_id,
        cancel_penalty_amount=cancel_penalty_amount,
        cancel_refund_amount=cancel_refund_amount,
        can_cancel=can_cancel,
        created_at=booking.created_at,
        seat=SeatBrief.model_validate(seat) if seat is not None else None,
        room=RoomBrief.model_validate(room),
    )


async def create_booking(
    db: AsyncSession, user_id: uuid.UUID, data: BookingCreate
) -> BookingResponse:
    """Create a booking with conflict detection.

    Note: For MVP, conflict detection uses a SELECT without FOR UPDATE.
    Under high concurrency, a database-level unique constraint on
    (seat_id, date, start_time, end_time) should be added as a safety net.
    See proposal.md risks section for details.
    """
    seat_result = await db.execute(select(Seat).where(Seat.id == data.seat_id))
    seat = seat_result.scalar_one_or_none()

    if seat is None:
        raise SeatNotFoundError("座位不存在")

    if seat.status == "maintenance":
        raise SeatMaintenanceError("该座位正在维护中")

    if data.end_time <= data.start_time:
        raise InvalidTimeRangeError("结束时间必须晚于开始时间")

    booking_repository = BookingRepository(db)
    has_conflict = await booking_repository.has_time_conflict(
        seat_id=data.seat_id,
        booking_date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
    )
    if has_conflict:
        raise BookingConflictError("该座位该时段已被预约")

    room_result = await db.execute(select(StudyRoom).where(StudyRoom.id == seat.room_id))
    room = room_result.scalar_one()

    if data.coupon_id is None:
        original_price = coupon_service.calculate_original_price(
            Decimal(str(seat.price_per_hour)), data.start_time, data.end_time
        )
        discount_amount = Decimal("0.00")
        total_price = original_price
        user_coupon = None
    else:
        try:
            coupon_result = await coupon_service.validate_coupon_for_booking(
                db=db,
                user_id=user_id,
                user_coupon_id=data.coupon_id,
                seat=seat,
                start_time=data.start_time,
                end_time=data.end_time,
            )
        except coupon_service.CouponError as exc:
            raise BookingCouponUnavailableError("卡券不可用，请重新选择") from exc
        original_price = coupon_result.original_price
        discount_amount = coupon_result.discount_amount
        total_price = coupon_result.payable_amount
        user_coupon = coupon_result.user_coupon

    balance_payment = data.payment_method == PaymentMethodEnum.balance
    user = None
    total_price = total_price.quantize(Decimal("0.01"))

    if balance_payment:
        user_result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            raise BookingError("User not found")
        if Decimal(str(user.balance)) < total_price:
            raise WalletBalanceInsufficientError("Wallet balance is insufficient")

        user.balance = Decimal(str(user.balance)) - total_price

    # 根据预约开始时间判断初始状态：当前时间 < date+start_time → pending（待开始），否则 → confirmed
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    if balance_payment:
        booking_start = datetime.combine(data.date, data.start_time)
        booking_start = booking_start.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        initial_status = "pending" if now < booking_start else "confirmed"
    else:
        initial_status = "pending"

    booking = Booking(
        seat_id=data.seat_id,
        user_id=str(user_id),
        room_id=seat.room_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        status=initial_status,
        original_price=original_price,
        discount_amount=discount_amount,
        total_price=total_price,
        coupon_id=data.coupon_id,
        payment_method=data.payment_method.value,
        payment_status="paid" if balance_payment else "pending",
        payment_provider=None if balance_payment else data.payment_method.value,
        payment_check_count=0,
        next_payment_check_at=None if balance_payment else datetime.now() + timedelta(minutes=1),
    )
    db.add(booking)
    await db.flush()

    wallet_transaction = None
    if balance_payment and user is not None:
        wallet_transaction = WalletTransaction(
            user_id=str(user_id),
            type="consume",
            amount=total_price,
            bonus_amount=Decimal("0.00"),
            balance_after=Decimal(str(user.balance)),
            order_id=str(uuid.uuid4()),
            status="completed",
            payment_method="balance",
        )
        setattr(wallet_transaction, "payment_provider", "balance")
        setattr(wallet_transaction, "payment_status", "paid")
        db.add(wallet_transaction)

    if user_coupon is not None:
        coupon_service.mark_coupon_used(user_coupon, booking.id)

    await db.flush()

    return _build_booking_response(booking, seat, room)


async def list_bookings(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
) -> BookingListResponse:
    """List bookings for the current user with pagination."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    await _sync_user_booking_completions(db, user_id)

    # Handle virtual statuses
    is_in_progress_filter = status == "in_progress"
    is_pending_start_filter = status == "pending_start"
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()

    conditions = [Booking.user_id == str(user_id)]
    if status is not None and not is_in_progress_filter and not is_pending_start_filter:
        conditions.append(Booking.status == status)
    elif is_in_progress_filter:
        # in_progress: status=confirmed, payment_status=paid (所有已支付类型)
        conditions.append(Booking.status == "confirmed")
        conditions.append(Booking.payment_status == "paid")
    elif is_pending_start_filter:
        # pending_start: status in (pending, pending_confirm), payment_status=paid
        conditions.append(Booking.status.in_(["pending", "pending_confirm"]))
        conditions.append(Booking.payment_status == "paid")

    where_clause = and_(*conditions)

    # For in_progress filter, seat bookings are already confirmed when started,
    # so we only need to further filter course bookings by start_date
    if is_in_progress_filter:
        # Separate course and seat booking IDs
        all_ids_result = await db.execute(
            select(Booking.id, Booking.booking_type, Booking.course_id).where(where_clause)
        )
        all_rows = all_ids_result.all()
        seat_booking_ids = {row[0] for row in all_rows if row[1] != "course"}
        course_booking_rows = [(row[0], row[2]) for row in all_rows if row[1] == "course"]
        candidate_course_ids = {cid for _, cid in course_booking_rows if cid is not None}

        valid_course_booking_ids = set()
        if candidate_course_ids:
            # Find courses that have started (start_date <= today)
            started_result = await db.execute(
                select(CourseSchedule.course_id).where(
                    CourseSchedule.course_id.in_(candidate_course_ids),
                    CourseSchedule.start_date <= today,
                )
            )
            started_course_ids = set(started_result.scalars().all())
            valid_course_booking_ids = {
                bid for bid, cid in course_booking_rows
                if cid is not None and cid in started_course_ids
            }

        valid_booking_ids = seat_booking_ids | valid_course_booking_ids
        if not valid_booking_ids:
            return BookingListResponse(items=[], total=0, page=page, page_size=page_size)

        where_clause = and_(
            Booking.user_id == str(user_id),
            Booking.id.in_(valid_booking_ids),
        )

    count_result = await db.execute(
        select(func.count()).select_from(Booking).where(where_clause)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Booking)
        .where(where_clause)
        .order_by(Booking.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    bookings = result.scalars().all()

    seat_ids = {b.seat_id for b in bookings if b.seat_id is not None}
    room_ids = {b.room_id for b in bookings}

    seats_result = await db.execute(select(Seat).where(Seat.id.in_(seat_ids))) if seat_ids else None
    rooms_result = await db.execute(select(StudyRoom).where(StudyRoom.id.in_(room_ids))) if room_ids else None
    seat_map = {s.id: s for s in seats_result.scalars().all()} if seats_result else {}
    room_map = {r.id: r for r in rooms_result.scalars().all()} if rooms_result else {}

    # 查询课程预约相关数据
    course_booking_ids = {b.id for b in bookings if getattr(b, "booking_type", None) == "course"}
    course_map: dict[int, str] = {}  # course_id -> course_name
    course_schedule_map: dict[int, str] = {}  # course_id -> schedule
    course_start_date_map: dict[int, date | None] = {}  # course_id -> start_date
    course_end_date_map: dict[int, date | None] = {}  # course_id -> end_date
    course_teacher_map: dict[int, int | None] = {}  # course_id -> teacher_id
    teacher_map: dict[int, dict] = {}  # teacher_id -> {name, avatar}
    lesson_map: dict[int, list[str]] = {}  # booking_id -> lesson_titles
    lesson_schedule_map: dict[int, list[LessonScheduleBrief]] = {}  # booking_id -> lesson_schedules (filtered by booking.lesson_ids)
    if course_booking_ids:
        course_ids = {b.course_id for b in bookings if getattr(b, "booking_type", None) == "course" and b.course_id is not None}
        if course_ids:
            courses_result = await db.execute(select(Course).where(Course.id.in_(course_ids)))
            courses_list = list(courses_result.scalars().all())
            for c in courses_list:
                course_map[c.id] = c.name
            
            # 查询排课信息（从 course_schedules 表获取 schedule 和 teacher_id）
            schedules_result = await db.execute(
                select(CourseSchedule).where(CourseSchedule.course_id.in_(course_ids))
                .order_by(CourseSchedule.course_id, CourseSchedule.created_at)
            )
            schedule_list = list(schedules_result.scalars().all())
            schedule_by_course: dict[int, CourseSchedule] = {}
            for s in schedule_list:
                if s.course_id not in schedule_by_course:
                    schedule_by_course[s.course_id] = s
            for cid, sched in schedule_by_course.items():
                course_schedule_map[cid] = sched.time_slots
                course_teacher_map[cid] = sched.teacher_id
                course_start_date_map[cid] = sched.start_date
                course_end_date_map[cid] = sched.end_date
            
            # 查询教师信息
            teacher_ids = {s.teacher_id for s in schedule_list if s.teacher_id is not None}
            if teacher_ids:
                teachers_result = await db.execute(select(Teacher).where(Teacher.id.in_(teacher_ids)))
                teacher_map = {t.id: {"name": t.name, "avatar": t.avatar} for t in teachers_result.scalars().all()}

            # 查询课时安排（lesson_schedules + course_lessons title）
            schedule_ids = {s.id for s in schedule_list}
            if schedule_ids:
                ls_result = await db.execute(
                    select(LessonSchedule)
                    .where(LessonSchedule.schedule_id.in_(schedule_ids))
                    .order_by(LessonSchedule.sort_order)
                )
                lesson_schedules_list = list(ls_result.scalars().all())
                # Build course_id -> schedule_id mapping
                schedule_id_to_course = {s.id: s.course_id for s in schedule_list}
                # schedule_id -> (schedule_type, schedule_status)，用于按订单类型选择课时记录
                schedule_info_map = {s.id: (s.schedule_type, s.schedule_status) for s in schedule_list}
                # lesson_schedule.id -> 所属 schedule_id，用于按订单关联的排课精确隔离课时
                ls_to_schedule_id = {ls.id: ls.schedule_id for ls in lesson_schedules_list}
                # Collect lesson_ids for title lookup
                all_lesson_ids = {ls.lesson_id for ls in lesson_schedules_list}
                lesson_title_map: dict[int, str] = {}
                if all_lesson_ids:
                    lt_result = await db.execute(
                        select(CourseLesson.id, CourseLesson.title).where(CourseLesson.id.in_(all_lesson_ids))
                    )
                    lesson_title_map = {row[0]: row[1] for row in lt_result.all()}
                # Group by course_id (intermediate, will be filtered per booking later)
                lesson_schedule_by_course: dict[int, list[LessonScheduleBrief]] = {}
                for ls in lesson_schedules_list:
                    cid = schedule_id_to_course.get(ls.schedule_id)
                    if cid is not None:
                        if cid not in lesson_schedule_by_course:
                            lesson_schedule_by_course[cid] = []
                        sched_type, sched_status = schedule_info_map.get(ls.schedule_id, (None, None))
                        lesson_schedule_by_course[cid].append(
                            LessonScheduleBrief(
                                id=ls.id,
                                lesson_id=ls.lesson_id,
                                lesson_date=ls.lesson_date,
                                lesson_time_slot=ls.lesson_time_slot,
                                lesson_title=lesson_title_map.get(ls.lesson_id),
                                sort_order=ls.sort_order,
                                schedule_type=sched_type,
                                schedule_status=sched_status,
                            )
                        )
                # Store as booking_id -> filtered lesson_schedules (only lessons in booking.lesson_ids)
                # 优先按订单关联的排课记录（schedule_id）精确隔离课时，避免同一课程下
                # 多个订单（固定班课/多个定制排课）的相同 lesson_id 记录互相混入；
                # 旧订单无 schedule_id 时回退按 schedule_type + in_progress 过滤。
                for b in bookings:
                    if getattr(b, "booking_type", None) == "course" and b.course_id and b.lesson_ids:
                        all_course_ls = lesson_schedule_by_course.get(b.course_id, [])
                        booked_lesson_ids = set(b.lesson_ids)
                        b_schedule_id = getattr(b, "schedule_id", None)
                        if b_schedule_id:
                            lesson_schedule_map[b.id] = [
                                ls for ls in all_course_ls
                                if ls.lesson_id in booked_lesson_ids
                                and ls_to_schedule_id.get(ls.id) == b_schedule_id
                            ]
                        else:
                            b_schedule_type = getattr(b, "schedule_type", None)
                            lesson_schedule_map[b.id] = [
                                ls for ls in all_course_ls
                                if ls.lesson_id in booked_lesson_ids
                                and (b_schedule_type is None or ls.schedule_type == b_schedule_type)
                                and ls.schedule_status == "in_progress"
                            ]

    # 查询课时标题 + fallback：当 lesson_schedules 中间表无记录时，从 lesson_ids + lesson_titles 构建基本条目
    for b in bookings:
        if getattr(b, "booking_type", None) == "course" and b.lesson_ids:
            if b.id not in lesson_map:
                lessons_result = await db.execute(
                    select(CourseLesson.title).where(CourseLesson.id.in_(b.lesson_ids))
                )
                lesson_map[b.id] = list(lessons_result.scalars().all())

            # Fallback: 当 lesson_schedules 中间表无记录或过滤后为空时，构建基本条目
            if not lesson_schedule_map.get(b.id):
                fallback_titles = lesson_map.get(b.id, [])
                lesson_schedule_map[b.id] = [
                    LessonScheduleBrief(
                        id=0,
                        lesson_id=lid,
                        lesson_date=None,
                        lesson_time_slot="",
                        lesson_title=fallback_titles[i] if i < len(fallback_titles) else None,
                        sort_order=i,
                    )
                    for i, lid in enumerate(b.lesson_ids)
                ]

    items: list[BookingResponse] = []
    for b in bookings:
        if getattr(b, "booking_type", None) == "course":
            # 课程预约：无座位，附加课程信息
            resp = _build_booking_response(
                b, seat_map.get(b.seat_id), room_map[b.room_id]
            )
            resp.booking_type = "course"
            resp.course_id = b.course_id
            resp.course_name = course_map.get(b.course_id) if b.course_id else None
            resp.lesson_titles = lesson_map.get(b.id)
            resp.schedule = course_schedule_map.get(b.course_id) if b.course_id else None
            start_d = course_start_date_map.get(b.course_id) if b.course_id else None
            # 1V1 定制订单的开课日期取用户预约时选择的日期（bookings.date），
            # 避免同一课程下固定班课排课的开课日期混淆定制订单展示
            if getattr(b, "schedule_type", None) == "custom" and getattr(b, "date", None):
                start_d = b.date
            resp.start_date = start_d.isoformat() if start_d else None
            end_d = course_end_date_map.get(b.course_id) if b.course_id else None
            resp.end_date = end_d.isoformat() if end_d else None
            # started: start_date <= today (Asia/Shanghai)
            resp.started = (start_d <= today) if start_d else None
            # lesson_schedules (already filtered by booking.lesson_ids above)
            resp.lesson_schedules = lesson_schedule_map.get(b.id) or []
            # highlighted_lesson_id
            resp.highlighted_lesson_id = getattr(b, "highlighted_lesson_id", None)
            # 订单课时类型（fixed 固定班课 / custom 1V1 定制），前端据此展示"定制"标签
            resp.schedule_type = getattr(b, "schedule_type", None)
            # 设置教师信息
            if b.course_id and b.course_id in course_teacher_map:
                teacher_id = course_teacher_map[b.course_id]
                if teacher_id and teacher_id in teacher_map:
                    teacher_info = teacher_map[teacher_id]
                    resp.teacher_name = teacher_info["name"]
                    resp.teacher_avatar = teacher_info["avatar"]
            items.append(resp)
        else:
            items.append(_build_booking_response(b, seat_map.get(b.seat_id), room_map.get(b.room_id)))

    return BookingListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_booking(
    db: AsyncSession, booking_id: int, user_id: uuid.UUID
) -> BookingResponse:
    """Get a booking detail. Only own bookings are visible."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if booking is None or booking.user_id != str(user_id):
        raise BookingNotFoundError("预约不存在")

    if _sync_booking_completion(booking):
        await db.flush()

    seat = (await db.execute(select(Seat).where(Seat.id == booking.seat_id))).scalar_one()
    room = (await db.execute(select(StudyRoom).where(StudyRoom.id == booking.room_id))).scalar_one()

    return _build_booking_response(booking, seat, room)


async def cancel_booking(
    db: AsyncSession, booking_id: int, user_id: uuid.UUID
) -> BookingResponse:
    """Cancel own paid future booking and refund the remaining amount to wallet."""
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id).with_for_update()
    )
    booking = result.scalar_one_or_none()

    if booking is None or booking.user_id != str(user_id):
        raise BookingNotFoundError("预约不存在")

    if _sync_booking_completion(booking):
        await db.flush()
        raise BookingCancellationNotAllowedError("预约已开始不可取消")

    if booking.status == "cancelled":
        raise BookingAlreadyCancelledError("该预约已取消")

    # Pending (unpaid) bookings can be cancelled without refund logic
    if booking.payment_status == "pending" and booking.status == "pending":
        now = booking_now(settings.BOOKING_TIMEZONE)
        booking.status = "cancelled"
        booking.cancelled_at = now
        await coupon_service.restore_user_coupon_for_booking(db, booking)
        await db.flush()
        seat = (await db.execute(select(Seat).where(Seat.id == booking.seat_id))).scalar_one()
        room = (await db.execute(select(StudyRoom).where(StudyRoom.id == booking.room_id))).scalar_one()
        return _build_booking_response(booking, seat, room)

    if booking.status not in ("confirmed", "pending"):
        raise BookingCancellationNotAllowedError("该预约不可取消")

    if booking.payment_status != "paid":
        raise BookingCancellationNotAllowedError("未支付预约不可取消")

    policy = calculate_cancellation_policy(
        total_price=Decimal(str(booking.total_price)),
        booking_date=booking.date,
        start_time=booking.start_time,
    )
    if not policy.can_cancel:
        _sync_booking_completion(booking)
        await db.flush()
        raise BookingCancellationNotAllowedError("预约已开始不可取消")

    user_result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    user = user_result.scalar_one_or_none()
    if user is None:
        raise BookingError("User not found")

    existing_refund_result = await db.execute(
        select(WalletTransaction).where(
            WalletTransaction.booking_id == booking.id,
            WalletTransaction.type == "booking_refund",
        )
    )
    if existing_refund_result.scalar_one_or_none() is not None:
        raise BookingAlreadyCancelledError("该预约已取消")

    user.balance = (
        Decimal(str(user.balance)) + policy.refund_amount
    ).quantize(Decimal("0.01"))

    now = booking_now(settings.BOOKING_TIMEZONE)
    booking.status = "cancelled"
    booking.cancelled_at = now
    booking.penalty_amount = policy.penalty_amount
    booking.refund_amount = policy.refund_amount
    booking.cancel_policy = policy.policy
    await coupon_service.restore_user_coupon_for_booking(db, booking)

    wallet_transaction = WalletTransaction(
        user_id=str(user_id),
        type="booking_refund",
        amount=policy.refund_amount,
        bonus_amount=Decimal("0.00"),
        balance_after=Decimal(str(user.balance)),
        order_id=str(uuid.uuid4()),
        status="completed",
        payment_method=booking.payment_method,
        booking_id=booking.id,
    )
    setattr(wallet_transaction, "payment_provider", booking.payment_provider or booking.payment_method)
    setattr(wallet_transaction, "payment_status", "paid")
    setattr(wallet_transaction, "paid_at", now)
    db.add(wallet_transaction)
    await db.flush()

    seat = (await db.execute(select(Seat).where(Seat.id == booking.seat_id))).scalar_one()
    room = (await db.execute(select(StudyRoom).where(StudyRoom.id == booking.room_id))).scalar_one()

    return _build_booking_response(
        booking,
        seat,
        room,
        refund_transaction_id=wallet_transaction.id,
    )


async def pay_pending_booking(
    db: AsyncSession,
    booking_id: int,
    user_id: uuid.UUID,
    payment_method: PaymentMethodEnum,
    wechat_payment_params: dict[str, str] | None = None,
) -> BookingResponse:
    """Process payment for an existing pending booking.

    For balance: deduct from wallet, mark as paid.
    For wechat: wechat_payment_params should be pre-created by the route handler.
    """
    result = await db.execute(
        select(Booking).where(Booking.id == booking_id).with_for_update()
    )
    booking = result.scalar_one_or_none()

    if booking is None or booking.user_id != str(user_id):
        raise BookingNotFoundError("预约不存在")

    if booking.status != "pending" or booking.payment_status != "pending":
        raise BookingError("该预约不在待支付状态")

    total_price = Decimal(str(booking.total_price)).quantize(Decimal("0.01"))

    if payment_method == PaymentMethodEnum.balance:
        user_result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            raise BookingError("User not found")
        if Decimal(str(user.balance)) < total_price:
            raise WalletBalanceInsufficientError("Wallet balance is insufficient")

        user.balance = Decimal(str(user.balance)) - total_price
        # 根据预约开始时间判断状态：当前时间 < date+start_time → pending（待开始），否则 → confirmed
        now = datetime.now(ZoneInfo("Asia/Shanghai"))
        booking_start = datetime.combine(booking.date, booking.start_time)
        booking_start = booking_start.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        booking.status = "pending" if now < booking_start else "confirmed"
        booking.payment_status = "paid"
        booking.payment_method = "balance"
        booking.payment_provider = None
        booking.paid_at = datetime.now()
        booking.next_payment_check_at = None

        wallet_transaction = WalletTransaction(
            user_id=str(user_id),
            type="consume",
            amount=total_price,
            bonus_amount=Decimal("0.00"),
            balance_after=Decimal(str(user.balance)),
            order_id=str(uuid.uuid4()),
            status="completed",
            payment_method="balance",
            booking_id=booking.id,
        )
        setattr(wallet_transaction, "payment_provider", "balance")
        setattr(wallet_transaction, "payment_status", "paid")
        db.add(wallet_transaction)
        await db.flush()
    else:
        booking.payment_method = "wechat"
        booking.payment_provider = "wechat"
        if wechat_payment_params:
            booking.next_payment_check_at = datetime.now() + timedelta(minutes=1)
        await db.flush()

    seat = (await db.execute(select(Seat).where(Seat.id == booking.seat_id))).scalar_one()
    room = (await db.execute(select(StudyRoom).where(StudyRoom.id == booking.room_id))).scalar_one()

    response = _build_booking_response(booking, seat, room)
    if wechat_payment_params:
        response_dict = response.model_dump()
        response_dict["payment_params"] = wechat_payment_params
        from app.schemas.booking import CreateBookingResponse
        return CreateBookingResponse.model_validate(response_dict)
    return response


def _build_admin_booking_response(
    booking: Booking, seat: Seat | None, room: StudyRoom | None, user_nickname: str | None = None
) -> BookingAdminResponse:
    return BookingAdminResponse(
        id=booking.id,
        user_id=booking.user_id,
        user_nickname=user_nickname,
        room_id=booking.room_id,
        seat_id=booking.seat_id,
        date=booking.date,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        original_price=booking.original_price,
        discount_amount=booking.discount_amount,
        total_price=booking.total_price,
        coupon_id=booking.coupon_id,
        payment_method=booking.payment_method,
        payment_status=booking.payment_status,
        payment_provider=booking.payment_provider,
        paid_at=booking.paid_at,
        cancelled_at=booking.cancelled_at,
        penalty_amount=booking.penalty_amount,
        refund_amount=booking.refund_amount,
        cancel_policy=booking.cancel_policy,
        booking_type=booking.booking_type,
        schedule_type=getattr(booking, "schedule_type", None),
        time_slots=getattr(booking, "time_slots", None),
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        seat=SeatBrief.model_validate(seat) if seat is not None else None,
        room=RoomBrief.model_validate(room) if room is not None else None,
    )


async def admin_list_bookings(
    db: AsyncSession,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
    room_id: int | None = None,
    date_start: date | None = None,
    date_end: date | None = None,
) -> BookingAdminListResponse:
    """List all bookings (admin view) with pagination and optional filters."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    conditions = []
    if status is not None:
        conditions.append(Booking.status == status)
    if room_id is not None:
        conditions.append(Booking.room_id == room_id)
    if date_start is not None:
        conditions.append(Booking.date >= date_start)
    if date_end is not None:
        conditions.append(Booking.date <= date_end)

    where_clause = and_(*conditions) if conditions else True

    count_result = await db.execute(
        select(func.count()).select_from(Booking).where(where_clause)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Booking)
        .where(where_clause)
        .order_by(Booking.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    bookings = result.scalars().all()

    seat_ids = {b.seat_id for b in bookings if b.seat_id is not None}
    room_ids = {b.room_id for b in bookings}
    user_ids = {b.user_id for b in bookings}

    seats_result = await db.execute(select(Seat).where(Seat.id.in_(seat_ids))) if seat_ids else None
    rooms_result = await db.execute(select(StudyRoom).where(StudyRoom.id.in_(room_ids))) if room_ids else None
    seat_map = {s.id: s for s in seats_result.scalars().all()} if seats_result else {}
    room_map = {r.id: r for r in rooms_result.scalars().all()} if rooms_result else {}

    # 查询用户昵称（仅对合法 UUID 的 user_id 查询，避免非法值导致参数绑定错误）
    user_nickname_map: dict[str, str] = {}
    valid_user_uuids: list[uuid.UUID] = []
    for uid in user_ids:
        try:
            valid_user_uuids.append(uuid.UUID(uid))
        except (ValueError, AttributeError, TypeError):
            continue
    if valid_user_uuids:
        users_result = await db.execute(
            select(User.id, User.nickname).where(User.id.in_(valid_user_uuids))
        )
        user_nickname_map = {str(row[0]): row[1] for row in users_result.all()}

    items: list[BookingAdminResponse] = []
    for b in bookings:
        items.append(
            _build_admin_booking_response(
                b, seat_map.get(b.seat_id), room_map.get(b.room_id),
                user_nickname=user_nickname_map.get(b.user_id),
            )
        )

    return BookingAdminListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def admin_get_booking(db: AsyncSession, booking_id: int) -> BookingAdminDetailResponse:
    """Get any booking detail (admin view) with related-table aggregation.

    手动逐表查询并用纯 Pydantic 组装响应，不返回带懒加载 relationship 的 ORM 对象，
    避免 async session 外触发 MissingGreenlet。
    """
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if booking is None:
        raise BookingNotFoundError("预约不存在")

    seat = (await db.execute(select(Seat).where(Seat.id == booking.seat_id))).scalar_one_or_none()
    room = (await db.execute(select(StudyRoom).where(StudyRoom.id == booking.room_id))).scalar_one_or_none()

    # user_id 可能不是合法 UUID（历史/异常数据），解析失败时仅展示 user_id
    user_row = None
    try:
        user_uuid = uuid.UUID(booking.user_id)
    except (ValueError, AttributeError, TypeError):
        user_uuid = None
    if user_uuid is not None:
        user_row = (
            await db.execute(
                select(User.id, User.nickname, User.phone, User.avatar).where(
                    User.id == user_uuid
                )
            )
        ).one_or_none()
    user_brief = (
        AdminUserBrief(
            id=booking.user_id,
            nickname=user_row[1],
            phone=user_row[2],
            avatar=user_row[3],
        )
        if user_row is not None
        else None
    )

    # 课程关联信息（仅课程预约订单）
    course_brief: AdminCourseBrief | None = None
    teacher_brief: AdminTeacherBrief | None = None
    schedule_brief: AdminScheduleBrief | None = None
    lesson_items: list[AdminLessonScheduleItem] = []

    if booking.course_id:
        course = (
            await db.execute(select(Course).where(Course.id == booking.course_id))
        ).scalar_one_or_none()
        if course is not None:
            course_brief = AdminCourseBrief(id=course.id, name=course.name, category=course.category)

    schedule: CourseSchedule | None = None
    if getattr(booking, "schedule_id", None):
        schedule = (
            await db.execute(
                select(CourseSchedule).where(CourseSchedule.id == booking.schedule_id)
            )
        ).scalar_one_or_none()
        if schedule is not None:
            schedule_brief = AdminScheduleBrief(
                id=schedule.id,
                start_date=schedule.start_date,
                end_date=schedule.end_date,
                schedule_type=schedule.schedule_type,
                schedule_status=schedule.schedule_status,
                time_slots=schedule.time_slots,
            )

    teacher_id = getattr(booking, "teacher_id", None) or (
        schedule.teacher_id if schedule is not None else None
    )
    if teacher_id:
        teacher = (await db.execute(select(Teacher).where(Teacher.id == teacher_id))).scalar_one_or_none()
        if teacher is not None:
            teacher_brief = AdminTeacherBrief(id=teacher.id, name=teacher.name, avatar=teacher.avatar)

    if schedule is not None:
        lesson_rows = (
            await db.execute(
                select(LessonSchedule, CourseLesson.title)
                .outerjoin(CourseLesson, CourseLesson.id == LessonSchedule.lesson_id)
                .where(LessonSchedule.schedule_id == schedule.id)
                .order_by(LessonSchedule.sort_order, LessonSchedule.id)
            )
        ).all()
        for ls, lesson_title in lesson_rows:
            lesson_items.append(
                AdminLessonScheduleItem(
                    id=ls.id,
                    lesson_id=ls.lesson_id,
                    lesson_title=lesson_title,
                    lesson_date=ls.lesson_date,
                    lesson_time_slot=ls.lesson_time_slot,
                    sort_order=ls.sort_order,
                )
            )

    # 优惠券信息（booking.coupon_id 指向 user_coupons）
    coupon_brief: AdminCouponBrief | None = None
    if booking.coupon_id:
        user_coupon_row = (
            await db.execute(
                select(UserCoupon, Coupon)
                .join(Coupon, Coupon.id == UserCoupon.coupon_id)
                .where(UserCoupon.id == booking.coupon_id)
            )
        ).one_or_none()
        if user_coupon_row is not None:
            user_coupon, coupon = user_coupon_row
            coupon_brief = AdminCouponBrief(
                user_coupon_id=user_coupon.id,
                coupon_id=coupon.id,
                name=coupon.name,
                type=coupon.type,
                discount_amount=coupon.discount_amount,
                discount_percent=coupon.discount_percent,
            )

    # 退款流水（取消退款后写入的 booking_refund 记录）
    refund_brief: AdminRefundTransaction | None = None
    refund_row = (
        await db.execute(
            select(WalletTransaction).where(
                WalletTransaction.booking_id == booking.id,
                WalletTransaction.type == "booking_refund",
            )
        )
    ).scalars().first()
    if refund_row is not None:
        refund_brief = AdminRefundTransaction(
            id=refund_row.id,
            amount=Decimal(str(refund_row.amount)),
            balance_after=Decimal(str(refund_row.balance_after)) if refund_row.balance_after is not None else None,
            payment_method=refund_row.payment_method,
            created_at=refund_row.created_at,
        )

    base = _build_admin_booking_response(
        booking,
        seat,
        room,
        user_nickname=user_row[1] if user_row is not None else None,
    )
    return BookingAdminDetailResponse(
        **base.model_dump(),
        lesson_ids=getattr(booking, "lesson_ids", None),
        highlighted_lesson_id=getattr(booking, "highlighted_lesson_id", None),
        schedule_id=getattr(booking, "schedule_id", None),
        teacher_id=getattr(booking, "teacher_id", None),
        prepay_id=booking.prepay_id,
        transaction_id=booking.transaction_id,
        payment_check_count=booking.payment_check_count,
        user=user_brief,
        course=course_brief,
        teacher=teacher_brief,
        schedule=schedule_brief,
        lesson_schedules=lesson_items,
        coupon=coupon_brief,
        refund_transaction=refund_brief,
    )


async def _cleanup_course_booking_schedule(db: AsyncSession, schedule_id: int | None) -> None:
    """删除订单专属排课记录及其课时记录。

    仅当不存在其他非取消订单引用该排课时才删除（共享的固定班课排课保留）；
    删除前先清空 bookings.schedule_id 外键引用，避免 FK 约束报错。
    使用显式 SQL 删除，不触发 ORM relationship 懒加载。
    """
    if schedule_id is None:
        return

    other_refs = (
        await db.execute(
            select(func.count())
            .select_from(Booking)
            .where(Booking.schedule_id == schedule_id, Booking.status != "cancelled")
        )
    ).scalar_one()
    if other_refs > 0:
        return

    await db.execute(
        update(Booking).where(Booking.schedule_id == schedule_id).values(schedule_id=None)
    )
    await db.execute(delete(LessonSchedule).where(LessonSchedule.schedule_id == schedule_id))
    await db.execute(delete(CourseSchedule).where(CourseSchedule.id == schedule_id))


async def admin_cancel_booking(db: AsyncSession, booking_id: int) -> BookingAdminResponse:
    """Cancel any booking with the same refund settlement as user cancellation.

    待开始订单（pending_confirm / 课程预约 pending）：已支付全额退款不扣手续费，
    课程预约额外删除订单专属的排课与课时记录。
    """
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if booking is None:
        raise BookingNotFoundError("预约不存在")

    if booking.status == "cancelled":
        raise BookingAlreadyCancelledError("该预约已取消")

    # 待开始订单：管理员取消，已支付全额退款不扣手续费（不使用行锁，避免嵌套锁冲突）
    is_course_pending_start = booking.booking_type == "course" and booking.status in (
        "pending",
        "pending_confirm",
    )
    if booking.status == "pending_confirm" or is_course_pending_start:
        schedule_id = getattr(booking, "schedule_id", None)
        now = booking_now(settings.BOOKING_TIMEZONE)
        booking.status = "cancelled"
        booking.cancelled_at = now

        if booking.payment_status == "paid":
            try:
                user_uuid = uuid.UUID(booking.user_id)
            except (ValueError, AttributeError, TypeError):
                raise BookingError("User not found")
            user_result = await db.execute(select(User).where(User.id == user_uuid))
            user = user_result.scalar_one_or_none()
            if user is None:
                raise BookingError("User not found")

            refund_amount = Decimal(str(booking.total_price))
            user.balance = (Decimal(str(user.balance)) + refund_amount).quantize(Decimal("0.01"))

            booking.penalty_amount = Decimal("0")
            booking.refund_amount = refund_amount
            booking.cancel_policy = "full_refund"
            await coupon_service.restore_user_coupon_for_booking(db, booking)

            wallet_transaction = WalletTransaction(
                user_id=booking.user_id,
                type="booking_refund",
                amount=refund_amount,
                bonus_amount=Decimal("0.00"),
                balance_after=Decimal(str(user.balance)),
                order_id=str(uuid.uuid4()),
                status="completed",
                payment_method=booking.payment_method,
                payment_provider=booking.payment_provider or booking.payment_method,
                payment_status="paid",
                paid_at=now,
                booking_id=booking.id,
            )
            db.add(wallet_transaction)
        await db.flush()

        # 课程预约：删除订单专属的排课与课时记录（共享排课保留）
        if is_course_pending_start:
            await _cleanup_course_booking_schedule(db, schedule_id)

        # 排课清理使用了原生 SQL，内存中 ORM 对象可能已过期，重新查询获取完整数据，
        # 避免 flush 后对象状态问题（参照 BUG-26 教训）
        db.expire_all()
        return await admin_get_booking(db, booking_id)

    await cancel_booking(db, booking.id, uuid.UUID(booking.user_id))
    await db.refresh(booking)

    return await admin_get_booking(db, booking_id)


async def admin_confirm_booking(db: AsyncSession, booking_id: int) -> BookingAdminResponse:
    """确认待确认订单，根据当前时间变更为“待开始”或“进行中”。

    对于1V1定制课时，确认时才创建排课记录（course_schedules + lesson_schedules）。
    """
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if booking is None:
        raise BookingNotFoundError("预约不存在")

    if booking.status != "pending_confirm":
        raise BookingError("该预约不是待确认状态")

    # 根据当前日期与预约日期（booking.date，对应 course_schedules.start_date）判断：
    #   当前日期 >= 预约日期 → “进行中”(confirmed)
    #   当前日期 < 预约日期  → “待开始”(pending)
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    booking_date = booking.date or today
    booking.status = "confirmed" if booking_date <= today else "pending"

    # 1V1定制课时：确认时才创建排课记录（course_schedules + lesson_schedules）
    if booking.booking_type == "course" and getattr(booking, "schedule_type", None) == "custom":
        await _create_custom_schedule_on_confirm(db, booking)

    await db.flush()

    # 重新查询获取完整数据，避免 flush 后 ORM 对象状态问题
    return await admin_get_booking(db, booking_id)


async def _create_custom_schedule_on_confirm(db: AsyncSession, booking: Booking) -> None:
    """管理员确认1V1定制订单时，创建定制排课记录和课时记录。

    排课数据来源：
    - start_date ← booking.date
    - time_slots ← booking.time_slots（无则从 start_time/end_time 重建）
    - teacher_id ← booking.teacher_id
    """
    import json

    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()

    # 从 booking 记录中读取用户选择的日期和时间段
    # time_slots 格式与课程排课一致：[{"weekday": N, "time_slot": "HH:MM-HH:MM"}]
    # 兼容旧数据（纯字符串数组 ["HH:MM-HH:MM"]），补全 weekday 后重建
    from app.services.admin_course_service import AdminCourseService

    lesson_date = booking.date or today
    time_slots_json = getattr(booking, "time_slots", None)
    slots: list[dict] = []
    if time_slots_json:
        try:
            parsed = json.loads(time_slots_json)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        slots.append(item)
                    elif isinstance(item, str):
                        slots.append({"weekday": lesson_date.isoweekday(), "time_slot": item})
        except (json.JSONDecodeError, TypeError):
            slots = []
    if not slots and booking.start_time and booking.end_time:
        time_slot = f"{booking.start_time.strftime('%H:%M')}-{booking.end_time.strftime('%H:%M')}"
        slots = [{"weekday": lesson_date.isoweekday(), "time_slot": time_slot}]
    time_slots_json = json.dumps(slots, ensure_ascii=False)

    # 创建定制排课记录（授课老师取自订单记录）
    custom_schedule = CourseSchedule(
        course_id=booking.course_id,
        teacher_id=getattr(booking, "teacher_id", None),
        start_date=lesson_date,
        time_slots=time_slots_json,
        price=Decimal("0"),
        custom_price=Decimal(str(booking.total_price)) if booking.total_price else Decimal("0"),
        schedule_type="custom",
    )
    db.add(custom_schedule)
    await db.flush()

    # 关联订单与定制排课记录，后续课时查询/状态推进均按此排课隔离，
    # 避免同一课程下多个订单的课时数据互相混入
    booking.schedule_id = custom_schedule.id

    # 创建课时记录：复用排课管理的取模循环分配 + 周次偏移算法计算每课时上课时间，
    # 结课日期 = 最后一个课时的上课日期 + 1 天（与 _save_lesson_schedules 一致）
    lesson_ids = getattr(booking, "lesson_ids", None) or []
    if lesson_ids and slots:
        all_slots = AdminCourseService._generate_all_slots(lesson_date, slots, len(lesson_ids))
    else:
        all_slots = []

    last_lesson_date = None
    for idx, lesson_id in enumerate(lesson_ids):
        if idx < len(all_slots):
            slot = all_slots[idx]
            slot_date = date.fromisoformat(slot["date"])
            slot_time = slot["time"]
        else:
            slot_date = lesson_date
            slot_time = slots[0]["time_slot"] if slots else ""
        last_lesson_date = slot_date
        lesson_schedule = LessonSchedule(
            schedule_id=custom_schedule.id,
            lesson_id=lesson_id,
            lesson_date=slot_date,
            lesson_time_slot=slot_time,
            sort_order=idx,
        )
        db.add(lesson_schedule)

    if last_lesson_date is not None:
        custom_schedule.end_date = last_lesson_date + timedelta(days=1)

    # 同步课程状态（当前日期 > 结课日期 → completed，否则 in_progress）
    custom_schedule.schedule_status = AdminCourseService._compute_schedule_status(
        custom_schedule.end_date
    )
