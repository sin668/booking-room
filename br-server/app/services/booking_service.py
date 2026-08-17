import uuid
from datetime import date, datetime, timedelta, time
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.booking_rules import (
    BookingCompletionInput,
    calculate_booking_hours,
    can_cancel_paid_booking,
    should_mark_booking_completed,
)
from app.models.booking import Booking
from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.repositories.booking_repository import BookingRepository
from app.schemas.booking import (
    BookingAdminListResponse,
    BookingAdminResponse,
    BookingCreate,
    BookingListResponse,
    BookingResponse,
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
    seat: Seat,
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
        seat=SeatBrief.model_validate(seat),
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

    booking = Booking(
        seat_id=data.seat_id,
        user_id=str(user_id),
        room_id=seat.room_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        status="confirmed" if balance_payment else "pending",
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

    conditions = [Booking.user_id == str(user_id)]
    if status is not None:
        conditions.append(Booking.status == status)

    where_clause = and_(*conditions)

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
    lesson_map: dict[int, list[str]] = {}  # booking_id -> lesson_titles
    if course_booking_ids:
        course_ids = {b.course_id for b in bookings if getattr(b, "booking_type", None) == "course" and b.course_id is not None}
        if course_ids:
            courses_result = await db.execute(select(Course).where(Course.id.in_(course_ids)))
            course_map = {c.id: c.name for c in courses_result.scalars().all()}

        for b in bookings:
            if getattr(b, "booking_type", None) == "course" and b.lesson_ids:
                lessons_result = await db.execute(
                    select(CourseLesson.title).where(CourseLesson.id.in_(b.lesson_ids))
                )
                lesson_map[b.id] = list(lessons_result.scalars().all())

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
            items.append(resp)
        else:
            items.append(_build_booking_response(b, seat_map[b.seat_id], room_map[b.room_id]))

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

    if booking.status != "confirmed":
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
        booking.status = "confirmed"
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


def _build_admin_booking_response(booking: Booking, seat: Seat, room: StudyRoom) -> BookingAdminResponse:
    return BookingAdminResponse(
        id=booking.id,
        user_id=booking.user_id,
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
        created_at=booking.created_at,
        updated_at=booking.updated_at,
        seat=SeatBrief.model_validate(seat),
        room=RoomBrief.model_validate(room),
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

    seat_ids = {b.seat_id for b in bookings}
    room_ids = {b.room_id for b in bookings}

    seats_result = await db.execute(select(Seat).where(Seat.id.in_(seat_ids))) if seat_ids else None
    rooms_result = await db.execute(select(StudyRoom).where(StudyRoom.id.in_(room_ids))) if room_ids else None
    seat_map = {s.id: s for s in seats_result.scalars().all()} if seats_result else {}
    room_map = {r.id: r for r in rooms_result.scalars().all()} if rooms_result else {}

    items: list[BookingAdminResponse] = []
    for b in bookings:
        items.append(_build_admin_booking_response(b, seat_map[b.seat_id], room_map[b.room_id]))

    return BookingAdminListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def admin_get_booking(db: AsyncSession, booking_id: int) -> BookingAdminResponse:
    """Get any booking detail (admin view)."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if booking is None:
        raise BookingNotFoundError("预约不存在")

    seat = (await db.execute(select(Seat).where(Seat.id == booking.seat_id))).scalar_one()
    room = (await db.execute(select(StudyRoom).where(StudyRoom.id == booking.room_id))).scalar_one()

    return _build_admin_booking_response(booking, seat, room)


async def admin_cancel_booking(db: AsyncSession, booking_id: int) -> BookingAdminResponse:
    """Cancel any booking with the same refund settlement as user cancellation."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if booking is None:
        raise BookingNotFoundError("预约不存在")

    if booking.status == "cancelled":
        raise BookingAlreadyCancelledError("该预约已取消")

    await cancel_booking(db, booking.id, uuid.UUID(booking.user_id))
    await db.refresh(booking)

    seat = (await db.execute(select(Seat).where(Seat.id == booking.seat_id))).scalar_one()
    room = (await db.execute(select(StudyRoom).where(StudyRoom.id == booking.room_id))).scalar_one()

    return _build_admin_booking_response(booking, seat, room)
