# br-server Clean Architecture 重构实施计划

> **给执行代理的要求：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐项执行。本计划使用复选框语法跟踪进度。

**目标：** 在不改变现有 API 行为的前提下，把 `br-server` 中预约、钱包、支付、核销相关的核心业务规则逐步提取到清晰的领域层与应用层。

**架构：** 第一阶段采用低风险迁移：先提取纯领域规则，再把现有 `services` 作为兼容门面调用新模块。路由、响应模型和数据库结构保持不变，所有行为由现有测试和新增小测试保护。

**技术栈：** Python 3.12、FastAPI、SQLAlchemy AsyncSession、pytest、pytest-asyncio、Pydantic。

---

## 文件结构

第一阶段新增这些目录和文件：

- 新增：`br-server/app/domain/__init__.py`
- 新增：`br-server/app/domain/booking_rules.py`
- 新增：`br-server/app/domain/wallet_rules.py`
- 新增：`br-server/app/domain/payment_rules.py`
- 新增：`br-server/app/domain/verification_rules.py`
- 新增：`br-server/tests/test_booking_rules.py`
- 新增：`br-server/tests/test_wallet_rules.py`
- 新增：`br-server/tests/test_payment_rules.py`
- 新增：`br-server/tests/test_verification_rules.py`

第一阶段修改这些现有文件：

- 修改：`br-server/app/services/booking_service.py`
- 修改：`br-server/app/services/wallet_service.py`
- 修改：`br-server/app/services/booking_payment_service.py`
- 修改：`br-server/app/services/booking_verification_service.py`

第二阶段再引入仓储和用例层，避免一次性迁移过大：

- 新增：`br-server/app/repositories/__init__.py`
- 新增：`br-server/app/repositories/booking_repository.py`
- 新增：`br-server/app/repositories/wallet_repository.py`
- 新增：`br-server/app/application/__init__.py`
- 新增：`br-server/app/application/booking_use_cases.py`
- 新增：`br-server/app/application/wallet_use_cases.py`

---

## 任务 1：建立基线验证

**文件：**
- 不创建文件
- 不修改业务代码

- [ ] **步骤 1：运行支付服务测试**

运行：

```powershell
python -m pytest tests/test_booking_payment_service.py -q
```

期望：测试通过；如果失败，记录失败用例和错误信息，不进入重构。

- [ ] **步骤 2：运行钱包服务测试**

运行：

```powershell
python -m pytest tests/test_wallet_service.py -q
```

期望：测试通过；如果失败，记录失败用例和错误信息，不进入重构。

- [ ] **步骤 3：运行预约核销服务测试**

运行：

```powershell
python -m pytest tests/test_booking_verification_service.py -q
```

期望：测试通过；如果失败，记录失败用例和错误信息，不进入重构。

- [ ] **步骤 4：运行预约 API 测试**

运行：

```powershell
python -m pytest tests/test_api_booking.py -q
```

期望：测试通过；如果失败，记录失败用例和错误信息，不进入重构。

- [ ] **步骤 5：提交基线记录**

如果没有代码改动，不提交。如果需要记录当前失败，新增 `docs/superpowers/verification/br-server-baseline-2026-05-30.md`，内容格式如下：

```markdown
# br-server 重构基线验证

- `python -m pytest tests/test_booking_payment_service.py -q`：通过
- `python -m pytest tests/test_wallet_service.py -q`：通过
- `python -m pytest tests/test_booking_verification_service.py -q`：通过
- `python -m pytest tests/test_api_booking.py -q`：通过
```

提交命令：

```powershell
git add docs/superpowers/verification/br-server-baseline-2026-05-30.md
git commit -m "docs: record br-server refactor baseline"
```

---

## 任务 2：提取预约时间与完成状态规则

**文件：**
- 新增：`br-server/app/domain/__init__.py`
- 新增：`br-server/app/domain/booking_rules.py`
- 新增：`br-server/tests/test_booking_rules.py`
- 修改：`br-server/app/services/booking_service.py`

- [ ] **步骤 1：写失败测试**

创建 `br-server/tests/test_booking_rules.py`：

```python
from datetime import date, datetime, time

from app.domain.booking_rules import (
    BookingCompletionInput,
    calculate_booking_hours,
    can_cancel_paid_booking,
    has_booking_started,
    should_mark_booking_completed,
)


def test_calculate_booking_hours_returns_fractional_hours():
    result = calculate_booking_hours(time(8, 30), time(11, 0))

    assert result == 2.5


def test_has_booking_started_uses_booking_date_and_start_time():
    result = has_booking_started(
        booking_date=date(2026, 5, 30),
        start_time=time(9, 0),
        now=datetime(2026, 5, 30, 9, 0),
    )

    assert result is True


def test_can_cancel_paid_booking_requires_confirmed_paid_and_not_started():
    result = can_cancel_paid_booking(
        status="confirmed",
        payment_status="paid",
        booking_date=date(2026, 5, 30),
        start_time=time(10, 0),
        now=datetime(2026, 5, 30, 9, 0),
    )

    assert result is True


def test_can_cancel_paid_booking_rejects_started_booking():
    result = can_cancel_paid_booking(
        status="confirmed",
        payment_status="paid",
        booking_date=date(2026, 5, 30),
        start_time=time(9, 0),
        now=datetime(2026, 5, 30, 9, 0),
    )

    assert result is False


def test_should_mark_booking_completed_only_for_started_confirmed_paid_booking():
    result = should_mark_booking_completed(
        BookingCompletionInput(
            status="confirmed",
            payment_status="paid",
            booking_date=date(2026, 5, 30),
            start_time=time(9, 0),
            now=datetime(2026, 5, 30, 9, 1),
        )
    )

    assert result is True
```

- [ ] **步骤 2：确认测试失败**

运行：

```powershell
python -m pytest tests/test_booking_rules.py -q
```

期望：失败，错误为 `ModuleNotFoundError: No module named 'app.domain'` 或无法导入 `calculate_booking_hours`。

- [ ] **步骤 3：写最小实现**

创建 `br-server/app/domain/__init__.py`：

```python
"""领域规则模块。"""
```

创建 `br-server/app/domain/booking_rules.py`：

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time


@dataclass(frozen=True)
class BookingCompletionInput:
    status: str
    payment_status: str
    booking_date: date
    start_time: time
    now: datetime


def calculate_booking_hours(start_time: time, end_time: time) -> float:
    start_seconds = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
    end_seconds = end_time.hour * 3600 + end_time.minute * 60 + end_time.second
    return (end_seconds - start_seconds) / 3600.0


def has_booking_started(
    *,
    booking_date: date,
    start_time: time,
    now: datetime,
) -> bool:
    return datetime.combine(booking_date, start_time) <= now


def can_cancel_paid_booking(
    *,
    status: str,
    payment_status: str,
    booking_date: date,
    start_time: time,
    now: datetime,
) -> bool:
    if status != "confirmed" or payment_status != "paid":
        return False
    return not has_booking_started(
        booking_date=booking_date,
        start_time=start_time,
        now=now,
    )


def should_mark_booking_completed(value: BookingCompletionInput) -> bool:
    return (
        value.status == "confirmed"
        and value.payment_status == "paid"
        and has_booking_started(
            booking_date=value.booking_date,
            start_time=value.start_time,
            now=value.now,
        )
    )
```

- [ ] **步骤 4：确认新测试通过**

运行：

```powershell
python -m pytest tests/test_booking_rules.py -q
```

期望：全部通过。

- [ ] **步骤 5：接入 `booking_service.py`**

在 `br-server/app/services/booking_service.py` 增加导入：

```python
from app.domain.booking_rules import (
    BookingCompletionInput,
    calculate_booking_hours,
    can_cancel_paid_booking,
    should_mark_booking_completed,
)
```

替换 `_calculate_hours` 实现：

```python
def _calculate_hours(start_time: time, end_time: time) -> float:
    return calculate_booking_hours(start_time, end_time)
```

替换 `_sync_booking_completion` 实现：

```python
def _sync_booking_completion(booking: Booking, now: datetime | None = None) -> bool:
    current_time = now or booking_now(settings.BOOKING_TIMEZONE)
    should_complete = should_mark_booking_completed(
        BookingCompletionInput(
            status=booking.status,
            payment_status=booking.payment_status,
            booking_date=booking.date,
            start_time=booking.start_time,
            now=current_time,
        )
    )
    if should_complete:
        booking.status = "completed"
        return True
    return False
```

替换 `_can_cancel_booking` 实现：

```python
def _can_cancel_booking(booking: Booking, now: datetime | None = None) -> bool:
    current_time = now or booking_now(settings.BOOKING_TIMEZONE)
    return can_cancel_paid_booking(
        status=booking.status,
        payment_status=booking.payment_status,
        booking_date=booking.date,
        start_time=booking.start_time,
        now=current_time,
    )
```

- [ ] **步骤 6：运行受影响测试**

运行：

```powershell
python -m pytest tests/test_booking_rules.py tests/test_api_booking.py tests/test_admin_booking_service.py -q
```

期望：全部通过。

- [ ] **步骤 7：提交**

```powershell
git add br-server/app/domain/__init__.py br-server/app/domain/booking_rules.py br-server/app/services/booking_service.py br-server/tests/test_booking_rules.py
git commit -m "refactor: extract booking domain rules"
```

---

## 任务 3：提取钱包流水展示规则

**文件：**
- 新增：`br-server/app/domain/wallet_rules.py`
- 新增：`br-server/tests/test_wallet_rules.py`
- 修改：`br-server/app/services/wallet_service.py`

- [ ] **步骤 1：写失败测试**

创建 `br-server/tests/test_wallet_rules.py`：

```python
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
```

- [ ] **步骤 2：确认测试失败**

运行：

```powershell
python -m pytest tests/test_wallet_rules.py -q
```

期望：失败，错误为无法导入 `app.domain.wallet_rules`。

- [ ] **步骤 3：写最小实现**

创建 `br-server/app/domain/wallet_rules.py`：

```python
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
```

- [ ] **步骤 4：确认新测试通过**

运行：

```powershell
python -m pytest tests/test_wallet_rules.py -q
```

期望：全部通过。

- [ ] **步骤 5：接入 `wallet_service.py`**

在 `br-server/app/services/wallet_service.py` 增加导入：

```python
from app.domain.wallet_rules import (
    admin_wallet_base_statuses,
    transaction_completed_at,
    transaction_direction,
    transaction_title,
)
```

替换私有函数实现：

```python
def _transaction_title(transaction_type: str, status: str) -> str:
    return transaction_title(transaction_type, status)


def _transaction_direction(transaction_type: str) -> str:
    return transaction_direction(transaction_type)


def _admin_wallet_base_conditions() -> list:
    return [WalletTransaction.status.in_(admin_wallet_base_statuses())]


def _transaction_completed_at(transaction: WalletTransaction) -> datetime | None:
    return transaction_completed_at(transaction)
```

- [ ] **步骤 6：运行受影响测试**

运行：

```powershell
python -m pytest tests/test_wallet_rules.py tests/test_wallet_service.py tests/test_api_wallet.py -q
```

期望：全部通过。若管理端钱包列表测试依赖“排除 pending”语义，也运行：

```powershell
python -m pytest tests/test_api_admin_wallet.py -q
```

期望：全部通过；如果该测试文件不存在，跳过并记录不存在。

- [ ] **步骤 7：提交**

```powershell
git add br-server/app/domain/wallet_rules.py br-server/app/services/wallet_service.py br-server/tests/test_wallet_rules.py
git commit -m "refactor: extract wallet display rules"
```

---

## 任务 4：提取支付金额与交易状态规则

**文件：**
- 新增：`br-server/app/domain/payment_rules.py`
- 新增：`br-server/tests/test_payment_rules.py`
- 修改：`br-server/app/services/booking_payment_service.py`

- [ ] **步骤 1：写失败测试**

创建 `br-server/tests/test_payment_rules.py`：

```python
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
```

- [ ] **步骤 2：确认测试失败**

运行：

```powershell
python -m pytest tests/test_payment_rules.py -q
```

期望：失败，错误为无法导入 `app.domain.payment_rules`。

- [ ] **步骤 3：写最小实现**

创建 `br-server/app/domain/payment_rules.py`：

```python
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
```

- [ ] **步骤 4：确认新测试通过**

运行：

```powershell
python -m pytest tests/test_payment_rules.py -q
```

期望：全部通过。

- [ ] **步骤 5：接入 `booking_payment_service.py`**

在 `br-server/app/services/booking_payment_service.py` 增加导入：

```python
from app.domain.payment_rules import (
    PAYMENT_QUERY_DELAYS,
    failed_trade_states,
    is_failed_trade_state,
    is_pending_trade_state,
    money_to_cents,
    pending_trade_states,
)
```

删除或替换本文件中的 `PAYMENT_QUERY_DELAYS`、`PENDING_TRADE_STATES`、`FAILED_TRADE_STATES` 常量定义：

```python
PENDING_TRADE_STATES = pending_trade_states()
FAILED_TRADE_STATES = failed_trade_states()
```

替换 `_decimal_to_cents` 方法实现：

```python
    def _decimal_to_cents(self, value: Decimal) -> int:
        return money_to_cents(value)
```

把直接判断交易状态集合的代码替换为谓词函数：

```python
if is_pending_trade_state(trade_state):
    ...

if is_failed_trade_state(trade_state):
    ...
```

- [ ] **步骤 6：运行受影响测试**

运行：

```powershell
python -m pytest tests/test_payment_rules.py tests/test_booking_payment_service.py tests/test_api_booking.py -q
```

期望：全部通过。

- [ ] **步骤 7：提交**

```powershell
git add br-server/app/domain/payment_rules.py br-server/app/services/booking_payment_service.py br-server/tests/test_payment_rules.py
git commit -m "refactor: extract booking payment rules"
```

---

## 任务 5：提取核销 token 纯规则

**文件：**
- 新增：`br-server/app/domain/verification_rules.py`
- 新增：`br-server/tests/test_verification_rules.py`
- 修改：`br-server/app/services/booking_verification_service.py`

- [ ] **步骤 1：写失败测试**

创建 `br-server/tests/test_verification_rules.py`：

```python
from datetime import UTC, datetime, timedelta

import pytest

from app.domain.verification_rules import (
    TOKEN_TTL_SECONDS,
    CompactVerificationPayload,
    ExpiredVerificationToken,
    InvalidVerificationToken,
    create_compact_verification_token,
    decode_compact_verification_token,
)


def test_create_and_decode_compact_verification_token_round_trips_booking_id():
    now = datetime(2026, 5, 30, 10, 0, tzinfo=UTC)
    token, expires_at = create_compact_verification_token(
        booking_id=123,
        secret="secret",
        now=now,
        nonce="abc",
    )

    payload = decode_compact_verification_token(
        token=token,
        secret="secret",
        now=now,
    )

    assert expires_at == now + timedelta(seconds=TOKEN_TTL_SECONDS)
    assert payload == CompactVerificationPayload(
        booking_id=123,
        issued_at=now,
        nonce="abc",
    )


def test_decode_compact_verification_token_rejects_bad_signature():
    now = datetime(2026, 5, 30, 10, 0, tzinfo=UTC)
    token, _ = create_compact_verification_token(
        booking_id=123,
        secret="secret",
        now=now,
        nonce="abc",
    )

    with pytest.raises(InvalidVerificationToken):
        decode_compact_verification_token(token=token, secret="other", now=now)


def test_decode_compact_verification_token_rejects_expired_token():
    now = datetime(2026, 5, 30, 10, 0, tzinfo=UTC)
    token, _ = create_compact_verification_token(
        booking_id=123,
        secret="secret",
        now=now,
        nonce="abc",
    )

    with pytest.raises(ExpiredVerificationToken):
        decode_compact_verification_token(
            token=token,
            secret="secret",
            now=now + timedelta(seconds=TOKEN_TTL_SECONDS + 1),
        )
```

- [ ] **步骤 2：确认测试失败**

运行：

```powershell
python -m pytest tests/test_verification_rules.py -q
```

期望：失败，错误为无法导入 `app.domain.verification_rules`。

- [ ] **步骤 3：写最小实现**

创建 `br-server/app/domain/verification_rules.py`：

```python
from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


TOKEN_TTL_SECONDS = 5 * 60
COMPACT_TOKEN_VERSION = "v1"


class InvalidVerificationToken(ValueError):
    pass


class ExpiredVerificationToken(ValueError):
    pass


@dataclass(frozen=True)
class CompactVerificationPayload:
    booking_id: int
    issued_at: datetime
    nonce: str


def create_compact_verification_token(
    *,
    booking_id: int,
    secret: str,
    now: datetime,
    nonce: str,
) -> tuple[str, datetime]:
    issued_at = ensure_utc(now)
    expires_at = issued_at + timedelta(seconds=TOKEN_TTL_SECONDS)
    signing_input = (
        f"{COMPACT_TOKEN_VERSION}.{booking_id}.{int(expires_at.timestamp())}.{nonce}"
    )
    signature = sign_compact_token(signing_input=signing_input, secret=secret)
    return f"{signing_input}.{signature}", expires_at


def decode_compact_verification_token(
    *,
    token: str,
    secret: str,
    now: datetime,
) -> CompactVerificationPayload:
    parts = token.split(".")
    if len(parts) != 5 or parts[0] != COMPACT_TOKEN_VERSION:
        raise InvalidVerificationToken("无效的核销码")

    signing_input = ".".join(parts[:4])
    expected_signature = sign_compact_token(signing_input=signing_input, secret=secret)
    if not hmac.compare_digest(parts[4], expected_signature):
        raise InvalidVerificationToken("无效的核销码")

    try:
        booking_id = int(parts[1])
        expires_at = datetime.fromtimestamp(int(parts[2]), tz=UTC)
        nonce = parts[3]
    except (TypeError, ValueError, OSError) as exc:
        raise InvalidVerificationToken("无效的核销码") from exc

    if not nonce:
        raise InvalidVerificationToken("无效的核销码")

    current_time = ensure_utc(now)
    if expires_at <= current_time:
        raise ExpiredVerificationToken("核销码已过期")

    return CompactVerificationPayload(
        booking_id=booking_id,
        issued_at=expires_at - timedelta(seconds=TOKEN_TTL_SECONDS),
        nonce=nonce,
    )


def sign_compact_token(*, signing_input: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64url_encode(digest[:16])


def base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
```

- [ ] **步骤 4：确认新测试通过**

运行：

```powershell
python -m pytest tests/test_verification_rules.py -q
```

期望：全部通过。

- [ ] **步骤 5：接入 `booking_verification_service.py`**

在 `br-server/app/services/booking_verification_service.py` 增加导入：

```python
from app.domain.verification_rules import (
    ExpiredVerificationToken,
    InvalidVerificationToken,
    create_compact_verification_token,
    decode_compact_verification_token,
)
```

替换 `_create_verification_token` 实现：

```python
def _create_verification_token(booking_id: int, user_id: str, now: datetime) -> tuple[str, datetime]:
    return create_compact_verification_token(
        booking_id=booking_id,
        secret=_get_signing_secret(),
        now=now,
        nonce=secrets.token_urlsafe(3),
    )
```

替换 `_decode_compact_verification_token` 中签名和过期判断主体。保留返回类型 `VerificationTokenPayload`：

```python
def _decode_compact_verification_token(token: str, now: datetime) -> VerificationTokenPayload:
    try:
        payload = decode_compact_verification_token(
            token=token,
            secret=_get_signing_secret(),
            now=now,
        )
    except ExpiredVerificationToken as exc:
        raise ExpiredVerificationTokenError("核销码已过期") from exc
    except InvalidVerificationToken as exc:
        raise InvalidVerificationTokenError("无效的核销码") from exc

    return VerificationTokenPayload(
        booking_id=payload.booking_id,
        user_id="",
        iat=payload.issued_at,
        nonce=payload.nonce,
    )
```

- [ ] **步骤 6：运行受影响测试**

运行：

```powershell
python -m pytest tests/test_verification_rules.py tests/test_booking_verification_service.py tests/test_api_booking_verification.py -q
```

期望：全部通过。

- [ ] **步骤 7：提交**

```powershell
git add br-server/app/domain/verification_rules.py br-server/app/services/booking_verification_service.py br-server/tests/test_verification_rules.py
git commit -m "refactor: extract verification token rules"
```

---

## 任务 6：提取预约仓储读写边界

**文件：**
- 新增：`br-server/app/repositories/__init__.py`
- 新增：`br-server/app/repositories/booking_repository.py`
- 新增：`br-server/tests/test_booking_repository.py`
- 修改：`br-server/app/services/booking_service.py`

- [ ] **步骤 1：写失败测试**

创建 `br-server/tests/test_booking_repository.py`：

```python
from datetime import date, time

import pytest

from app.models.booking import Booking
from app.repositories.booking_repository import BookingRepository


@pytest.mark.asyncio
async def test_has_time_conflict_returns_true_for_overlapping_confirmed_booking(db_session):
    existing = Booking(
        user_id="00000000-0000-0000-0000-000000000001",
        seat_id=1,
        room_id=1,
        date=date(2026, 5, 30),
        start_time=time(9, 0),
        end_time=time(11, 0),
        status="confirmed",
        payment_status="paid",
        original_price=10,
        discount_amount=0,
        total_price=10,
    )
    db_session.add(existing)
    await db_session.flush()

    repository = BookingRepository(db_session)

    result = await repository.has_time_conflict(
        seat_id=1,
        booking_date=date(2026, 5, 30),
        start_time=time(10, 0),
        end_time=time(12, 0),
    )

    assert result is True
```

- [ ] **步骤 2：确认测试失败**

运行：

```powershell
python -m pytest tests/test_booking_repository.py -q
```

期望：失败，错误为无法导入 `app.repositories.booking_repository`。

- [ ] **步骤 3：写最小仓储实现**

创建 `br-server/app/repositories/__init__.py`：

```python
"""数据库仓储适配层。"""
```

创建 `br-server/app/repositories/booking_repository.py`：

```python
from __future__ import annotations

from datetime import date, time

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking


class BookingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def has_time_conflict(
        self,
        *,
        seat_id: int,
        booking_date: date,
        start_time: time,
        end_time: time,
    ) -> bool:
        stmt = select(Booking.id).where(
            Booking.seat_id == seat_id,
            Booking.date == booking_date,
            Booking.status.in_(["pending", "confirmed"]),
            and_(
                Booking.start_time < end_time,
                Booking.end_time > start_time,
            ),
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None
```

- [ ] **步骤 4：确认仓储测试通过**

运行：

```powershell
python -m pytest tests/test_booking_repository.py -q
```

期望：全部通过。

- [ ] **步骤 5：在 `booking_service.py` 使用仓储**

在 `br-server/app/services/booking_service.py` 增加导入：

```python
from app.repositories.booking_repository import BookingRepository
```

把 `create_booking` 中的预约冲突查询替换为：

```python
    booking_repository = BookingRepository(db)
    has_conflict = await booking_repository.has_time_conflict(
        seat_id=data.seat_id,
        booking_date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
    )
    if has_conflict:
        raise BookingConflictError("Seat is already booked for this time range")
```

- [ ] **步骤 6：运行受影响测试**

运行：

```powershell
python -m pytest tests/test_booking_repository.py tests/test_api_booking.py tests/test_admin_booking_service.py -q
```

期望：全部通过。

- [ ] **步骤 7：提交**

```powershell
git add br-server/app/repositories/__init__.py br-server/app/repositories/booking_repository.py br-server/app/services/booking_service.py br-server/tests/test_booking_repository.py
git commit -m "refactor: extract booking repository conflict query"
```

---

## 任务 7：提取钱包仓储流水写入边界

**文件：**
- 新增：`br-server/app/repositories/wallet_repository.py`
- 新增：`br-server/tests/test_wallet_repository.py`
- 修改：`br-server/app/services/wallet_service.py`

- [ ] **步骤 1：写失败测试**

创建 `br-server/tests/test_wallet_repository.py`：

```python
from decimal import Decimal

import pytest

from app.repositories.wallet_repository import WalletRepository


@pytest.mark.asyncio
async def test_create_transaction_flushes_wallet_transaction(db_session):
    repository = WalletRepository(db_session)

    transaction = await repository.create_transaction(
        user_id="00000000-0000-0000-0000-000000000001",
        transaction_type="refund",
        amount=Decimal("12.30"),
        status="completed",
        description="取消退款",
    )

    assert transaction.id is not None
    assert transaction.type == "refund"
    assert transaction.amount == Decimal("12.30")
```

- [ ] **步骤 2：确认测试失败**

运行：

```powershell
python -m pytest tests/test_wallet_repository.py -q
```

期望：失败，错误为无法导入 `app.repositories.wallet_repository`。

- [ ] **步骤 3：写最小仓储实现**

创建 `br-server/app/repositories/wallet_repository.py`：

```python
from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import WalletTransaction


class WalletRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_transaction(
        self,
        *,
        user_id: str,
        transaction_type: str,
        amount: Decimal,
        status: str,
        description: str,
        related_booking_id: int | None = None,
    ) -> WalletTransaction:
        transaction = WalletTransaction(
            user_id=user_id,
            type=transaction_type,
            amount=amount,
            status=status,
            description=description,
            related_booking_id=related_booking_id,
        )
        self._db.add(transaction)
        await self._db.flush()
        return transaction
```

- [ ] **步骤 4：确认仓储测试通过**

运行：

```powershell
python -m pytest tests/test_wallet_repository.py -q
```

期望：全部通过。

- [ ] **步骤 5：在 `wallet_service.py` 使用仓储**

在 `br-server/app/services/wallet_service.py` 增加导入：

```python
from app.repositories.wallet_repository import WalletRepository
```

在 `WalletService.__init__` 中初始化：

```python
        self._wallet_repository = WalletRepository(db)
```

把类内直接创建 `WalletTransaction(...)` 且紧跟 `self._db.add(...)`、`await self._db.flush()` 的代码块逐个替换为：

```python
transaction = await self._wallet_repository.create_transaction(
    user_id=str(user_id),
    transaction_type="refund",
    amount=refund_amount,
    status="completed",
    description="取消退款",
    related_booking_id=booking_id,
)
```

替换时保持原有 `type`、`amount`、`status`、`description`、`related_booking_id` 值不变。

- [ ] **步骤 6：运行受影响测试**

运行：

```powershell
python -m pytest tests/test_wallet_repository.py tests/test_wallet_service.py tests/test_api_wallet.py -q
```

期望：全部通过。

- [ ] **步骤 7：提交**

```powershell
git add br-server/app/repositories/wallet_repository.py br-server/app/services/wallet_service.py br-server/tests/test_wallet_repository.py
git commit -m "refactor: extract wallet transaction repository"
```

---

## 任务 8：引入预约应用用例门面

**文件：**
- 新增：`br-server/app/application/__init__.py`
- 新增：`br-server/app/application/booking_use_cases.py`
- 新增：`br-server/tests/test_booking_use_cases.py`
- 修改：`br-server/app/services/booking_service.py`

- [ ] **步骤 1：写失败测试**

创建 `br-server/tests/test_booking_use_cases.py`：

```python
from app.application.booking_use_cases import BookingUseCases


def test_booking_use_cases_exposes_existing_service_callables():
    use_cases = BookingUseCases()

    assert callable(use_cases.create_booking)
    assert callable(use_cases.cancel_booking)
    assert callable(use_cases.list_bookings)
```

- [ ] **步骤 2：确认测试失败**

运行：

```powershell
python -m pytest tests/test_booking_use_cases.py -q
```

期望：失败，错误为无法导入 `app.application.booking_use_cases`。

- [ ] **步骤 3：创建兼容用例门面**

创建 `br-server/app/application/__init__.py`：

```python
"""应用用例编排层。"""
```

创建 `br-server/app/application/booking_use_cases.py`：

```python
from __future__ import annotations

from app.services import booking_service


class BookingUseCases:
    create_booking = staticmethod(booking_service.create_booking)
    list_bookings = staticmethod(booking_service.list_bookings)
    get_booking = staticmethod(booking_service.get_booking)
    cancel_booking = staticmethod(booking_service.cancel_booking)
```

- [ ] **步骤 4：确认测试通过**

运行：

```powershell
python -m pytest tests/test_booking_use_cases.py -q
```

期望：全部通过。

- [ ] **步骤 5：提交**

```powershell
git add br-server/app/application/__init__.py br-server/app/application/booking_use_cases.py br-server/tests/test_booking_use_cases.py
git commit -m "refactor: add booking use case facade"
```

---

## 任务 9：阶段性全量验证

**文件：**
- 不创建文件
- 不修改业务代码

- [ ] **步骤 1：运行后端聚焦测试**

运行：

```powershell
python -m pytest tests/test_booking_rules.py tests/test_wallet_rules.py tests/test_payment_rules.py tests/test_verification_rules.py tests/test_booking_repository.py tests/test_wallet_repository.py tests/test_booking_use_cases.py -q
```

期望：全部通过。

- [ ] **步骤 2：运行核心回归测试**

运行：

```powershell
python -m pytest tests/test_api_booking.py tests/test_api_wallet.py tests/test_wallet_service.py tests/test_booking_payment_service.py tests/test_booking_verification_service.py -q
```

期望：全部通过。

- [ ] **步骤 3：运行后端全量测试**

运行：

```powershell
python -m pytest
```

期望：全部通过。

- [ ] **步骤 4：检查工作区**

运行：

```powershell
git status --short
```

期望：只有本阶段预期修改，且没有 `.pytest_cache`、`__pycache__`、`uploads` 等生成物被暂存。

---

## 自检

- 设计范围只覆盖 `br-server`，没有混入前端和管理端。
- 每个行为提取任务都有失败测试、最小实现、接入现有服务、回归测试和提交步骤。
- 第一阶段先提取纯规则，再提取仓储，再引入用例门面，避免一次性重写服务。
- 所有新增文档使用中文。

