from __future__ import annotations

from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP


PAYMENT_QUERY_DELAYS = (
    timedelta(minutes=1),
    timedelta(minutes=3),
    timedelta(minutes=5),
)

PENDING_TRADE_STATES = {"NOTPAY", "USERPAYING", "ACCEPT"}
FAILED_TRADE_STATES = {"CLOSED", "REVOKED", "PAYERROR", "REFUND"}


def money_to_cents(amount: Decimal) -> int:
    cents = (amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def pending_trade_states() -> set[str]:
    return set(PENDING_TRADE_STATES)


def failed_trade_states() -> set[str]:
    return set(FAILED_TRADE_STATES)


def is_pending_trade_state(value: str) -> bool:
    return value in PENDING_TRADE_STATES


def is_failed_trade_state(value: str) -> bool:
    return value in FAILED_TRADE_STATES


def next_payment_check_delay(check_count: int) -> timedelta | None:
    if check_count < 0 or check_count >= len(PAYMENT_QUERY_DELAYS):
        return None
    return PAYMENT_QUERY_DELAYS[check_count]
