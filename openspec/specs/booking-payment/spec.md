## ADDED Requirements

### Requirement: Booking payment method selection
系统 SHALL 在订单确认页提供支付方式选择，支持"账户余额"和"微信支付"两种方式。默认选中"账户余额"。UI 参照 `prototype/order-confirm.html` 原型图，使用 radio 样式展示选项。

#### Scenario: Display payment method selector
- **GIVEN** 用户进入订单确认页
- **WHEN** 页面加载完成
- **THEN** 页面显示支付方式选择区域，包含"账户余额"选项（显示当前余额金额）和"微信支付"选项
- **AND** "账户余额"默认选中，radio 样式显示蓝色选中态

#### Scenario: Select WeChat payment
- **GIVEN** 用户位于订单确认页
- **WHEN** 用户点击"微信支付"选项
- **THEN** "微信支付"显示蓝色选中态，"账户余额"取消选中
- **AND** 底部按钮文字保持"立即支付"

#### Scenario: Select balance payment
- **GIVEN** 用户已选择"微信支付"
- **WHEN** 用户点击"账户余额"选项
- **THEN** "账户余额"显示蓝色选中态，"微信支付"取消选中

### Requirement: Balance payment insufficient warning
当选择余额支付且余额不足时，系统 SHALL 在支付方式旁显示余额不足提示，但仍允许用户切换到微信支付。

#### Scenario: Show insufficient balance warning
- **GIVEN** 用户选择"账户余额"支付
- **AND** 账户余额小于实付金额
- **WHEN** 页面渲染
- **THEN** "账户余额"选项旁显示余额不足提示文字

#### Scenario: Switch to WeChat when balance insufficient
- **GIVEN** 用户选择"账户余额"且余额不足
- **WHEN** 用户点击"微信支付"
- **THEN** 切换到微信支付选中态
- **AND** 余额不足提示消失

### Requirement: Booking payment with balance
系统 SHALL 在用户选择"账户余额"时，使用现有余额扣款逻辑创建预约，行为与改造前一致。

#### Scenario: Pay with sufficient balance
- **GIVEN** 用户选择"账户余额"且余额充足
- **WHEN** 用户点击"立即支付"
- **THEN** 系统创建预约并扣除余额
- **AND** 预约 `payment_method='balance'`、`payment_status='paid'`
- **AND** 显示预约成功弹窗

#### Scenario: Pay with insufficient balance
- **GIVEN** 用户选择"账户余额"且余额不足
- **WHEN** 用户点击"立即支付"
- **THEN** 系统返回余额不足错误
- **AND** 显示"余额不足，请切换微信支付或先充值"提示

### Requirement: Booking payment with WeChat Pay
系统 SHALL 在用户选择"微信支付"时，创建 pending 状态的预约并返回微信 JSAPI 支付参数。

#### Scenario: Create booking with WeChat payment
- **GIVEN** 用户选择"微信支付"且微信支付配置可用
- **WHEN** 用户点击"立即支付"
- **THEN** 系统创建预约，`payment_method='wechat'`、`payment_status='pending'`
- **AND** 系统调用微信支付 JSAPI 下单获取 `prepay_id`
- **AND** 返回 201，响应包含 `payment_params`（timeStamp、nonceStr、package、signType、paySign）
- **AND** 前端使用 `payment_params` 调用 `uni.requestPayment`

#### Scenario: WeChat Pay disabled
- **GIVEN** 用户选择"微信支付"
- **AND** `WECHAT_PAY_ENABLED=false`
- **WHEN** 用户点击"立即支付"
- **THEN** 显示"微信支付暂不可用"提示

#### Scenario: WeChat Pay creation failure
- **GIVEN** 用户选择"微信支付"
- **WHEN** 后端调用微信支付下单失败
- **THEN** 显示"支付创建失败，请重试"提示
- **AND** 不创建预约记录

### Requirement: Booking WeChat payment callback
系统 SHALL 提供 `POST /api/v1/bookings/wechat/notify` 处理微信支付订单的异步通知，支付成功后确认预约。

#### Scenario: Process successful booking payment notification
- **GIVEN** 存在 `payment_status='pending'` 的预约
- **WHEN** 微信支付发送签名有效、金额匹配、`trade_state='SUCCESS'` 的通知
- **THEN** 系统更新预约 `payment_status='paid'`、`paid_at`、`transaction_id`
- **AND** 返回微信要求的成功响应

#### Scenario: Duplicate booking payment notification
- **GIVEN** 预约已经 `payment_status='paid'`
- **WHEN** 微信支付再次发送同一订单的成功通知
- **THEN** 系统返回成功响应，不重复更新

#### Scenario: Booking payment notification amount mismatch
- **GIVEN** 预约 `total_price=9.00`
- **WHEN** 微信通知金额不为 9.00
- **THEN** 系统拒绝处理，记录错误日志，预约保持 pending

### Requirement: Booking payment status query
系统 SHALL 提供 `GET /api/v1/bookings/{booking_id}/payment-status` 供前端轮询支付结果。

#### Scenario: Query pending payment
- **GIVEN** 预约 `payment_status='pending'`
- **WHEN** 前端查询支付状态
- **THEN** 返回 `payment_status='pending'`

#### Scenario: Query paid booking
- **GIVEN** 预约 `payment_status='paid'`
- **WHEN** 前端查询支付状态
- **THEN** 返回 `payment_status='paid'`、`paid_at`、`transaction_id`

### Requirement: WeChat payment flow UI management
前端 SHALL 在微信支付流程中管理状态（创建订单、唤起支付、轮询结果、完成），避免重复提交。

#### Scenario: Prevent duplicate submission during WeChat payment
- **GIVEN** 用户正在等待微信支付结果
- **WHEN** 用户重复点击"立即支付"
- **THEN** 前端忽略重复点击

#### Scenario: WeChat payment cancelled by user
- **GIVEN** 前端调用 `uni.requestPayment`
- **WHEN** 用户取消支付
- **THEN** 显示"支付已取消"
- **AND** 不自动取消预约，允许用户重新支付

#### Scenario: WeChat payment failed
- **GIVEN** 前端调用 `uni.requestPayment`
- **WHEN** 支付返回非取消类错误
- **THEN** 显示"支付失败，请重试"

#### Scenario: Poll payment result after WeChat success
- **GIVEN** `uni.requestPayment` 返回 success
- **WHEN** 前端轮询 `GET /api/v1/bookings/{id}/payment-status`
- **AND** 响应 `payment_status='paid'`
- **THEN** 显示预约成功弹窗
- **AND** 关闭弹窗后跳转到"订单"tab 页

#### Scenario: Payment callback delayed
- **GIVEN** `uni.requestPayment` 返回 success
- **WHEN** 前端轮询多次后 `payment_status` 仍为 'pending'
- **THEN** 显示"支付处理中，请稍后在订单中查看"

### Requirement: Unpaid booking timeout cleanup
系统 SHALL 对 `payment_status='pending'` 超过 15 分钟的预约自动取消并释放座位。

#### Scenario: Auto-cancel unpaid booking
- **GIVEN** 预约创建超过 15 分钟且 `payment_status='pending'`
- **WHEN** 定时任务扫描
- **THEN** 预约状态变为 'cancelled'
- **AND** 若使用了卡券，卡券恢复为可用
- **AND** 座位时段释放

### Requirement: Booking cancellation refund settlement
系统 SHALL 在已支付预约取消成功时，将可退金额退回用户钱包，并记录扣款金额、退款金额和退款流水。退款金额 SHALL 基于预约 `total_price` 计算，不基于原价或优惠前金额。余额支付和微信支付预约取消后均退回钱包余额，不进行微信原路退款。系统创建的钱包流水类型 MUST 为 `booking_refund`，钱包流水展示标题 MUST 为“取消退款”。

#### Scenario: Refund based on paid amount
- **GIVEN** 预约 `original_price=120.00`、`discount_amount=20.00`、`total_price=100.00`
- **AND** 当前取消规则扣 10%
- **WHEN** 用户取消预约
- **THEN** 系统按 `total_price=100.00` 计算扣款
- **AND** `penalty_amount=10.00`
- **AND** `refund_amount=90.00`

#### Scenario: Balance payment refund to wallet
- **GIVEN** 用户使用余额支付了一笔预约
- **WHEN** 用户成功取消该预约
- **THEN** 系统将可退金额加回用户钱包余额
- **AND** 创建 `type='booking_refund'` 的预约取消退款钱包流水
- **AND** 钱包流水展示标题为“取消退款”

#### Scenario: WeChat payment refund to wallet
- **GIVEN** 用户使用微信支付且预约 `payment_status='paid'`
- **WHEN** 用户成功取消该预约
- **THEN** 系统将可退金额加到用户钱包余额
- **AND** 不调用微信原路退款
- **AND** 创建 `type='booking_refund'` 的预约取消退款钱包流水
- **AND** 钱包流水展示标题为“取消退款”

#### Scenario: Atomic settlement
- **GIVEN** 用户取消一笔可取消预约
- **WHEN** 系统执行取消结算
- **THEN** 订单状态更新、余额增加、钱包流水创建在同一数据库事务内完成
- **AND** 任一步失败时所有变更回滚

#### Scenario: No refund for invalid cancellation
- **GIVEN** 预约已取消、未支付、属于其他用户或已到开始时间
- **WHEN** 用户请求取消预约
- **THEN** 系统不增加用户钱包余额
- **AND** 不创建退款流水

#### Scenario: Decimal rounding
- **GIVEN** 预约实付金额无法按扣款比例整除到分
- **WHEN** 系统计算扣款金额和退款金额
- **THEN** 金额按人民币两位小数稳定取值
- **AND** `penalty_amount + refund_amount = total_price`
