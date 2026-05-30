from __future__ import annotations

from datetime import datetime
from typing import Protocol


class TransactionLike(Protocol):
    status: str
    created_at: datetime
    paid_at: datetime | None
    notify_processed_at: datetime | None


def transaction_title(transaction_type: str, status: str) -> str:
    if transaction_type == "recharge":
        return {
            "completed": "充值到账",
            "pending": "充值待支付",
            "failed": "充值失败",
        }.get(status, "钱包充值")
    if transaction_type == "consume":
        return "钱包消费"
    if transaction_type == "refund":
        return "钱包退款"
    if transaction_type == "booking_refund":
        return "取消退款"
    return "钱包流水"


def transaction_direction(transaction_type: str) -> str:
    if transaction_type == "consume":
        return "expense"
    return "income"


def admin_wallet_base_statuses() -> tuple[str, str]:
    return ("completed", "failed")


def transaction_completed_at(transaction: TransactionLike) -> datetime | None:
    if transaction.paid_at is not None:
        return transaction.paid_at
    if transaction.status == "completed":
        return transaction.notify_processed_at or transaction.created_at
    return None
