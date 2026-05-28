from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo


MONEY = Decimal("0.01")
DEFAULT_BOOKING_TIMEZONE = "Asia/Shanghai"


@dataclass(frozen=True)
class CancellationPolicyResult:
    policy: str
    penalty_amount: Decimal
    refund_amount: Decimal
    can_cancel: bool


def booking_start_datetime(booking_date: date, start_time: time) -> datetime:
    return datetime.combine(booking_date, start_time)


def booking_now(timezone: str = DEFAULT_BOOKING_TIMEZONE) -> datetime:
    return datetime.now(ZoneInfo(timezone)).replace(tzinfo=None)


def calculate_cancellation_policy(
    *,
    total_price: Decimal,
    booking_date: date,
    start_time: time,
    now: datetime | None = None,
) -> CancellationPolicyResult:
    current_time = now or booking_now()
    start_at = booking_start_datetime(booking_date, start_time)
    remaining_seconds = (start_at - current_time).total_seconds()
    total = Decimal(str(total_price)).quantize(MONEY, rounding=ROUND_HALF_UP)

    if remaining_seconds <= 0:
        return CancellationPolicyResult(
            policy="started",
            penalty_amount=total,
            refund_amount=Decimal("0.00"),
            can_cancel=False,
        )

    remaining_hours = Decimal(str(remaining_seconds)) / Decimal("3600")
    if remaining_hours > Decimal("48"):
        policy = "over_48h"
        rate = Decimal("0")
    elif remaining_hours > Decimal("24"):
        policy = "24h_48h"
        rate = Decimal("0.10")
    elif remaining_hours > Decimal("2"):
        policy = "2h_24h"
        rate = Decimal("0.20")
    else:
        policy = "within_2h"
        rate = Decimal("0.50")

    penalty = (total * rate).quantize(MONEY, rounding=ROUND_HALF_UP)
    refund = (total - penalty).quantize(MONEY, rounding=ROUND_HALF_UP)
    return CancellationPolicyResult(
        policy=policy,
        penalty_amount=penalty,
        refund_amount=refund,
        can_cancel=True,
    )
