from datetime import datetime
from types import SimpleNamespace

from app.domain.wallet_rules import (
    admin_wallet_base_statuses,
    transaction_completed_at,
    transaction_direction,
    transaction_title,
)


def test_transaction_title_maps_recharge_status():
    assert transaction_title("recharge", "completed") == "充值到账"
    assert transaction_title("recharge", "pending") == "充值待支付"
    assert transaction_title("recharge", "failed") == "充值失败"


def test_transaction_title_maps_wallet_business_types():
    assert transaction_title("consume", "completed") == "钱包消费"
    assert transaction_title("refund", "completed") == "钱包退款"
    assert transaction_title("booking_refund", "completed") == "取消退款"
    assert transaction_title("unknown", "completed") == "钱包流水"


def test_transaction_direction_marks_consume_as_expense():
    assert transaction_direction("consume") == "expense"
    assert transaction_direction("refund") == "income"


def test_admin_wallet_base_statuses_excludes_pending():
    assert admin_wallet_base_statuses() == ("completed", "failed")


def test_transaction_completed_at_prefers_paid_at():
    paid_at = datetime(2026, 5, 30, 10, 0)
    created_at = datetime(2026, 5, 30, 9, 0)
    transaction = SimpleNamespace(
        paid_at=paid_at,
        notify_processed_at=None,
        created_at=created_at,
        status="completed",
    )

    assert transaction_completed_at(transaction) == paid_at


def test_transaction_completed_at_uses_notify_or_created_for_completed_transaction():
    notify_processed_at = datetime(2026, 5, 30, 10, 5)
    created_at = datetime(2026, 5, 30, 9, 0)
    transaction = SimpleNamespace(
        paid_at=None,
        notify_processed_at=notify_processed_at,
        created_at=created_at,
        status="completed",
    )

    assert transaction_completed_at(transaction) == notify_processed_at
