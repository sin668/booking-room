from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PaymentMethodEnum(str, Enum):
    balance = "balance"
    wechat = "wechat"


class PaymentStatusEnum(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


class SeatBrief(BaseModel):
    id: int
    seat_number: str
    zone: str
    position: str | None
    price_per_hour: Decimal

    model_config = ConfigDict(from_attributes=True)


class RoomBrief(BaseModel):
    id: int
    name: str
    address: str

    model_config = ConfigDict(from_attributes=True)


class LessonScheduleBrief(BaseModel):
    """课时安排简要信息。"""
    id: int
    lesson_id: int
    lesson_date: Optional[date] = None
    lesson_time_slot: str
    lesson_title: str | None = None
    sort_order: int = 0
    schedule_type: str | None = None
    schedule_status: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    seat_id: int
    date: date
    start_time: time
    end_time: time
    coupon_id: int | None = None
    payment_method: PaymentMethodEnum = PaymentMethodEnum.balance


class BookingResponse(BaseModel):
    id: int
    seat_id: int | None = None
    user_id: str
    room_id: int
    date: date
    start_time: time
    end_time: time
    status: str
    original_price: Decimal
    discount_amount: Decimal
    total_price: Decimal
    coupon_id: int | None
    payment_method: str
    payment_status: str
    payment_provider: str | None = None
    paid_at: datetime | None = None
    cancelled_at: datetime | None = None
    penalty_amount: Decimal = Decimal("0.00")
    refund_amount: Decimal = Decimal("0.00")
    cancel_policy: str | None = None
    refund_transaction_id: UUID | None = None
    cancel_penalty_amount: Decimal = Decimal("0.00")
    cancel_refund_amount: Decimal = Decimal("0.00")
    can_cancel: bool = False
    created_at: datetime
    seat: SeatBrief | None = None
    room: RoomBrief
    # 课程预约扩展字段
    booking_type: str = "seat"
    course_id: int | None = None
    course_name: str | None = None
    lesson_titles: list[str] | None = None
    teacher_name: str | None = None
    teacher_avatar: str | None = None
    schedule: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    started: bool | None = None
    lesson_schedules: list[LessonScheduleBrief] | None = None
    highlighted_lesson_id: int | None = None
    schedule_type: str | None = None

    model_config = ConfigDict(from_attributes=True)


class WeChatPaymentParams(BaseModel):
    timeStamp: str
    nonceStr: str
    package: str
    signType: str
    paySign: str


class CreateBookingResponse(BookingResponse):
    payment_params: WeChatPaymentParams | None = None


class PaymentStatusResponse(BaseModel):
    booking_id: int
    payment_status: str
    paid_at: datetime | None = None
    transaction_id: str | None = None


class PayPendingBooking(BaseModel):
    payment_method: PaymentMethodEnum = PaymentMethodEnum.balance


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    page: int
    page_size: int


class BookingAdminResponse(BaseModel):
    id: int
    user_id: str
    user_nickname: str | None = None
    room_id: int
    seat_id: int | None = None
    date: date
    start_time: time
    end_time: time
    status: str
    original_price: Decimal
    discount_amount: Decimal
    total_price: Decimal
    coupon_id: int | None
    payment_method: str
    payment_status: str
    payment_provider: str | None = None
    paid_at: datetime | None = None
    cancelled_at: datetime | None = None
    penalty_amount: Decimal = Decimal("0.00")
    refund_amount: Decimal = Decimal("0.00")
    cancel_policy: str | None = None
    booking_type: str = "seat"
    schedule_type: str | None = None
    time_slots: str | None = None
    course_name: str | None = None
    lesson_titles: list[str] | None = None
    created_at: datetime
    updated_at: datetime
    seat: SeatBrief | None = None
    room: RoomBrief | None = None

    model_config = ConfigDict(from_attributes=True)


class BookingAdminListResponse(BaseModel):
    items: list[BookingAdminResponse]
    total: int
    page: int
    page_size: int


class AdminUserBrief(BaseModel):
    """订单详情-用户信息。"""

    id: str
    nickname: str | None = None
    phone: str | None = None
    avatar: str | None = None


class AdminCourseBrief(BaseModel):
    """订单详情-课程信息。"""

    id: int
    name: str
    category: str


class AdminTeacherBrief(BaseModel):
    """订单详情-授课老师信息。"""

    id: int
    name: str
    avatar: str | None = None


class AdminScheduleBrief(BaseModel):
    """订单详情-排课记录信息。"""

    id: int
    start_date: date | None = None
    end_date: date | None = None
    schedule_type: str
    schedule_status: str
    time_slots: str | None = None


class AdminLessonScheduleItem(BaseModel):
    """订单详情-课时安排条目。"""

    id: int
    lesson_id: int
    lesson_title: str | None = None
    lesson_date: date | None = None
    lesson_time_slot: str
    sort_order: int = 0


class AdminCouponBrief(BaseModel):
    """订单详情-优惠券信息。"""

    user_coupon_id: int
    coupon_id: int
    name: str | None = None
    type: str | None = None
    discount_amount: Decimal | None = None
    discount_percent: int | None = None


class AdminRefundTransaction(BaseModel):
    """订单详情-退款流水信息。"""

    id: UUID
    amount: Decimal
    balance_after: Decimal | None = None
    payment_method: str | None = None
    created_at: datetime | None = None


class BookingAdminDetailResponse(BookingAdminResponse):
    """管理员订单详情：订单字段 + 关联表聚合信息。"""

    lesson_ids: list[int] | None = None
    highlighted_lesson_id: int | None = None
    schedule_id: int | None = None
    teacher_id: int | None = None
    prepay_id: str | None = None
    transaction_id: str | None = None
    payment_check_count: int = 0
    user: AdminUserBrief | None = None
    course: AdminCourseBrief | None = None
    teacher: AdminTeacherBrief | None = None
    schedule: AdminScheduleBrief | None = None
    lesson_schedules: list[AdminLessonScheduleItem] = []
    coupon: AdminCouponBrief | None = None
    refund_transaction: AdminRefundTransaction | None = None
