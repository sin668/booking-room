# Proposal: 订单列表页增加待支付订单操作按钮

## 问题描述

br-app 的 `/pages/orders/index` 订单列表页面中，当订单的 `payment_status === "pending"`（待支付）时，卡片底部没有显示任何操作按钮。用户无法从订单列表直接发起支付或取消待支付订单，只能通过其他路径操作。

## 根因分析

`orders/index.vue` 的 `card-action-row` 区域仅根据 `order.status` 条件渲染按钮：
- `confirmed` → 显示"查看座位" + "取消"（当 `can_cancel === true`）
- `completed` → 显示"再来一单"
- `cancelled` → 显示"重新预约"

缺少对 `payment_status === "pending"` 的判断分支。后端 `BookingResponse` 已返回 `payment_status` 字段，前端未消费该字段来渲染对应操作按钮。

## 修复目标

1. 当 `payment_status === "pending"` 时，在订单卡片底部显示"去支付"和"取消"按钮
2. "去支付"跳转到已有的 `booking/confirm.vue` 支付页面，携带 `booking_id` 参数
3. "取消"复用已有的 `confirmCancelBooking` 逻辑，取消订单并释放座位锁定状态
4. 不引入新 API，不涉及后端改动
