# Design: 已取消订单隐藏"去支付"和"取消"按钮

## 修复方案

### 模板改动

在 `br-app/src/pages/orders/index.vue` 的 `card-action-row` 中，将两个待支付按钮的 `v-if` 条件从：

```vue
v-if="order.payment_status === 'pending'"
```

改为：

```vue
v-if="order.payment_status === 'pending' && order.status !== 'cancelled'"
```

涉及第 100 行和第 107 行两个 `view` 组件："去支付"按钮和"取消"按钮。

### 行为说明

- 当订单 `status === 'cancelled'` 时，无论 `payment_status` 为何值，都不显示待支付操作按钮
- 已取消订单将落入后续分支，仅显示"重新预约"按钮（如原有逻辑已支持）
- 不影响待支付且未取消订单的正常操作
