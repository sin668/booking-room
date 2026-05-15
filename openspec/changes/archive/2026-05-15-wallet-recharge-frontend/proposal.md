## Why

用户目前无法在应用内进行钱包充值，Profile 页面已有钱包入口（`/pages/recharge/index`）和余额展示（¥256.00），但充值功能尚未实现。需要补齐充值页面，让用户能够选择金额、选择支付方式完成充值，形成完整的资金闭环。

## What Changes

- 新增钱包充值页面（`/pages/recharge/index`），包含余额展示、金额选择、支付方式、优惠码兑换
- 新增充值相关 API 封装（`/src/api/wallet.js`）
- 注册页面路由（`pages.json`）
- 新增后端钱包充值 API（创建充值订单）
- 优惠码兑换功能

## Capabilities

### New Capabilities

- `wallet-recharge-ui`: 钱包充值前端页面 — 余额卡片、金额选择网格、支付方式选择、优惠码输入、充值按钮
- `wallet-recharge-api`: 钱包充值后端 API — 创建充值订单、余额查询、优惠码兑换

### Modified Capabilities

（无已有 capability 需要修改）

## Impact

- **前端模块**：br-app（新增页面、API 封装、路由注册）
- **后端模块**：br-server（新增 wallet routes、service、model、schema）
- **数据库**：新增 wallet_transactions 表（充值记录）、wallet_balance 字段（users 表）
- **API 变更**：新增 `POST /api/wallet/recharge`、`GET /api/wallet/balance`、`POST /api/wallet/promo-code`
- **回滚方案**：移除新增的路由、页面文件和 API 端点即可回滚，数据库迁移可通过 `alembic downgrade` 回退
