## Why

当前订单确认页仅支持账户余额支付（`payment_method: 'wallet'` 硬编码），用户必须先充值再预约。根据 `prototype/order-confirm.html` 原型图，需要增加支付方式选择（账户余额 / 微信支付），并实现直接微信支付预约功能，降低用户使用门槛。现有 WeChat Pay 基础设施（JSAPI 下单、回调处理）已用于钱包充值，可复用于订单支付。

## What Changes

- 订单确认页整体 UI 对齐 `prototype/order-confirm.html` 原型图，包括 5 个区域改造
- 门店信息：显示楼层（替代当前地址显示）
- 卡券区：改为原型简洁行样式（一行显示"优惠券 + 折扣金额 + 箭头"，点击弹出选择弹窗）
- 支付方式：新增 radio 选择卡片（账户余额 / 微信支付），匹配原型设计
- 成功弹窗：简化为原型 4 行摘要样式（门店、座位、时间、支付金额）
- 视觉风格：对齐圆角、间距、图标尺寸等细节
- 后端 booking 创建 API 支持两种支付方式：`balance`（余额直接扣款）和 `wechat`（微信 JSAPI 下单）
- 新增订单微信支付回调处理，支付成功后确认预约
- booking 模型新增 `payment_method`、`payment_status`、`payment_provider` 等字段
- 支持余额不足时自动引导选择微信支付

## Capabilities

### New Capabilities
- `booking-payment`: 订单支付能力（支付方式选择、微信直接支付、支付回调确认预约）

### Modified Capabilities
- `study-room-booking-api`: Create booking API 增加 `payment_method` 参数，支持 `balance` 和 `wechat` 两种支付方式，booking 响应增加支付相关字段
- `study-room-booking-ui`: 订单确认页增加支付方式选择 UI，匹配原型图设计，增加微信支付流程处理
- `wechat-payment-api`: 扩展微信支付能力，支持订单直接支付（不再仅限于钱包充值）

## Impact

- **br-app** (前端小程序): `pages/booking/confirm.vue` 订单确认页 UI 重构，新增支付方式选择组件、微信支付调用逻辑
- **br-server** (后端): `api/routes/booking.py` 创建预约 API 修改，`services/` 新增订单支付服务，`models/booking.py` 增加支付字段，新增支付回调 endpoint，alembic 数据库迁移
- **数据库**: `bookings` 表新增 `payment_method`、`payment_status`、`payment_provider`、`prepay_id`、`transaction_id` 字段
- **回滚方案**: 新增字段均为可空字段且有默认值，回滚时设置 `payment_method='balance'`、`payment_status='paid'` 即可兼容旧逻辑；前端保留余额支付为默认选项，关闭 `WECHAT_PAY_ENABLED` 环境变量即可禁用微信支付
