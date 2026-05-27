from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

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


class BookingCreate(BaseModel):
    seat_id: int
    date: date
    start_time: time
    end_time: time
    coupon_id: int | None = None
    payment_method: PaymentMethodEnum = PaymentMethodEnum.balance


class BookingResponse(BaseModel):
    id: int
    seat_id: int
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
    created_at: datetime
    seat: SeatBrief
    room: RoomBrief

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


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int
    page: int
    page_size: int


class BookingAdminResponse(BaseModel):
    id: int
    user_id: str
    room_id: int
    seat_id: int
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
    created_at: datetime
    updated_at: datetime
    seat: SeatBrief
    room: RoomBrief

    model_config = ConfigDict(from_attributes=True)


class BookingAdminListResponse(BaseModel):
    items: list[BookingAdminResponse]
    total: int
    page: int
    page_size: int
