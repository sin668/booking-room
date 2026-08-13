# 订单确认页 UI 对齐 + 微信支付 设计

## 概述

将订单确认页（`pages/booking/confirm.vue`）整体 UI 对齐 `prototype/order-confirm.html` 原型图，同时增加直接微信支付功能。所有改动合并到现有 `update-order-payment-wechat` openspec change 中。

## 原型对比分析

对比 `prototype/order-confirm.html` 与现有 `confirm.vue`，识别出 5 个差异区域：

| 区域 | 现有实现 | 原型设计 | 影响 |
|------|----------|----------|------|
| 门店信息 | 显示地址 | 显示楼层（如"3楼"） | 小 |
| 卡券区 | 内联展开 radio 列表 | 简洁行 + 弹窗选择 | 大 |
| 支付方式 | 仅余额卡片 | Radio 双选（余额/微信） | 大 |
| 成功弹窗 | 7 字段详情 | 4 行简洁摘要 | 小 |
| 视觉风格 | 项目 SCSS 变量 | 原型圆角/间距/图标颜色 | 中 |

## 设计决策

### D1: 门店信息改为楼层
门店卡片第二行从 `roomAddress` 改为 `floor`。地址已在详情页展示，确认页保持简洁。

### D2: 卡券区改为简洁行 + 弹窗
移除内联展开列表，改为原型一行样式（ticket 图标 + "优惠券" + 折扣金额 + 箭头）。点击弹出 bottom sheet 选择卡券。减少页面视觉复杂度，保留选择功能。

### D3: 支付方式 Radio 选择
替换"钱包余额"独立卡片为 radio 选择卡片（余额默认选中 + 微信支付）。余额不足时显示提示。

### D4: Booking 模型增加支付字段
`bookings` 表新增 `payment_method`、`payment_status`、`payment_provider`、`prepay_id`、`transaction_id`、`paid_at`。余额支付即时 paid，微信支付先 pending 后回调更新。

### D5: 微信支付两阶段流程
余额：即时扣款 → confirmed + paid。微信：占座 pending → JSAPI 下单 → 回调确认 → paid。15 分钟超时自动取消。

### D6: 复用 wechat_pay_client
新增 `booking_payment_service.py`，复用现有微信支付基础设施，订单号前缀 `BK-` 区分充值 `RC-`。

### D7: 成功弹窗简化
从 7 字段简化为 4 行（门店、座位、时间、支付金额），匹配原型。

### D8: 视觉风格对齐
卡片圆角 16rpx、图标颜色（门店 blue、座位 green、日期 amber、时钟 purple、卡券 red）、间距与原型一致。

## 风险

- **微信支付超时占座** → 15 分钟定时任务自动取消
- **回调丢失** → 前端轮询支付状态 + 超时提示
- **并发冲突** → 数据库唯一约束 + 事务保证

## OpenSpec 变更

所有改动合并到 `openspec/changes/update-order-payment-wechat/`，已更新：
- `proposal.md` — 增加 UI 对齐范围
- `design.md` — 增加 D6/D7/D8 决策
- `specs/study-room-booking-ui/spec.md` — 卡券弹窗、成功弹窗简化、视觉风格对齐
- `tasks.md` — 第 6 组增加 UI 对齐任务（8 项）
