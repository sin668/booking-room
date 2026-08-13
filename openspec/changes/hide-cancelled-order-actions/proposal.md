# Proposal: 已取消订单隐藏"去支付"和"取消"按钮

## Why

用户反馈：订单列表中，当订单被点击"取消"后，状态会变为"已取消"，但卡片底部仍然同时显示"去支付"和"取消"按钮。这会让用户误以为已取消的订单仍可继续支付或再次取消。

## What Changes

在 `br-app/src/pages/orders/index.vue` 中，将"去支付"和"取消"按钮的渲染条件从仅判断 `payment_status === 'pending'` 改为同时判断 `payment_status === 'pending' && status !== 'cancelled'`。

## Scope

- 仅修改 `br-app/src/pages/orders/index.vue`
- 不改动后端 API 或数据模型
- 不引入新功能
