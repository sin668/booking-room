from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app.services.booking_cancellation_policy import calculate_cancellation_policy


def _policy(hours_before_start: int | float, total: Decimal = Decimal("100.00")):
    now = datetime(2026, 5, 28, 12, 0, 0)
    start_at = now + timedelta(hours=hours_before_start)
    return calculate_cancellation_policy(
        total_price=total,
        booking_date=start_at.date(),
        start_time=start_at.time(),
        now=now,
    )


def test_over_48_hours_full_refund():
    result = _policy(49)

    assert result.policy == "over_48h"
    assert result.penalty_amount == Decimal("0.00")
    assert result.refund_amount == Decimal("100.00")
    assert result.can_cancel is True


def test_exact_48_hours_charges_10_percent():
    result = _policy(48)

    assert result.policy == "24h_48h"
    assert result.penalty_amount == Decimal("10.00")
    assert result.refund_amount == Decimal("90.00")


def test_exact_24_hours_charges_20_percent():
    result = _policy(24)

    assert result.policy == "2h_24h"
    assert result.penalty_amount == Decimal("20.00")
    assert result.refund_amount == Decimal("80.00")


def test_exact_2_hours_charges_50_percent():
    result = _policy(2)

    assert result.policy == "within_2h"
    assert result.penalty_amount == Decimal("50.00")
    assert result.refund_amount == Decimal("50.00")


def test_started_booking_cannot_cancel():
    result = calculate_cancellation_policy(
        total_price=Decimal("100.00"),
        booking_date=date(2026, 5, 28),
        start_time=time(12, 0, 0),
        now=datetime(2026, 5, 28, 12, 0, 0),
    )

    assert result.policy == "started"
    assert result.can_cancel is False
    assert result.refund_amount == Decimal("0.00")


def test_non_round_amount_keeps_penalty_and_refund_balanced():
    result = _policy(36, Decimal("33.33"))

    assert result.penalty_amount == Decimal("3.33")
    assert result.refund_amount == Decimal("30.00")
    assert result.penalty_amount + result.refund_amount == Decimal("33.33")
