from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RechargeRequest(BaseModel):
    amount: float = Field(gt=0, le=9999, description="充值金额")
    payment_method: str = Field(pattern="^(wechat|alipay)$", description="支付方式: wechat 或 alipay")
    promo_code: str | None = Field(default=None, description="优惠码")


class RechargeResponse(BaseModel):
    order_id: UUID
    amount: Decimal
    bonus_amount: Decimal = Decimal("0")
    status: str
    balance_after: Decimal | None = None

    model_config = ConfigDict(from_attributes=True)


class BalanceResponse(BaseModel):
    balance: Decimal
    total_recharged: Decimal

    model_config = ConfigDict(from_attributes=True)


class PromoCodeRequest(BaseModel):
    code: str = Field(min_length=1, description="优惠码")


class PromoCodeResponse(BaseModel):
    code: str
    description: str
    bonus_amount: Decimal

    model_config = ConfigDict(from_attributes=True)
