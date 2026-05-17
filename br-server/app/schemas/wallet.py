from decimal import Decimal
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RechargeRequest(BaseModel):
    amount: float = Field(gt=0, le=9999, description="Recharge amount")
    payment_method: str = Field(
        pattern="^(wechat|alipay)$",
        description="Payment method: wechat or alipay",
    )
    promo_code: str | None = Field(default=None, description="Promo code")


class PaymentParams(BaseModel):
    timeStamp: str
    nonceStr: str
    package: str
    signType: str
    paySign: str


class RechargeResponse(BaseModel):
    order_id: UUID
    amount: Decimal
    bonus_amount: Decimal = Decimal("0")
    status: str
    balance_after: Decimal | None = None
    payment_provider: str | None = None
    payment_status: str | None = None
    payment_params: PaymentParams | None = None

    model_config = ConfigDict(from_attributes=True)


class RechargeOrderResponse(BaseModel):
    order_id: UUID
    amount: Decimal
    bonus_amount: Decimal = Decimal("0")
    status: str
    payment_provider: str | None = None
    payment_status: str
    balance_after: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)


class BalanceResponse(BaseModel):
    balance: Decimal
    total_recharged: Decimal

    model_config = ConfigDict(from_attributes=True)


WalletTransactionType = Literal["all", "recharge", "consume", "refund"]


class WalletTransactionResponse(BaseModel):
    id: UUID
    type: str
    title: str
    amount: Decimal
    bonus_amount: Decimal = Decimal("0")
    direction: str
    status: str
    payment_method: str | None = None
    balance_after: Decimal | None = None
    created_at: datetime
    completed_at: datetime | None = None
    order_id: UUID


class WalletTransactionListResponse(BaseModel):
    items: list[WalletTransactionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class PromoCodeRequest(BaseModel):
    code: str = Field(min_length=1, description="Promo code")


class PromoCodeResponse(BaseModel):
    code: str
    description: str
    bonus_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class WechatNotifyAmount(BaseModel):
    total: int
    currency: str


class WechatDecryptedNotify(BaseModel):
    appid: str
    mchid: str
    out_trade_no: str
    transaction_id: str
    trade_state: str
    success_time: str | None = None
    amount: WechatNotifyAmount
