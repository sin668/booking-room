"""Unit tests for admin booking service methods."""

import pytest
import uuid
from datetime import UTC, date, datetime, timedelta, time
from decimal import Decimal
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
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
from app.schemas.booking import BookingCreate
from app.services.booking_service import (
    BookingAlreadyCancelledError,
    BookingCouponUnavailableError,
    BookingNotFoundError,
    admin_list_bookings,
    admin_get_booking,
    admin_cancel_booking,
    admin_confirm_booking,
    cancel_booking,
    create_booking,
)

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


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


def _make_room(db: AsyncSession, room_id: int = 1, name: str = "Room 1"):
    room = StudyRoom(id=room_id, name=name, address="Address", status="open")
    db.add(room)
    return room


def _make_seat(db: AsyncSession, seat_id: int = 1, room_id: int = 1):
    seat = Seat(
        id=seat_id,
        room_id=room_id,
        seat_number="A1",
        zone="quiet",
        price_per_hour=Decimal("10.00"),
        status="available",
        row=1,
        col=1,
    )
    db.add(seat)
    return seat


def _make_user(
    db: AsyncSession,
    user_id: uuid.UUID = USER_ID,
    balance: Decimal = Decimal("100.00"),
):
    user = User(
        id=user_id,
        phone="18800009999",
        nickname="Booking User",
        password_hash="hash",
        balance=balance,
    )
    db.add(user)
    return user


def _make_booking(
    db: AsyncSession,
    booking_id: int = 1,
    seat_id: int = 1,
    room_id: int = 1,
    user_id: str = "user-1",
    booking_date: date = date(2026, 5, 1),
    status: str = "in_progress",
):
    now = datetime(2026, 5, 1, 10, 0, 0)
    booking = Booking(
        id=booking_id,
        seat_id=seat_id,
        user_id=user_id,
        room_id=room_id,
        date=booking_date,
        start_time=time(9, 0),
        end_time=time(11, 0),
        status=status,
        total_price=Decimal("20.00"),
        created_at=now,
        updated_at=now,
    )
    db.add(booking)
    return booking


def _make_coupon(
    db: AsyncSession,
    user_id: str = str(USER_ID),
    discount_amount: Decimal = Decimal("3.00"),
    min_order_amount: Decimal = Decimal("20.00"),
):
    now = datetime.now(UTC)
    coupon = Coupon(
        name="满20减3",
        description="全场通用",
        type="threshold_amount_off",
        discount_amount=discount_amount,
        discount_percent=None,
        min_order_amount=min_order_amount,
        scope="all",
        seat_zone=None,
        valid_from=now - timedelta(days=1),
        expires_at=now + timedelta(days=1),
        is_active=True,
    )
    db.add(coupon)
    return coupon


async def _make_user_coupon(
    db: AsyncSession,
    user_id: str = str(USER_ID),
):
    coupon = _make_coupon(db, user_id=user_id)
    await db.flush()
    user_coupon = UserCoupon(user_id=user_id, coupon_id=coupon.id, status="available")
    db.add(user_coupon)
    await db.flush()
    return user_coupon


@pytest.mark.asyncio
async def test_create_booking_service_without_coupon_sets_original_and_zero_discount(
    db_session: AsyncSession,
):
    _make_room(db_session, 1)
    seat = _make_seat(db_session, 1, 1)
    _make_user(db_session)
    await db_session.flush()

    result = await create_booking(
        db_session,
        USER_ID,
        BookingCreate(
            seat_id=seat.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
        ),
    )

    assert result.original_price == Decimal("20.00")
    assert result.discount_amount == Decimal("0.00")
    assert result.total_price == Decimal("20.00")
    assert result.coupon_id is None


@pytest.mark.asyncio
async def test_create_booking_service_with_coupon_marks_coupon_used(
    db_session: AsyncSession,
):
    _make_room(db_session, 1)
    seat = _make_seat(db_session, 1, 1)
    _make_user(db_session)
    user_coupon = await _make_user_coupon(db_session)

    result = await create_booking(
        db_session,
        USER_ID,
        BookingCreate(
            seat_id=seat.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            coupon_id=user_coupon.id,
        ),
    )

    assert result.original_price == Decimal("20.00")
    assert result.discount_amount == Decimal("3.00")
    assert result.total_price == Decimal("17.00")
    assert result.coupon_id == user_coupon.id
    await db_session.refresh(user_coupon)
    assert user_coupon.status == "used"
    assert user_coupon.used_booking_id == result.id
    assert user_coupon.used_at is not None


@pytest.mark.asyncio
async def test_create_booking_service_invalid_coupon_does_not_create_booking_or_mutate_coupon(
    db_session: AsyncSession,
):
    _make_room(db_session, 1)
    seat = _make_seat(db_session, 1, 1)
    user_coupon = await _make_user_coupon(db_session, user_id=str(OTHER_USER_ID))

    with pytest.raises(BookingCouponUnavailableError):
        await create_booking(
            db_session,
            USER_ID,
            BookingCreate(
                seat_id=seat.id,
                date=date(2026, 5, 1),
                start_time=time(9, 0),
                end_time=time(11, 0),
                coupon_id=user_coupon.id,
            ),
        )

    booking_ids = (await db_session.execute(select(Booking.id))).scalars().all()
    assert booking_ids == []
    await db_session.refresh(user_coupon)
    assert user_coupon.status == "available"
    assert user_coupon.used_booking_id is None
    assert user_coupon.used_at is None


@pytest.mark.asyncio
async def test_cancel_booking_service_restores_used_coupon(db_session: AsyncSession):
    _make_room(db_session, 1)
    seat = _make_seat(db_session, 1, 1)
    _make_user(db_session, USER_ID, Decimal("0.00"))
    user_coupon = await _make_user_coupon(db_session)
    booking = _make_booking(
        db_session,
        1,
        seat.id,
        1,
        str(USER_ID),
        booking_date=date.today() + timedelta(days=1),
        status="in_progress",
    )
    booking.original_price = Decimal("20.00")
    booking.discount_amount = Decimal("3.00")
    booking.total_price = Decimal("17.00")
    booking.coupon_id = user_coupon.id
    await db_session.flush()
    user_coupon.status = "used"
    user_coupon.used_booking_id = booking.id
    user_coupon.used_at = datetime.now(UTC)
    await db_session.flush()

    result = await cancel_booking(db_session, booking.id, USER_ID)

    assert result.status == "cancelled"
    await db_session.refresh(user_coupon)
    assert user_coupon.status == "available"
    assert user_coupon.used_booking_id is None
    assert user_coupon.used_at is None


@pytest.mark.asyncio
async def test_admin_list_bookings_normal_pagination(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_seat(db_session, 1, 1)
    _make_booking(db_session, 1, 1, 1, "user-1")
    _make_booking(db_session, 2, 1, 1, "user-2")
    _make_booking(db_session, 3, 1, 1, "user-3")
    await db_session.flush()

    result = await admin_list_bookings(db_session, page=1, page_size=2)
    assert result.total == 3
    assert len(result.items) == 2
    assert result.page == 1
    assert result.page_size == 2


@pytest.mark.asyncio
async def test_admin_list_bookings_filter_by_status(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_seat(db_session, 1, 1)
    _make_booking(db_session, 1, 1, 1, "user-1", status="in_progress")
    _make_booking(db_session, 2, 1, 1, "user-2", status="cancelled")
    _make_booking(db_session, 3, 1, 1, "user-3", status="in_progress")
    await db_session.flush()

    result = await admin_list_bookings(db_session, status="in_progress")
    assert result.total == 2
    assert all(b.status == "in_progress" for b in result.items)


@pytest.mark.asyncio
async def test_admin_list_bookings_filter_by_room_id(db_session: AsyncSession):
    _make_room(db_session, 1, "Room A")
    _make_room(db_session, 2, "Room B")
    _make_seat(db_session, 1, 1)
    _make_seat(db_session, 2, 2)
    _make_booking(db_session, 1, 1, 1, "user-1")
    _make_booking(db_session, 2, 2, 2, "user-2")
    await db_session.flush()

    result = await admin_list_bookings(db_session, room_id=2)
    assert result.total == 1
    assert result.items[0].room_id == 2


@pytest.mark.asyncio
async def test_admin_list_bookings_filter_by_date_range(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_seat(db_session, 1, 1)
    _make_booking(db_session, 1, 1, 1, "user-1", booking_date=date(2026, 5, 1))
    _make_booking(db_session, 2, 1, 1, "user-2", booking_date=date(2026, 5, 10))
    _make_booking(db_session, 3, 1, 1, "user-3", booking_date=date(2026, 5, 15))
    await db_session.flush()

    result = await admin_list_bookings(
        db_session, date_start=date(2026, 5, 5), date_end=date(2026, 5, 12)
    )
    assert result.total == 1
    assert result.items[0].date == date(2026, 5, 10)


@pytest.mark.asyncio
async def test_admin_list_bookings_empty_result(db_session: AsyncSession):
    result = await admin_list_bookings(db_session)
    assert result.total == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_admin_get_booking(db_session: AsyncSession):
    _make_room(db_session, 1, "Room A")
    _make_seat(db_session, 1, 1)
    _make_booking(db_session, 1, 1, 1, "user-1")
    await db_session.flush()

    result = await admin_get_booking(db_session, 1)
    assert result.id == 1
    assert result.user_id == "user-1"
    assert result.seat.seat_number == "A1"
    assert result.room.name == "Room A"


@pytest.mark.asyncio
async def test_admin_get_booking_not_found(db_session: AsyncSession):
    with pytest.raises(BookingNotFoundError):
        await admin_get_booking(db_session, 999)


@pytest.mark.asyncio
async def test_admin_cancel_booking(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_seat(db_session, 1, 1)
    _make_user(db_session, USER_ID, Decimal("0.00"))
    _make_booking(
        db_session,
        1,
        1,
        1,
        str(USER_ID),
        booking_date=date.today() + timedelta(days=3),
        status="in_progress",
    )
    await db_session.flush()

    result = await admin_cancel_booking(db_session, 1)
    assert result.status == "cancelled"
    assert result.refund_amount == Decimal("20.00")
    assert result.cancel_policy == "over_48h"
    transaction = (
        await db_session.execute(
            select(WalletTransaction).where(
                WalletTransaction.booking_id == 1,
                WalletTransaction.type == "booking_refund",
            )
        )
    ).scalar_one()
    assert transaction.amount == Decimal("20.00")


@pytest.mark.asyncio
async def test_admin_cancel_booking_already_cancelled(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_seat(db_session, 1, 1)
    _make_booking(db_session, 1, 1, 1, "user-1", status="cancelled")
    await db_session.flush()

    with pytest.raises(BookingAlreadyCancelledError):
        await admin_cancel_booking(db_session, 1)


@pytest.mark.asyncio
async def test_admin_cancel_booking_not_found(db_session: AsyncSession):
    with pytest.raises(BookingNotFoundError):
        await admin_cancel_booking(db_session, 999)


# --- 详情聚合与课程预约取消（admin-booking-list-enhancements）---


def _make_course_data(db: AsyncSession):
    """创建课程/老师/定制排课/课时测试数据，返回 (course, schedule)。"""
    course = Course(
        id=1, room_id=1, name="高考冲刺班", category="training", status="active"
    )
    teacher = Teacher(id=1, name="张老师")
    db.add(course)
    db.add(teacher)
    schedule = CourseSchedule(
        id=1,
        course_id=1,
        teacher_id=1,
        start_date=date(2026, 5, 10),
        time_slots='[{"weekday": 3, "time_slot": "10:00-12:00"}]',
        price=Decimal("20.00"),
        custom_price=Decimal("20.00"),
        schedule_type="custom",
    )
    db.add(schedule)
    lesson = CourseLesson(id=1, course_id=1, title="第1课")
    db.add(lesson)
    db.add(
        LessonSchedule(
            schedule_id=1,
            lesson_id=1,
            lesson_date=date(2026, 5, 13),
            lesson_time_slot="10:00-12:00",
            sort_order=0,
        )
    )
    return course, schedule


def _make_course_booking(
    db: AsyncSession,
    booking_id: int = 1,
    schedule_id: int | None = 1,
    status: str = "pending_start",
    payment_status: str = "paid",
):
    now = datetime(2026, 5, 1, 10, 0, 0)
    booking = Booking(
        id=booking_id,
        seat_id=None,
        user_id=str(USER_ID),
        room_id=1,
        date=date(2026, 5, 10),
        start_time=time(10, 0),
        end_time=time(12, 0),
        status=status,
        payment_status=payment_status,
        total_price=Decimal("20.00"),
        booking_type="course",
        course_id=1,
        schedule_type="custom",
        schedule_id=schedule_id,
        time_slots='[{"weekday": 3, "time_slot": "10:00-12:00"}]',
        teacher_id=1,
        created_at=now,
        updated_at=now,
    )
    db.add(booking)
    return booking


@pytest.mark.asyncio
async def test_admin_get_booking_detail_aggregates_related_tables(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_user(db_session)
    _make_course_data(db_session)
    _make_course_booking(db_session, 1)
    await db_session.flush()

    result = await admin_get_booking(db_session, 1)

    assert result.booking_type == "course"
    assert result.schedule_type == "custom"
    assert result.time_slots == '[{"weekday": 3, "time_slot": "10:00-12:00"}]'
    assert result.user is not None
    assert result.user.nickname == "Booking User"
    assert result.user.phone == "18800009999"
    assert result.course is not None and result.course.name == "高考冲刺班"
    assert result.teacher is not None and result.teacher.name == "张老师"
    assert result.schedule is not None and result.schedule.schedule_type == "custom"
    assert len(result.lesson_schedules) == 1
    assert result.lesson_schedules[0].lesson_title == "第1课"


@pytest.mark.asyncio
async def test_admin_get_booking_detail_includes_refund_transaction(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_user(db_session)
    _make_course_data(db_session)
    _make_course_booking(db_session, 1)
    await db_session.flush()

    await admin_cancel_booking(db_session, 1)
    result = await admin_get_booking(db_session, 1)

    assert result.status == "cancelled"
    assert result.refund_transaction is not None
    assert result.refund_transaction.amount == Decimal("20.00")


@pytest.mark.asyncio
async def test_admin_cancel_course_pending_booking_full_refund_and_schedule_deleted(
    db_session: AsyncSession,
):
    _make_room(db_session, 1)
    _make_user(db_session, balance=Decimal("0.00"))
    _make_course_data(db_session)
    _make_course_booking(db_session, 1)
    await db_session.flush()

    result = await admin_cancel_booking(db_session, 1)

    assert result.status == "cancelled"
    assert result.refund_amount == Decimal("20.00")
    assert result.penalty_amount == Decimal("0.00")
    assert result.cancel_policy == "full_refund"
    balance = (
        await db_session.execute(select(User.balance).where(User.id == USER_ID))
    ).scalar_one()
    assert Decimal(str(balance)) == Decimal("20.00")

    # 订单专属排课与课时记录被删除，外键引用清空
    booking_row = (
        await db_session.execute(select(Booking).where(Booking.id == 1))
    ).scalar_one()
    assert booking_row.schedule_id is None
    assert (
        await db_session.execute(select(CourseSchedule).where(CourseSchedule.id == 1))
    ).scalar_one_or_none() is None
    assert (
        await db_session.execute(
            select(LessonSchedule).where(LessonSchedule.schedule_id == 1)
        )
    ).scalars().all() == []

    transaction = (
        await db_session.execute(
            select(WalletTransaction).where(
                WalletTransaction.booking_id == 1,
                WalletTransaction.type == "booking_refund",
            )
        )
    ).scalar_one()
    assert transaction.amount == Decimal("20.00")


@pytest.mark.asyncio
async def test_admin_cancel_course_pending_booking_keeps_shared_schedule(
    db_session: AsyncSession,
):
    _make_room(db_session, 1)
    _make_user(db_session)
    _make_course_data(db_session)
    _make_course_booking(db_session, 1)
    # 另一个非取消订单引用同一排课（共享场景）
    _make_course_booking(db_session, 2, status="in_progress")
    await db_session.flush()

    result = await admin_cancel_booking(db_session, 1)

    assert result.status == "cancelled"
    assert result.refund_amount == Decimal("20.00")
    # 共享排课与课时保留，仅取消订单的引用被清空
    assert (
        await db_session.execute(select(CourseSchedule).where(CourseSchedule.id == 1))
    ).scalar_one_or_none() is not None
    assert len(
        (
            await db_session.execute(
                select(LessonSchedule).where(LessonSchedule.schedule_id == 1)
            )
        ).scalars().all()
    ) == 1
    other = (
        await db_session.execute(select(Booking).where(Booking.id == 2))
    ).scalar_one()
    assert other.schedule_id == 1


@pytest.mark.asyncio
async def test_admin_cancel_course_pending_booking_keeps_fixed_schedule(
    db_session: AsyncSession,
):
    """固定班课（schedule_type=fixed）订单取消时不得删除 fixed 排课与课时记录。"""
    _make_room(db_session, 1)
    _make_user(db_session)
    course, schedule = _make_course_data(db_session)
    schedule.schedule_type = "fixed"
    booking = _make_course_booking(db_session, 1)
    booking.schedule_type = "fixed"
    booking.time_slots = None
    booking.teacher_id = None
    await db_session.flush()

    result = await admin_cancel_booking(db_session, 1)

    assert result.status == "cancelled"
    assert result.refund_amount == Decimal("20.00")
    # fixed 排课与课时记录必须保留，仅清空订单外键引用
    kept_schedule = (
        await db_session.execute(select(CourseSchedule).where(CourseSchedule.id == 1))
    ).scalar_one_or_none()
    assert kept_schedule is not None
    assert kept_schedule.schedule_type == "fixed"
    assert len(
        (
            await db_session.execute(
                select(LessonSchedule).where(LessonSchedule.schedule_id == 1)
            )
        ).scalars().all()
    ) == 1
    booking_row = (
        await db_session.execute(select(Booking).where(Booking.id == 1))
    ).scalar_one()
    # 非 custom 排课不做任何清理，订单引用保持不变（与共享排课早退行为一致）
    assert booking_row.schedule_id == 1


@pytest.mark.asyncio
async def test_admin_list_bookings_includes_booking_type_fields(db_session: AsyncSession):
    _make_room(db_session, 1)
    _make_user(db_session)
    _make_course_data(db_session)
    _make_course_booking(db_session, 1)
    await db_session.flush()

    result = await admin_list_bookings(db_session)
    item = result.items[0]
    assert item.booking_type == "course"
    assert item.schedule_type == "custom"
    assert item.time_slots == '[{"weekday": 3, "time_slot": "10:00-12:00"}]'


@pytest.mark.asyncio
async def test_admin_confirm_custom_booking_future_first_lesson_pending(db_session: AsyncSession):
    """确认定制订单：第一课时日期在未来 → 待开始，且预约/开课日期取第一课时日期。"""
    _make_room(db_session, 1)
    _make_user(db_session)
    _make_course_data(db_session)

    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    base_date = today + timedelta(days=10)
    # 第一课时日期 = 基准日期起第一个匹配 weekday=3 的日期
    first_lesson_date = base_date + timedelta(days=(3 - base_date.isoweekday()) % 7)

    booking = _make_course_booking(db_session, 1, schedule_id=None, status="pending_confirm")
    booking.date = base_date
    booking.lesson_ids = [1]
    await db_session.flush()

    result = await admin_confirm_booking(db_session, 1)

    assert result.status == "pending_start"
    booking_row = (
        await db_session.execute(select(Booking).where(Booking.id == 1))
    ).scalar_one()
    # 预约日期回写为第一课时日期，并关联新建的定制排课
    assert booking_row.date == first_lesson_date
    assert booking_row.schedule_id is not None
    schedule = (
        await db_session.execute(
            select(CourseSchedule).where(CourseSchedule.id == booking_row.schedule_id)
        )
    ).scalar_one()
    # 开课日期同步为第一课时日期
    assert schedule.start_date == first_lesson_date
    lessons = (
        await db_session.execute(
            select(LessonSchedule).where(LessonSchedule.schedule_id == schedule.id)
        )
    ).scalars().all()
    assert len(lessons) == 1
    assert lessons[0].lesson_date == first_lesson_date


@pytest.mark.asyncio
async def test_admin_confirm_custom_booking_first_lesson_today_confirmed(db_session: AsyncSession):
    """确认定制订单：第一课时日期 <= 今天 → 进行中（confirmed）。"""
    _make_room(db_session, 1)
    _make_user(db_session)
    _make_course_data(db_session)

    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    booking = _make_course_booking(db_session, 1, schedule_id=None, status="pending_confirm")
    booking.date = today
    # 时间段星期与基准日期一致 → 第一课时日期即今天
    booking.time_slots = f'[{{"weekday": {today.isoweekday()}, "time_slot": "10:00-12:00"}}]'
    booking.lesson_ids = [1]
    await db_session.flush()

    result = await admin_confirm_booking(db_session, 1)

    assert result.status == "in_progress"
    booking_row = (
        await db_session.execute(select(Booking).where(Booking.id == 1))
    ).scalar_one()
    assert booking_row.date == today


@pytest.mark.asyncio
async def test_admin_confirm_custom_booking_records_paid_amount_separately(
    db_session: AsyncSession,
):
    """确认定制订单：已支付金额记入 paid_amount，定制每课时价格取课程固定班课排课。

    回归 br-admin /booking/list “确认”按钮把订单实付总额误写入
    course_schedules.custom_price（定制每课时价格）的问题。
    """
    _make_room(db_session, 1)
    _make_user(db_session)
    _make_course_data(db_session)
    # 课程固定班课排课：C 端下单计价来源，定制每课时价格与订单实付总额明显不同
    db_session.add(
        CourseSchedule(
            id=2,
            course_id=1,
            teacher_id=1,
            start_date=date(2026, 5, 10),
            time_slots='[{"weekday": 3, "time_slot": "10:00-12:00"}]',
            price=Decimal("80.00"),
            custom_price=Decimal("120.00"),
            schedule_type="fixed",
            schedule_status="in_progress",
        )
    )

    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    booking = _make_course_booking(db_session, 1, schedule_id=None, status="pending_confirm")
    booking.date = today
    # 时间段星期与基准日期一致 → 第一课时日期即今天
    booking.time_slots = f'[{{"weekday": {today.isoweekday()}, "time_slot": "10:00-12:00"}}]'
    booking.lesson_ids = [1]
    booking.total_price = Decimal("360.00")
    await db_session.flush()

    await admin_confirm_booking(db_session, 1)

    booking_row = (
        await db_session.execute(select(Booking).where(Booking.id == 1))
    ).scalar_one()
    schedule = (
        await db_session.execute(
            select(CourseSchedule).where(CourseSchedule.id == booking_row.schedule_id)
        )
    ).scalar_one()
    assert schedule.schedule_type == "custom"
    # 已支付金额 = 订单实付总额
    assert schedule.paid_amount == Decimal("360.00")
    # 定制每课时价格 = 课程固定班课排课的定制价，不再是订单实付总额
    assert schedule.custom_price == Decimal("120.00")
