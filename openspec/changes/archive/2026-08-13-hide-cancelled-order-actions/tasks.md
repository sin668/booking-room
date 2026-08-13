# Tasks: 已取消订单隐藏"去支付"和"取消"按钮

## Task 1: 修改订单卡片按钮渲染条件

在 `br-app/src/pages/orders/index.vue` 中，将"去支付"和"取消"两个待支付按钮的 `v-if` 条件增加 `order.status !== 'cancelled'` 判断。

- [x] 第 100 行"去支付"按钮条件改为 `order.payment_status === 'pending' && order.status !== 'cancelled'`
- [x] 第 107 行"取消"按钮条件改为 `order.payment_status === 'pending' && order.status !== 'cancelled'`

## Task 2: 构建验证

- [x] 运行 `npm run build:h5` 确认无编译错误
