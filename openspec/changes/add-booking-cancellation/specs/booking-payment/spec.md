## ADDED Requirements

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
