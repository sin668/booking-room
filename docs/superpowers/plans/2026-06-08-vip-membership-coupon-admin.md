# VIP 会员开通 + 卡券管理后台 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 VIP 会员开通机制（充值100+自动升级、首次赠券）和管理后台卡券 CRUD 管理页面。

**Architecture:** 后端在充值确认回调中嵌入 VIP 升级和赠券逻辑（方案 A），VIP 校验通过 `membership_level` 枚举字段实现。管理后台卡券 API 遵循现有 admin 路由模式（RBAC 权限 + FastAPI + SQLAlchemy）。前端 br-admin 新增卡券列表页和编辑弹窗，br-app 新增 VIP 权益页和充值联动。

**Tech Stack:** Python 3.12 + FastAPI + SQLAlchemy + Alembic (后端), Vue3 + Naive UI + TypeScript (br-admin), uni-app Vue3 + TailwindCSS (br-app)

---

## 文件结构映射

### 后端新建文件
| 文件 | 职责 |
|------|------|
| `br-server/alembic/versions/xxxx_add_membership_level.py` | User 表新增 membership_level 字段迁移 |
| `br-server/app/services/admin_coupon_service.py` | 管理后台卡券 CRUD 服务 |
| `br-server/app/schemas/coupon_admin.py` | 管理后台卡券 Pydantic schema |
| `br-server/app/api/routes/admin_coupon.py` | 管理后台卡券 API 路由 |
| `br-server/tests/services/test_admin_coupon_service.py` | 管理后台卡券服务单元测试 |
| `br-server/tests/services/test_vip_membership.py` | VIP 升级逻辑单元测试 |
| `br-server/tests/api/test_admin_coupon.py` | 管理后台卡券 API 集成测试 |

### 后端修改文件
| 文件 | 变更 |
|------|------|
| `br-server/app/models/user.py:97-101` | 新增 `membership_level` 字段 |
| `br-server/app/schemas/wallet.py:26-36` | RechargeResponse 新增 `membership_upgraded` 和 `vip_coupon_id` |
| `br-server/app/services/wallet_service.py:344-387` | confirm_payment 中嵌入 VIP 升级和赠券逻辑 |
| `br-server/app/services/coupon_service.py` | 抽取 `_check_scope` 统一方法，增加 `vip_only` 校验 |
| `br-server/app/api/routes/coupon.py` | 用户卡券查询增加 `membership_level` VIP 过滤 |
| 路由注册文件 | 注册 admin_coupon 路由 |

### 管理后台 br-admin 新建文件
| 文件 | 职责 |
|------|------|
| `br-admin/src/api/coupon/index.ts` | 卡券管理 API 和 TypeScript 类型 |
| `br-admin/src/views/coupon/list/index.vue` | 卡券列表页 |
| `br-admin/src/views/coupon/list/CouponEditModal.vue` | 卡券新建/编辑弹窗 |
| `br-admin/src/views/coupon/list/columns.ts` | 表格列定义和格式化 |
| `br-admin/src/router/modules/coupon.ts` | 卡券管理路由模块 |

### 管理后台 br-admin 修改文件
| 文件 | 变更 |
|------|------|
| `br-admin/src/views/activity/list/ActivityCouponConfig.vue` | 卡券 ID 输入替换为 NSelect 远程搜索 |

### 前端 br-app 新建文件
| 文件 | 职责 |
|------|------|
| `br-app/src/pages/membership/index.vue` | VIP 权益介绍页 |

### 前端 br-app 修改文件
| 文件 | 变更 |
|------|------|
| `br-app/src/pages/profile/index.vue` | 会员卡片 VIP 状态联动 |
| `br-app/src/pages/recharge/index.vue` | VIP 来源参数预填充和升级提示 |
| `br-app/src/pages/activity/detail.vue` | 无关联卡券时隐藏卡券区域 |
| `br-app/src/api/user.js` | 新增获取用户会员等级接口调用 |

---

### Task 1: 数据库迁移 — 新增 membership_level

**Files:**
- Create: `br-server/alembic/versions/<auto>_add_membership_level.py`
- Modify: `br-server/app/models/user.py:97` (balance 字段之后)

- [ ] **Step 1: 修改 User 模型，新增 membership_level 字段**

在 `br-server/app/models/user.py` 的 `balance` 字段（第 97-101 行）之后、`created_at` 之前，添加：

```python
    membership_level: Mapped[str] = mapped_column(
        String(20),
        default="none",
        nullable=False,
    )
```

在 `__table_args__` 的 CheckConstraint 列表中新增：

```python
CheckConstraint("membership_level IN ('none', 'vip', 'svip')", name="ck_users_membership_level"),
```

- [ ] **Step 2: 生成 Alembic 迁移**

Run: `cd br-server && conda activate booking-room && alembic revision --autogenerate -m "add_membership_level"`
预期：生成迁移文件，包含 `ADD COLUMN membership_level VARCHAR(20) NOT NULL DEFAULT 'none'` 和 CHECK 约束。

- [ ] **Step 3: 执行迁移**

Run: `cd br-server && alembic upgrade head`
预期：迁移成功，`users` 表新增 `membership_level` 列。

- [ ] **Step 4: 验证迁移**

Run: `cd br-server && python -c "from app.core.database import engine; import asyncio; asyncio.run(engine.connect().execute('SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name=\'users\' AND column_name=\'membership_level\''))"`
预期：返回 membership_level 列信息，默认值为 'none'。

- [ ] **Step 5: 提交**

```bash
git add br-server/app/models/user.py br-server/alembic/versions/*add_membership_level*
git commit -m "feat: add membership_level enum field to User model"
```

---

### Task 2: VIP 升级逻辑 — 单元测试

**Files:**
- Create: `br-server/tests/services/test_vip_membership.py`
- Modify: `br-server/app/schemas/wallet.py:26-36`

- [ ] **Step 1: 增强 RechargeResponse schema**

在 `br-server/app/schemas/wallet.py` 的 `RechargeResponse` 类中（第 26-36 行），在 `payment_params` 之后添加：

```python
    membership_upgraded: bool = False
    vip_coupon_id: int | None = None
```

- [ ] **Step 2: 编写 VIP 升级单元测试**

创建 `br-server/tests/services/test_vip_membership.py`：

```python
"""VIP 会员升级逻辑单元测试"""
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.wallet_service import WalletService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.WALLET_SIMULATED_CONFIRM_ENABLED = True
    return config


@pytest.fixture
def service(mock_db, mock_config):
    return WalletService(mock_db, mock_config)


@pytest.fixture
def none_user():
    """membership_level=none 的普通用户"""
    user = MagicMock()
    user.membership_level = "none"
    user.balance = Decimal("0")
    user.id = "user-uuid-001"
    user.nickname = "测试用户"
    return user


@pytest.fixture
def vip_user():
    """membership_level=vip 的 VIP 用户"""
    user = MagicMock()
    user.membership_level = "vip"
    user.balance = Decimal("100")
    user.id = "user-uuid-002"
    user.nickname = "VIP用户"
    return user


@pytest.fixture
def pending_transaction():
    txn = MagicMock()
    txn.amount = Decimal("100")
    txn.bonus_amount = Decimal("0")
    txn.status = "pending"
    txn.user_id = "user-uuid-001"
    txn.order_id = "order-001"
    return txn


class TestVIPUpgradeTrigger:
    """VIP 升级触发条件测试"""

    @pytest.mark.asyncio
    async def test_recharge_100_triggers_vip_upgrade(self, service, mock_db, none_user, pending_transaction):
        """充值100元应触发VIP升级"""
        # Arrange: mock DB queries
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = pending_transaction
        mock_db.execute = AsyncMock(return_value=result_mock)
        mock_db.flush = AsyncMock()

        # Mock user query to return none_user on first call, then vip_user
        user_result = MagicMock()
        user_result.scalar_one.return_value = none_user
        mock_db.execute = AsyncMock(return_value=user_result)

        # Act
        response = await service.confirm_payment(
            order_id=pending_transaction.order_id,
            user_id=none_user.id
        )

        # Assert
        assert response.membership_upgraded is True

    @pytest.mark.asyncio
    async def test_recharge_50_no_upgrade(self, service, mock_db, none_user):
        """充值50元不应触发VIP升级"""
        txn = MagicMock()
        txn.amount = Decimal("50")
        txn.bonus_amount = Decimal("0")
        txn.status = "pending"
        txn.user_id = none_user.id
        txn.order_id = "order-002"

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = txn
        user_result = MagicMock()
        user_result.scalar_one.return_value = none_user

        mock_db.execute = AsyncMock(side_effect=[result_mock, user_result])
        mock_db.flush = AsyncMock()

        response = await service.confirm_payment(
            order_id=txn.order_id,
            user_id=none_user.id
        )

        assert response.membership_upgraded is False

    @pytest.mark.asyncio
    async def test_already_vip_no_upgrade(self, service, mock_db, vip_user):
        """已是VIP用户充值不应重复升级"""
        txn = MagicMock()
        txn.amount = Decimal("100")
        txn.bonus_amount = Decimal("0")
        txn.status = "pending"
        txn.user_id = vip_user.id
        txn.order_id = "order-003"

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = txn
        user_result = MagicMock()
        user_result.scalar_one.return_value = vip_user

        mock_db.execute = AsyncMock(side_effect=[result_mock, user_result])
        mock_db.flush = AsyncMock()

        response = await service.confirm_payment(
            order_id=txn.order_id,
            user_id=vip_user.id
        )

        assert response.membership_upgraded is False
        assert vip_user.membership_level == "vip"  # 不变
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd br-server && pytest tests/services/test_vip_membership.py -v`
预期：FAIL（VIP 升级逻辑尚未实现）

- [ ] **Step 4: 提交测试**

```bash
git add br-server/app/schemas/wallet.py br-server/tests/services/test_vip_membership.py
git commit -m "test: add VIP membership upgrade unit tests"
```

---

### Task 3: VIP 升级逻辑 — 实现

**Files:**
- Modify: `br-server/app/services/wallet_service.py:344-387`

- [ ] **Step 1: 在 confirm_payment 中实现 VIP 升级逻辑**

在 `br-server/app/services/wallet_service.py` 的 `confirm_payment` 方法中（第 376 行 `transaction.status = "completed"` 之后），添加 VIP 升级检测和赠券创建逻辑：

```python
        # VIP 升级检测
        membership_upgraded = False
        vip_coupon_id = None
        if (
            transaction.amount >= Decimal("100")
            and user.membership_level == "none"
        ):
            user.membership_level = "vip"
            membership_upgraded = True

            # 创建 VIP 欢迎券
            now = datetime.now()
            welcome_coupon = Coupon(
                name=f"VIP专属8折券-{user.nickname}",
                type="percentage_off",
                discount_percent=80,
                min_order_amount=Decimal("0"),
                scope="vip_only",
                valid_from=now,
                expires_at=now.replace(month=now.month + 1 if now.month < 12 else 1, day=now.day),
                is_active=True,
            )
            self._db.add(welcome_coupon)
            await self._db.flush()  # 获取 coupon.id

            user_coupon = UserCoupon(
                user_id=str(user.id),
                coupon_id=welcome_coupon.id,
                status="available",
                source_type="vip_welcome",
            )
            self._db.add(user_coupon)
            await self._db.flush()  # 获取 user_coupon.id
            vip_coupon_id = user_coupon.id
```

修改返回值（第 381-387 行）：

```python
        return RechargeResponse(
            order_id=uuid.UUID(transaction.order_id),
            amount=transaction.amount,
            bonus_amount=transaction.bonus_amount,
            status=transaction.status,
            balance_after=transaction.balance_after,
            membership_upgraded=membership_upgraded,
            vip_coupon_id=vip_coupon_id,
        )
```

确保文件顶部已导入 `Coupon` 和 `UserCoupon`：

```python
from app.models.coupon import Coupon, UserCoupon
```

- [ ] **Step 2: 运行测试确认通过**

Run: `cd br-server && pytest tests/services/test_vip_membership.py -v`
预期：PASS

- [ ] **Step 3: 提交**

```bash
git add br-server/app/services/wallet_service.py
git commit -m "feat: implement VIP auto-upgrade on recharge with welcome coupon"
```

---

### Task 4: VIP 适用范围过滤逻辑

**Files:**
- Modify: `br-server/app/services/coupon_service.py`
- Modify: `br-server/app/api/routes/coupon.py`

- [ ] **Step 1: 在 coupon_service.py 中抽取 `_check_scope` 统一方法**

在 `br-server/app/services/coupon_service.py` 中添加统一的 scope 校验函数：

```python
def _check_scope(user: Any, coupon: Coupon, has_prior_bookings: bool = False) -> bool:
    """统一校验卡券适用范围"""
    if coupon.scope == "all":
        return True
    if coupon.scope == "first_booking":
        return not has_prior_bookings
    if coupon.scope == "vip_only":
        return getattr(user, "membership_level", "none") in ("vip", "svip")
    # seat_zone scope
    return True  # 座位区域校验在调用方处理
```

- [ ] **Step 2: 修改用户卡券查询路由增加 VIP 过滤**

在 `br-server/app/api/routes/coupon.py` 的卡券列表查询中，过滤 `scope=vip_only` 且用户非 VIP 的卡券。找到获取用户卡券的查询逻辑，在过滤条件中添加：

```python
# 排除非VIP用户的VIP专享券
if user.membership_level not in ("vip", "svip"):
    conditions.append(
        ~exists().where(
            Coupon.id == UserCoupon.coupon_id,
            Coupon.scope == "vip_only"
        )
    )
```

- [ ] **Step 3: 修改预约可用卡券查询增加 VIP 过滤**

在卡券可用预约查询逻辑中，添加同样的 VIP 过滤条件。

- [ ] **Step 4: 编写 VIP 范围过滤测试**

在 `br-server/tests/services/test_vip_membership.py` 中添加：

```python
from app.services.coupon_service import _check_scope
from app.models.coupon import Coupon


class TestVIPScopeFilter:
    def test_vip_only_coupon_for_vip_user(self):
        coupon = MagicMock(spec=Coupon)
        coupon.scope = "vip_only"
        user = MagicMock()
        user.membership_level = "vip"
        assert _check_scope(user, coupon) is True

    def test_vip_only_coupon_for_none_user(self):
        coupon = MagicMock(spec=Coupon)
        coupon.scope = "vip_only"
        user = MagicMock()
        user.membership_level = "none"
        assert _check_scope(user, coupon) is False

    def test_all_scope_for_any_user(self):
        coupon = MagicMock(spec=Coupon)
        coupon.scope = "all"
        user = MagicMock()
        user.membership_level = "none"
        assert _check_scope(user, coupon) is True
```

- [ ] **Step 5: 运行测试**

Run: `cd br-server && pytest tests/services/test_vip_membership.py -v`
预期：PASS

- [ ] **Step 6: 提交**

```bash
git add br-server/app/services/coupon_service.py br-server/app/api/routes/coupon.py br-server/tests/services/test_vip_membership.py
git commit -m "feat: add VIP scope filtering to coupon queries"
```

---

### Task 5: 管理后台卡券服务层

**Files:**
- Create: `br-server/app/services/admin_coupon_service.py`
- Create: `br-server/app/schemas/coupon_admin.py`
- Create: `br-server/tests/services/test_admin_coupon_service.py`

- [ ] **Step 1: 创建 AdminCoupon Pydantic schemas**

创建 `br-server/app/schemas/coupon_admin.py`：

```python
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class AdminCouponCreate(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=255)
    type: str = Field(pattern="^(threshold_amount_off|amount_off|percentage_off)$")
    discount_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    discount_percent: int | None = Field(default=None, ge=1, le=99)
    min_order_amount: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    scope: str = Field(default="all")
    seat_zone: str | None = Field(default=None, max_length=20)
    valid_from: datetime
    expires_at: datetime
    is_active: bool = True


class AdminCouponUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    type: str | None = Field(default=None, pattern="^(threshold_amount_off|amount_off|percentage_off)$")
    discount_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    discount_percent: int | None = Field(default=None, ge=1, le=99)
    min_order_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    scope: str | None = None
    seat_zone: str | None = Field(default=None, max_length=20)
    valid_from: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None


class AdminCouponResponse(BaseModel):
    id: int
    name: str
    description: str | None
    type: str
    discount_amount: Decimal | None
    discount_percent: int | None
    min_order_amount: Decimal
    scope: str
    seat_zone: str | None
    valid_from: datetime
    expires_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminCouponListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminCouponResponse]


class AdminCouponStatusUpdate(BaseModel):
    is_active: bool
```

- [ ] **Step 2: 创建 AdminCouponService**

创建 `br-server/app/services/admin_coupon_service.py`，参考现有 `ActivityService` 模式，实现：
- `list_coupons(db, page, page_size, keyword, type, scope, is_active)` — 分页列表
- `get_coupon(db, coupon_id)` — 详情
- `create_coupon(db, data)` — 创建（含 type 与优惠规则校验）
- `update_coupon(db, coupon_id, data)` — 更新（已关联 ActivityCoupon 时禁止修改 type）
- `toggle_status(db, coupon_id, is_active)` — 启停（已过期禁止启用）
- `delete_coupon(db, coupon_id)` — 删除（已关联时禁止）

校验规则：
- `threshold_amount_off`: discount_amount 必填，min_order_amount > 0
- `amount_off`: discount_amount 必填
- `percentage_off`: discount_percent 必填，1-99

- [ ] **Step 3: 编写 AdminCouponService 单元测试**

创建 `br-server/tests/services/test_admin_coupon_service.py`，覆盖：
- 创建满减券成功/失败（缺少 discount_amount）
- 创建折扣券成功/失败（discount_percent 超范围）
- 更新已关联卡券的类型被拒
- 停用已过期卡券被拒
- 删除已关联卡券被拒

- [ ] **Step 4: 运行测试**

Run: `cd br-server && pytest tests/services/test_admin_coupon_service.py -v`
预期：PASS

- [ ] **Step 5: 提交**

```bash
git add br-server/app/services/admin_coupon_service.py br-server/app/schemas/coupon_admin.py br-server/tests/services/test_admin_coupon_service.py
git commit -m "feat: add admin coupon CRUD service and schemas"
```

---

### Task 6: 管理后台卡券 API 路由

**Files:**
- Create: `br-server/app/api/routes/admin_coupon.py`
- Modify: 路由注册文件

- [ ] **Step 1: 创建 admin_coupon 路由**

创建 `br-server/app/api/routes/admin_coupon.py`，参考 `admin_activity.py` 模式：

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin_permission
from app.core.database import get_db
from app.schemas.coupon_admin import (
    AdminCouponCreate,
    AdminCouponListResponse,
    AdminCouponResponse,
    AdminCouponStatusUpdate,
    AdminCouponUpdate,
)
from app.services import admin_coupon_service

router = APIRouter(prefix="/api/v1/admin/coupons", tags=["admin-coupons"])


@router.get("", response_model=AdminCouponListResponse, dependencies=[Depends(require_admin_permission("coupon:view"))])
async def list_coupons(
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    type: str | None = None,
    scope: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> AdminCouponListResponse:
    return await admin_coupon_service.list_coupons(
        db, page=page, page_size=page_size, keyword=keyword, type=type, scope=scope, is_active=is_active
    )


@router.post("", response_model=AdminCouponResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin_permission("coupon:create"))])
async def create_coupon(data: AdminCouponCreate, db: AsyncSession = Depends(get_db)) -> AdminCouponResponse:
    return await admin_coupon_service.create_coupon(db, data.model_dump())


@router.get("/{coupon_id}", response_model=AdminCouponResponse, dependencies=[Depends(require_admin_permission("coupon:view"))])
async def get_coupon(coupon_id: int, db: AsyncSession = Depends(get_db)) -> AdminCouponResponse:
    coupon = await admin_coupon_service.get_coupon(db, coupon_id)
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="卡券不存在")
    return coupon


@router.put("/{coupon_id}", response_model=AdminCouponResponse, dependencies=[Depends(require_admin_permission("coupon:update"))])
async def update_coupon(coupon_id: int, data: AdminCouponUpdate, db: AsyncSession = Depends(get_db)) -> AdminCouponResponse:
    return await admin_coupon_service.update_coupon(db, coupon_id, data.model_dump(exclude_none=True))


@router.patch("/{coupon_id}/status", response_model=AdminCouponResponse, dependencies=[Depends(require_admin_permission("coupon:update"))])
async def toggle_coupon_status(coupon_id: int, data: AdminCouponStatusUpdate, db: AsyncSession = Depends(get_db)) -> AdminCouponResponse:
    return await admin_coupon_service.toggle_status(db, coupon_id, data.is_active)


@router.delete("/{coupon_id}", dependencies=[Depends(require_admin_permission("coupon:delete"))])
async def delete_coupon(coupon_id: int, db: AsyncSession = Depends(get_db)):
    await admin_coupon_service.delete_coupon(db, coupon_id)
    return {"detail": "删除成功"}
```

- [ ] **Step 2: 注册路由**

在路由注册入口（参考 main.py 或 app 初始化文件中 admin 路由的挂载方式）添加：

```python
from app.api.routes.admin_coupon import router as admin_coupon_router
app.include_router(admin_coupon_router)
```

- [ ] **Step 3: 编写 API 集成测试**

创建 `br-server/tests/api/test_admin_coupon.py`，测试 CRUD 流程。

- [ ] **Step 4: 运行测试**

Run: `cd br-server && pytest tests/api/test_admin_coupon.py -v`
预期：PASS

- [ ] **Step 5: 提交**

```bash
git add br-server/app/api/routes/admin_coupon.py br-server/tests/api/test_admin_coupon.py
git commit -m "feat: add admin coupon CRUD API routes with RBAC"
```

---

### Task 7: br-admin 卡券管理 API 层

**Files:**
- Create: `br-admin/src/api/coupon/index.ts`

- [ ] **Step 1: 创建卡券管理 API 模块**

```typescript
import { Alova } from '@/utils/http/alova/index';
import { ADMIN_NATIVE_META } from '@/api/contracts/admin';

export interface AdminCouponItem {
  id: number;
  name: string;
  description: string | null;
  type: string;
  discount_amount: string | number | null;
  discount_percent: number | null;
  min_order_amount: string | number;
  scope: string;
  seat_zone: string | null;
  valid_from: string;
  expires_at: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminCouponListResult {
  total: number;
  page: number;
  page_size: number;
  items: AdminCouponItem[];
}

export interface AdminCouponCreateParams {
  name: string;
  description?: string | null;
  type: string;
  discount_amount?: number | null;
  discount_percent?: number | null;
  min_order_amount?: number;
  scope?: string;
  seat_zone?: string | null;
  valid_from: string;
  expires_at: string;
  is_active?: boolean;
}

export interface AdminCouponUpdateParams extends Partial<AdminCouponCreateParams> {}

export interface AdminCouponListParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  type?: string;
  scope?: string;
  is_active?: boolean;
}

export function getCouponList(params?: AdminCouponListParams) {
  return Alova.Get<AdminCouponListResult>('/v1/admin/coupons', { params, meta: ADMIN_NATIVE_META });
}

export function getCouponById(id: number) {
  return Alova.Get<AdminCouponItem>(`/v1/admin/coupons/${id}`, { meta: ADMIN_NATIVE_META });
}

export function createCoupon(data: AdminCouponCreateParams) {
  return Alova.Post<AdminCouponItem>('/v1/admin/coupons', data, { meta: ADMIN_NATIVE_META });
}

export function updateCoupon(id: number, data: AdminCouponUpdateParams) {
  return Alova.Put<AdminCouponItem>(`/v1/admin/coupons/${id}`, data, { meta: ADMIN_NATIVE_META });
}

export function toggleCouponStatus(id: number, is_active: boolean) {
  return Alova.Patch<AdminCouponItem>(`/v1/admin/coupons/${id}/status`, { is_active }, { meta: ADMIN_NATIVE_META });
}

export function deleteCoupon(id: number) {
  return Alova.Delete(`/v1/admin/coupons/${id}`, { meta: ADMIN_NATIVE_META });
}
```

- [ ] **Step 2: 提交**

```bash
git add br-admin/src/api/coupon/index.ts
git commit -m "feat(admin): add coupon management API module"
```

---

### Task 8: br-admin 卡券列表页

**Files:**
- Create: `br-admin/src/views/coupon/list/index.vue`
- Create: `br-admin/src/views/coupon/list/columns.ts`
- Create: `br-admin/src/views/coupon/list/CouponEditModal.vue`
- Create: `br-admin/src/router/modules/coupon.ts`

- [ ] **Step 1: 创建表格列定义**

创建 `br-admin/src/views/coupon/list/columns.ts`，定义表格列：名称、类型（满减/立减/折扣 tag）、优惠规则（格式化显示）、适用范围（全场通用/首次预约/VIP专享/区域名）、有效期、状态、创建时间、操作。

类型格式化工具：
```typescript
const typeLabels: Record<string, string> = {
  threshold_amount_off: '满减券',
  amount_off: '立减券',
  percentage_off: '折扣券',
};

const scopeLabels: Record<string, string> = {
  all: '全场通用',
  first_booking: '首次预约',
  vip_only: 'VIP专享',
};
```

- [ ] **Step 2: 创建卡券列表页**

创建 `br-admin/src/views/coupon/list/index.vue`，参考现有 `activity/list/index.vue` 模式：
- 顶部搜索框 + 类型/状态筛选下拉
- NDataTable 表格展示卡券列表
- "新建卡券"按钮打开编辑弹窗
- 操作列：编辑、启停切换、删除（确认对话框）

- [ ] **Step 3: 创建卡券编辑弹窗**

创建 `br-admin/src/views/coupon/list/CouponEditModal.vue`：
- NModal + NForm 表单
- 类型选择联动显示优惠规则字段（满减→金额+门槛，立减→金额，折扣→折扣比例）
- 适用范围 NSelect（全场通用/首次预约/VIP专享/指定区域，选择指定区域时显示区域输入）
- NDatePicker 日期范围选择器（valid_from, expires_at）
- 表单校验：名称必填、类型必填、有效期必填、优惠规则与类型匹配

- [ ] **Step 4: 创建路由模块**

创建 `br-admin/src/router/modules/coupon.ts`：

```typescript
import type { RouteRecordRaw } from 'vue-router';
import { BasicLayout } from '@/router/base';

const routes: RouteRecordRaw[] = [
  {
    path: '/coupon',
    name: 'Coupon',
    component: BasicLayout,
    redirect: '/coupon/list',
    meta: { title: '卡券管理', sort: 30 },
    children: [
      {
        path: 'list',
        name: 'CouponList',
        component: () => import('@/views/coupon/list/index.vue'),
        meta: { title: '卡券列表' },
      },
    ],
  },
];

export default routes;
```

- [ ] **Step 5: 提交**

```bash
git add br-admin/src/views/coupon/ br-admin/src/router/modules/coupon.ts
git commit -m "feat(admin): add coupon management list page and edit modal"
```

---

### Task 9: br-admin 活动卡券选择器改造

**Files:**
- Modify: `br-admin/src/views/activity/list/ActivityCouponConfig.vue`

- [ ] **Step 1: 将卡券 ID 输入框替换为 NSelect 远程搜索**

修改 `ActivityCouponConfig.vue` 第 44-49 行，将 NInputNumber 替换为 NSelect：

```vue
<n-form-item-gi label="卡券模板">
  <n-select
    v-model:value="item.coupon.coupon_id"
    filterable
    remote
    :options="couponOptions"
    :loading="couponSearchLoading"
    placeholder="搜索卡券名称"
    clearable
    @search="handleCouponSearch"
    @update:value="handleCouponSelect(item.index, $event)"
    style="width: 100%"
  />
</n-form-item-gi>
```

- [ ] **Step 2: 添加远程搜索逻辑**

在 script 中添加：
- `couponOptions` ref（NSelect 选项列表）
- `couponSearchLoading` ref
- `handleCouponSearch(query: string)` — 300ms 防抖，调用 `getCouponList({ keyword: query, page_size: 20, is_active: true })`
- `handleCouponSelect(index: number, couponId: number)` — 调用 `getCouponById` 回显卡券信息到只读字段

- [ ] **Step 3: 添加重复关联校验**

在 `handleCouponSelect` 中检查当前活动的所有卡券配置，如果 `coupon_id` 已存在则提示"该卡券已关联此活动"。

- [ ] **Step 4: 提交**

```bash
git add br-admin/src/views/activity/list/ActivityCouponConfig.vue
git commit -m "feat(admin): replace coupon ID input with remote search selector"
```

---

### Task 10: br-app VIP 权益页和我的页面联动

**Files:**
- Create: `br-app/src/pages/membership/index.vue`
- Modify: `br-app/src/pages/profile/index.vue`
- Modify: `br-app/src/pages/recharge/index.vue`
- Modify: `br-app/src/api/user.js`

- [ ] **Step 1: 新增用户会员等级 API 调用**

在 `br-app/src/api/user.js` 中新增获取用户信息接口（如不存在），确保返回 `membership_level` 字段。

- [ ] **Step 2: 创建 VIP 权益介绍页**

创建 `br-app/src/pages/membership/index.vue`：
- 页面标题"超级会员"
- 权益列表：8折优惠、专属座位、优先预约
- 底部按钮"立即开通 - 充值100元起"
- 点击跳转 `/pages/recharge/index?amount=100&source=vip`
- VIP 用户访问时按钮显示"已是超级会员"（禁用）
- 注册到 `pages.json`

- [ ] **Step 3: 修改我的页面会员卡片**

修改 `br-app/src/pages/profile/index.vue` 第 130-138 行会员卡片：
- 从用户信息中读取 `membership_level`
- 非 VIP：保持现有"升级超级会员"和"立即开通"按钮，点击跳转 `/pages/membership/index`
- VIP：修改为"超级会员"标题，显示 VIP 标签，移除"立即开通"或改为"已是会员"禁用态

- [ ] **Step 4: 修改充值页 VIP 联动**

修改 `br-app/src/pages/recharge/index.vue`：
- 在 `onLoad` 中检测 URL 参数 `source=vip` 和 `amount`
- 当 `source=vip` 时，预填充充值金额为 `amount`（100 元）
- 充值成功回调中，检查 `res.membership_upgraded`
- 若为 true，弹出"恭喜成为超级会员"提示 + 赠券信息
- 用户确认后跳转回我的页面

- [ ] **Step 5: 提交**

```bash
git add br-app/src/pages/membership/ br-app/src/pages/profile/index.vue br-app/src/pages/recharge/index.vue br-app/src/api/user.js br-app/src/pages.json
git commit -m "feat(app): add VIP membership page and recharge upgrade flow"
```

---

### Task 11: br-app 活动详情卡券区域条件渲染

**Files:**
- Modify: `br-app/src/pages/activity/detail.vue`

- [ ] **Step 1: 添加 v-if 条件**

修改 `br-app/src/pages/activity/detail.vue` 第 36 行，将 `<view class="coupon-section">` 改为：

```vue
<view v-if="activityCoupons.length > 0" class="coupon-section">
```

- [ ] **Step 2: 提交**

```bash
git add br-app/src/pages/activity/detail.vue
git commit -m "fix(app): hide coupon section when activity has no coupons"
```

---

### Task 12: API 文档与代码审查

**Files:**
- Modify: `docs/api.md`

- [ ] **Step 1: 更新 API 文档**

在 `docs/api.md` 中补充：
- 管理后台卡券 CRUD 接口（GET/POST/PUT/PATCH/DELETE `/api/v1/admin/coupons`）
- VIP 会员升级相关字段说明（RechargeResponse 新增字段）

- [ ] **Step 2: 代码审查**

审查清单：
- [ ] 所有 admin API 端点都有 RBAC 权限校验
- [ ] VIP 升级逻辑在 DB 事务内执行
- [ ] `_check_scope` 覆盖所有 scope 类型
- [ ] Clean Architecture 分层：路由→服务→模型
- [ ] 前端卡券选择器防抖正常工作
- [ ] br-app 无关联卡券时 coupon-section 不渲染

- [ ] **Step 3: 最终提交**

```bash
git add docs/api.md
git commit -m "docs: update API documentation for coupon admin and VIP membership"
```
