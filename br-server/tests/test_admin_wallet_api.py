"""Tests for admin wallet API routes."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.routes.admin_wallet import export_transactions


async def test_export_transactions_returns_400_when_result_exceeds_limit() -> None:
    db = AsyncMock()
    count_result = MagicMock()
    count_result.scalar_one.return_value = 10001
    db.execute.return_value = count_result

    with pytest.raises(HTTPException) as exc_info:
        await export_transactions(
            type="recharge",
            transaction_status="completed",
            user_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            date_start=date(2026, 5, 1),
            date_end=date(2026, 5, 31),
            db=db,
        )

    assert exc_info.value.status_code == 400
    assert "10000" in exc_info.value.detail
    count_stmt = db.execute.await_args.args[0]
    count_sql = str(count_stmt)
    assert "wallet_transactions.status" in count_sql
    assert "wallet_transactions.created_at >=" in count_sql
    assert "wallet_transactions.created_at <=" in count_sql
