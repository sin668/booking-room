# Design: 订单列表页待支付按钮

## 修复方案

在 `orders/index.vue` 的 `card-action-row` 区域增加 `payment_status === "pending"` 的条件分支，渲染"去支付"和"取消"两个按钮。

### 模板改动

在 `card-action-row` 中，在现有 `confirmed` 分支之前，增加待支付条件分支：

```html
<!-- 待支付：去支付 + 取消 -->
<view v-if="order.payment_status === 'pending'" class="action-btn pay-action-btn" @tap="goPay(order)">
  <text class="action-btn-text pay-action-text">去支付</text>
</view>
<view v-if="order.payment_status === 'pending'"
      :class="['action-btn', 'cancel-action-btn', { disabled: cancellingOrderId === order.id }]"
      @tap.stop="confirmCancelBooking(order)">
  <text class="action-btn-text cancel-action-text">
    {{ cancellingOrderId === order.id ? '取消中' : '取消' }}
  </text>
</view>
```

### 方法改动

新增 `goPay(order)` 方法，导航到支付确认页：

```js
goPay(order) {
  uni.navigateTo({
    url: `/pages/booking/confirm?booking_id=${order.id}`
  })
}
```

### 样式改动

新增 `.pay-action-btn` 样式（渐变背景填充按钮，区别于"取消"的描边按钮）。

### 注意事项（参考 bug-fixed.md）

- BUG-22 修复后，API 路径的尾部斜杠由 `StripTrailingSlashMiddleware` 统一处理，无需在 API 调用中去除斜杠
- BUG-12 教训：不要引用未定义的变量，确保新增的 `goPay` 方法在 `methods` 中正确定义
- 复用已有的 `confirmCancelBooking` / `handleCancelBooking`，不重复实现取消逻辑

## 影响范围

- 仅修改 `br-app/src/pages/orders/index.vue` 1 个文件
- 不涉及后端、不新增 API、不改数据库
