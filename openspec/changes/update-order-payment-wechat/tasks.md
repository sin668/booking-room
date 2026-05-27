## 1. 数据库迁移 — Booking 模型增加支付字段

- [x] 1.1 创建 alembic 迁移文件 `br-server/alembic/versions/`：`bookings` 表新增 `payment_method`（VARCHAR(20), default 'balance', nullable=False）、`payment_status`（VARCHAR(20), default 'paid', nullable=False）、`payment_provider`（VARCHAR(20), nullable）、`prepay_id`（VARCHAR(64), nullable）、`transaction_id`（VARCHAR(64), nullable）、`paid_at`（TIMESTAMP, nullable）
- [x] 1.2 迁移数据回填：所有现有 `bookings` 记录设置 `payment_method='balance'`、`payment_status='paid'`
- [x] 1.3 更新 SQLAlchemy 模型 `br-server/app/models/booking.py`：添加上述 6 个字段及 `PaymentMethod`、`PaymentStatus` 枚举类型
- [ ] 1.4 执行迁移验证：`alembic upgrade head` 成功，确认现有 booking 数据的 `payment_method` 和 `payment_status` 已正确回填

## 2. 后端 — Schema 和 Service 层

- [x] 2.1 更新 Pydantic schema `br-server/app/schemas/booking.py`：`CreateBookingRequest` 增加 `payment_method` 字段（`PaymentMethodEnum`，默认 'balance'，校验 'balance'/'wechat'）；`BookingResponse` 增加 `payment_method`、`payment_status`、`paid_at`、`payment_provider` 字段；新增 `PaymentStatusResponse` schema（payment_status、paid_at、transaction_id）；新增 `WeChatPaymentParams` schema（timeStamp、nonceStr、package、signType、paySign）；`CreateBookingResponse` 在微信支付时额外包含 `payment_params` 字段
- [x] 2.2 新建 `br-server/app/services/booking_payment_service.py`：封装 `create_booking_payment(booking, user)` 方法，内部调用 `wechat_pay_client.create_order()` 获取 prepay_id 和 payment_params，订单号格式 `BK-{booking_id}`，description 为 "{门店名} {座位号} {日期} {时段}"；封装 `process_wechat_notify(notification)` 方法处理回调：签名校验 → 金额匹配 → 更新 booking；封装 `query_payment_status(booking_id, user_id)` 查询支付状态
- [x] 2.3 单元测试 `br-server/tests/test_booking_payment_service.py`：测试 `create_booking_payment` 正常下单（mock wechat_pay_client）、微信配置不可用抛异常、下单失败回滚；测试 `process_wechat_notify` 成功更新、重复通知幂等、金额不匹配拒绝

## 3. 后端 — Booking API 修改 + 新增 Endpoint

- [x] 3.1 修改 `br-server/app/api/routes/booking.py` 中 `POST /api/v1/bookings/`：从 request body 读取 `payment_method`（默认 'balance'）；`payment_method='balance'` 分支：走现有 `booking_service.create_booking()` 余额扣款逻辑，设置 `payment_method='balance'`、`payment_status='paid'`；`payment_method='wechat'` 分支：创建 `payment_status='pending'` 的 booking（不扣余额），调用 `booking_payment_service.create_booking_payment()` 获取 payment_params，返回 201 + payment_params
- [x] 3.2 新增 `POST /api/v1/bookings/wechat/notify` endpoint：调用 `booking_payment_service.process_wechat_notify()`，返回微信要求的成功/失败响应格式
- [x] 3.3 新增 `GET /api/v1/bookings/{booking_id}/payment-status` endpoint：调用 `booking_payment_service.query_payment_status()`，校验 booking 归属当前用户，返回 `PaymentStatusResponse`
- [x] 3.4 在 `br-server/app/main.py` 中确认新 endpoint 已通过 booking_router 注册（在同一路由文件中定义，无需额外注册）
- [x] 3.5 集成测试 `br-server/tests/test_booking_payment_api.py`：余额支付 201 + payment_status=paid；微信支付 201 + payment_params + payment_status=pending；余额不足 402；微信不可用 503；booking 不存在 404；支付状态查询自己的 200 + 他人的 404

## 4. 后端 — 未支付订单超时清理

- [x] 4.1 新建 `br-server/app/services/booking_cleanup_service.py`：实现 `cleanup_unpaid_bookings()` 函数，查询 `payment_status='pending'` 且 `created_at < now() - 15min` 的 bookings，逐个取消（status='cancelled'）、恢复卡券状态
- [x] 4.2 在 `br-server/app/main.py` 添加 APScheduler `BackgroundScheduler`：启动时注册 `cleanup_unpaid_bookings` 定时任务，间隔可配置（默认 300 秒），shutdown 时清理 scheduler
- [x] 4.3 单元测试 `br-server/tests/test_booking_cleanup.py`：测试超时 booking 被取消 + 卡券恢复；未超时 booking 不受影响；无 pending booking 时安全返回

## 5. 前端 — API 层 + 数据层

- [x] 5.1 在 `br-app/src/api/bookings.js` 新增 `getBookingPaymentStatus(bookingId)` 函数，调用 `GET /api/v1/bookings/{id}/payment-status`
- [x] 5.2 在 `br-app/src/api/bookings.js` 中 `createBooking()` 的 payload 增加 `payment_method` 参数传递

## 6. 前端 — 订单确认页 UI 重构（对齐原型）

- [x] 6.1 门店信息卡片改造 `br-app/src/pages/booking/confirm.vue`：第二行从 `roomAddress` 改为 `floor`（从 seat 数据中获取，显示如"3楼"），匹配 `prototype/order-confirm.html`
- [x] 6.2 卡券区重构：移除现有内联展开的 `.coupon-card` 卡片（含 coupon-header、coupon-list 等），替换为原型简洁行样式：ticket 红色图标 + "优惠券"文字 + 右侧显示已选卡券折扣金额（如"-¥3.00"）+ 右箭头 chevron
- [x] 6.3 新增卡券选择弹窗组件：底部弹出 bottom sheet，包含可用卡券列表（名称、描述、折扣金额、实付金额）+ "不使用卡券"选项，选择后关闭弹窗、更新 `selectedCoupon`、刷新费用明细；无可用卡券时点击简洁行提示"暂无可用卡券"
- [x] 6.4 移除现有 `.wallet-card` 独立卡片（钱包余额 + 刷新按钮），替换为"支付方式"选择卡片：标题"支付方式"，包含两个 radio 选项行 —— "账户余额"（蓝色钱包图标 + "账户余额" + 余额金额如"¥256.00"）和"微信支付"（绿色微信图标 + "微信支付"），radio 样式匹配原型（20px 圆点，选中蓝色 + 内蓝点），默认选中"账户余额"
- [x] 6.5 支付方式切换逻辑：新增 `paymentMethod` data 字段（默认 'balance'），`selectPaymentMethod(method)` 方法切换 radio 选中态
- [x] 6.6 余额不足提示：computed 属性 `isBalanceInsufficient`（`walletBalance < payableAmountNum`），为 true 时在"账户余额"行右侧显示红色"余额不足"文字
- [x] 6.7 成功弹窗简化：移除 `summary-row` 中的"原价"和"优惠抵扣"行，保留 4 行 —— 门店、座位（含区域）、时间、支付金额（primary 颜色加粗）
- [x] 6.8 视觉风格对齐原型：卡片圆角统一为 32rpx（`rounded-2xl`）、卡片间距 24rpx（margin: 24rpx 28rpx）、图标容器 72rpx 圆角正方形、图标颜色（门店 $primary、座位 $success/green、日期 amber、时钟 $purple、卡券 red）、radio 圆点 36rpx 外圈 18rpx 内点

## 7. 前端 — 微信支付流程

- [x] 7.1 `onPay` 方法重构：读取 `this.paymentMethod`；`'balance'` 分支走现有余额扣款逻辑（`payment_method: 'balance'`）；`'wechat'` 分支：调用 `createBooking({ ..., payment_method: 'wechat' })`，获取响应中的 `payment_params`，调用 `uni.requestPayment(payment_params)`
- [x] 7.2 微信支付轮询逻辑：`uni.requestPayment` success 后，以 2 秒间隔轮询 `getBookingPaymentStatus(booking.id)`，最多 10 次（20 秒）；`payment_status='paid'` 时显示成功弹窗；超时未 paid 显示"支付处理中，请稍后在订单中查看"
- [x] 7.3 微信支付取消处理：`uni.requestPayment` fail 且 err errMsg 含 'cancel' → 显示"支付已取消"，留在当前页，不取消 booking（允许重试）
- [x] 7.4 微信支付失败处理：`uni.requestPayment` fail 且非 cancel → 显示"支付失败，请重试"
- [x] 7.5 submitting 状态管理覆盖完整流程：创建订单 → 唤起支付 → 轮询结果全程禁用重复点击；余额支付微信支付失败后重置 submitting；最终成功/取消/失败后重置

## 8. 文档与代码审查

- [x] 8.1 更新 `docs/api.md`：补充 `POST /api/v1/bookings/` 新增 `payment_method` 参数说明和 `payment_params` 响应字段；补充 `GET /api/v1/bookings/{id}/payment-status` 接口文档；补充 `POST /api/v1/bookings/wechat/notify` 回调接口文档（含请求/响应格式）
- [x] 8.2 代码审查：确认 `booking_payment_service.py` 与 `wallet_service.py` 无重复支付逻辑；确认 `booking.py` schema 前后端字段一致；确认 `confirm.vue` 移除了所有 `.wallet-card` 相关的 dead code（template + script + style）
