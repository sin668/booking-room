# Tasks: 订单列表页待支付按钮

## Task 1: 模板 — 增加待支付按钮

在 `card-action-row` 中增加 `payment_status === "pending"` 条件分支，渲染"去支付"和"取消"按钮。

- [x] 在 `confirmed` 分支之前增加 `payment_status === "pending"` 的 `v-if` 块
- [x] "去支付"按钮调用 `goPay(order)`
- [x] "取消"按钮复用 `confirmCancelBooking(order)`，含 `cancellingOrderId` loading 状态
- [x] 原有 `can_cancel` 取消按钮增加 `payment_status !== 'pending'` 条件避免重复

## Task 2: 方法 — 新增 goPay

在 `methods` 中新增 `goPay(order)` 方法，携带 `booking_id` + 座位/房间/时间参数导航到 `booking/confirm` 页面。

- [x] 使用 `uni.navigateTo` 跳转到 `/pages/booking/confirm?booking_id=${order.id}&room_id=...&seat_id=...&date=...&start_time=...&end_time=...`

## Task 3: 样式 — pay-action-btn

新增 `.pay-action-btn` 和 `.pay-action-text` 样式。

- [x] `.pay-action-btn`：渐变背景填充按钮
- [x] `.pay-action-text`：白色文字

## Task 4: 后端 — cancel_booking 支持 pending 订单

修改 `booking_service.cancel_booking` 允许取消 `status=pending` + `payment_status=pending` 的订单，跳过退款逻辑。

- [x] 在 `cancel_booking` 中新增 pending 分支：设 status=cancelled、cancelled_at=now、恢复卡券、跳过退款
- [x] 不影响原有 confirmed+paid 订单的取消退款流程

## Task 5: 后端 — 新增 pay 端点

新增 `POST /api/v1/bookings/{booking_id}/pay` 端点，处理已有待支付订单的支付。

- [x] 新增 `PayPendingBooking` schema（仅含 `payment_method`）
- [x] 新增 `pay_pending_booking` service 函数（余额扣款 + 微信支付参数）
- [x] 新增路由处理函数，微信支付先创建 payment params 再调用 service

## Task 6: 前端 — API 层 + service 层

新增 `payBooking` API 函数和 `payPendingBooking` service 包装。

- [x] `bookings.js` 新增 `payBooking(bookingId, paymentMethod)`
- [x] `bookingPageService.js` 新增 `payPendingBooking` 包装

## Task 7: 前端 — confirm.vue 支持 booking_id

修改 `confirm.vue` 支持加载已有订单并支付。

- [x] `onLoad` 接收 `booking_id` 参数，设置 `isExistingBooking` computed
- [x] `onPay` 分支：已有订单调用 `payPendingBooking`，新订单调用 `createBookingOrder`
- [x] 优惠券对已有订单禁用选择（`openCouponSheet` 返回 + `couponSummaryText` 显示"不可更改"）
- [x] 跳过已有订单的优惠券加载
- [x] 成功弹窗标题动态：已有订单"支付成功" / 新订单"预约成功"
