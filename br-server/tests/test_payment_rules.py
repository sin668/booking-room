from datetime import timedelta
from decimal import Decimal

from app.domain.payment_rules import (
    PAYMENT_QUERY_DELAYS,
    failed_trade_states,
    is_failed_trade_state,
    is_pending_trade_state,
    money_to_cents,
    next_payment_check_delay,
    pending_trade_states,
)


def test_money_to_cents_rounds_half_up():
    assert money_to_cents(Decimal("10.235")) == 1024
    assert money_to_cents(Decimal("0.01")) == 1


def test_trade_state_sets_are_explicit():
    assert pending_trade_states() == {"NOTPAY", "USERPAYING", "ACCEPT"}
    assert failed_trade_states() == {"CLOSED", "REVOKED", "PAYERROR", "REFUND"}


def test_trade_state_predicates():
    assert is_pending_trade_state("NOTPAY") is True
    assert is_pending_trade_state("SUCCESS") is False
    assert is_failed_trade_state("PAYERROR") is True
    assert is_failed_trade_state("SUCCESS") is False


def test_next_payment_check_delay_uses_configured_sequence():
    assert next_payment_check_delay(0) == timedelta(minutes=1)
    assert next_payment_check_delay(1) == timedelta(minutes=3)
    assert next_payment_check_delay(2) == timedelta(minutes=5)
    assert next_payment_check_delay(99) is None


def test_payment_query_delays_are_stable():
    assert PAYMENT_QUERY_DELAYS == (
        timedelta(minutes=1),
        timedelta(minutes=3),
        timedelta(minutes=5),
    )
