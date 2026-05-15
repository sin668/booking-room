## Context

br-app（UniApp Vue3）Profile 页面已有钱包入口（`/pages/recharge/index`）和余额展示，seed data 中也有充值相关的 banner 指向该路径，但充值页面尚未实现。后端目前无钱包相关的 model、service 或 route。

原型图位于 `prototype/recharge.html`，采用与现有页面一致的设计语言（primary #4F6EF7、圆角卡片、底部固定按钮）。

## Goals / Non-Goals

**Goals:**
- 实现与原型图一致的钱包充值页面
- 实现后端充值订单创建、余额查询、优惠码兑换 API
- 前端页面接入真实 API，替换静态数据

**Non-Goals:**
- 不实现真实微信/支付宝支付回调（使用模拟支付完成流程）
- 不实现充值记录历史页面
- 不实现管理后台的钱包管理
- 不实现提现功能

## Decisions

### 1. 前端：复用现有页面模式

**选择**：按照现有 br-app 页面结构（Vue3 SFC + Composition API + SCSS），新建 `pages/recharge/index.vue`，API 封装到 `api/wallet.js`。

**理由**：与 coupon、study-record 等页面保持一致的代码组织方式，降低维护成本。

**备选**：抽取通用 PaymentMethod 组件 → 过度设计，当前只有充值页用到支付方式选择。

### 2. 后端：WalletService 独立于 AuthService

**选择**：新建 `WalletService` + `Wallet` model，不扩展现有 `AuthService`。

**理由**：职责分离。认证（JWT/token）与钱包（余额/充值/交易）是不同领域，拆分后各自演进互不影响。

### 3. 数据模型：users 表加 balance 字段 + wallet_transactions 交易表

**选择**：
- `users` 表新增 `balance` 字段（DECIMAL(10,2)，默认 0）
- 新建 `wallet_transactions` 表记录每笔交易（type/amount/balance_after/promo_code_id）

**理由**：余额冗余在 users 表避免每次聚合计算，wallet_transactions 保留完整审计链。

**备选**：只用 wallet_transactions 聚合余额 → 查询性能差，高并发下余额计算不准确。

### 4. 充值流程：先创建订单 → 模拟支付 → 服务端确认

**选择**：
```
前端选择金额+支付方式 → POST /api/wallet/recharge（创建充值订单）
→ 返回订单信息 → 前端调用"模拟支付"API → 服务端增加余额
→ 轮询/返回最新余额
```

**理由**：即使暂不接入真实支付，订单模型保留扩展性，后续接入微信支付只需替换支付步骤。

### 5. 优惠码：复用现有 coupon 体系

**选择**：优惠码兑换复用 `CouponCode` 模型，充值时关联 coupon_code_id。

**理由**：seed_data 中已有 "充值100送30" 的活动 banner，复用现有优惠体系保持一致性。

```
┌─────────┐    POST /recharge     ┌─────────────┐
│  前端    │ ──────────────────→   │  后端 API    │
│ recharge │                      │  FastAPI     │
│  page    │  ← order + pay_url   │             │
│          │                      │  WalletService│
│          │  POST /pay/confirm   │  .create_order│
│          │ ──────────────────→  │  .confirm_pay │
│          │  ← updated balance   │             │
│          │                      │  DB          │
│          │                      │  users.balance│
│          │                      │  wallet_txn   │
└─────────┘                      └─────────────┘
```

## Risks / Trade-offs

- **[余额并发安全]** → 使用 `UPDATE users SET balance = balance + :amount WHERE id = :id` 原子操作 + 数据库行锁，避免超卖
- **[模拟支付无真实交易]** → 订单状态字段预留 `pending/completed/failed`，后续接入真实支付只需扩展 confirm 逻辑
- **[优惠码重复使用]** → 兑换时校验 `used_at IS NULL` + 用户维度限制，数据库 UNIQUE 约束兜底
