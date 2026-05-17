## ADDED Requirements

### Requirement: Invoke WeChat payment from recharge page
小程序充值页 SHALL 使用后端返回的微信支付参数调用 `uni.requestPayment`，完成微信支付唤起。

#### Scenario: Start WeChat payment successfully
- **GIVEN** 用户已登录并选择微信支付
- **WHEN** 用户点击“立即充值”
- **THEN** 前端调用 `POST /api/v1/wallet/recharge`
- **AND** 使用响应中的 `payment_params` 调用 `uni.requestPayment`
- **AND** 支付处理中按钮不可重复点击

#### Scenario: Missing payment params
- **GIVEN** 后端创建订单成功但未返回 `payment_params`
- **WHEN** 前端准备唤起微信支付
- **THEN** 显示“支付创建失败，请重试”
- **AND** 不调用 `uni.requestPayment`

### Requirement: Confirm payment result by backend status
小程序充值页 SHALL 在微信支付控件返回后查询后端充值订单状态，不得仅凭客户端支付控件 success 展示最终入账成功。

#### Scenario: Payment completed after polling
- **GIVEN** `uni.requestPayment` 返回 success
- **WHEN** 前端轮询 `GET /api/v1/wallet/recharge/{order_id}` 且响应 `status="completed"`
- **THEN** 显示“充值成功”
- **AND** 刷新钱包余额

#### Scenario: Payment callback delayed
- **GIVEN** `uni.requestPayment` 返回 success
- **WHEN** 前端轮询多次后订单仍未 completed
- **THEN** 显示“支付处理中，请稍后查看余额”
- **AND** 不本地增加余额

#### Scenario: User cancels payment
- **WHEN** `uni.requestPayment` 返回取消支付错误
- **THEN** 显示“支付已取消”
- **AND** 保持当前余额不变

#### Scenario: Payment fails
- **WHEN** `uni.requestPayment` 返回非取消类错误
- **THEN** 显示“支付失败，请重试”
- **AND** 保持当前余额不变

### Requirement: Unsupported payment methods
充值页 SHALL 防止用户提交尚未接通的支付方式。

#### Scenario: User selects Alipay
- **WHEN** 用户选择支付宝并点击充值
- **THEN** 前端提示“暂未开通”
- **AND** 不创建充值订单

### Requirement: Recharge page state management
充值页 SHALL 区分创建订单、微信支付、支付处理中和完成状态，避免重复提交或错误提示。

#### Scenario: Repeated submit while paying
- **GIVEN** 当前充值正在创建订单或等待支付结果
- **WHEN** 用户重复点击充值按钮
- **THEN** 前端忽略重复点击
- **AND** 不创建第二笔充值订单
