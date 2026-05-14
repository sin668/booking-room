## ADDED Requirements

### Requirement: Recharge page displays user balance
充值页面 SHALL 在顶部展示用户当前账户余额和累计充值金额，样式参考 `prototype/recharge.html` 的渐变余额卡片。

#### Scenario: User views recharge page with existing balance
- **WHEN** 用户从 Profile 页点击"钱包充值"进入充值页
- **THEN** 页面展示余额卡片，显示当前余额（如 ¥256.00）和累计充值金额

#### Scenario: User views recharge page with zero balance
- **WHEN** 新用户首次进入充值页，余额为 0
- **THEN** 页面正常展示，余额显示 ¥0.00，累计充值显示 ¥0.00

### Requirement: User can select recharge amount
页面 SHALL 提供 6 个预设金额选项（¥30/50/100/200/500/自定义），用户点击后高亮选中状态，底部按钮文字同步更新。

#### Scenario: User selects a preset amount
- **WHEN** 用户点击 ¥100 选项
- **THEN** 该选项高亮（primary 边框+背景色），底部按钮变为"立即充值 ¥100"

#### Scenario: User taps custom amount
- **WHEN** 用户点击"自定义"选项
- **THEN** 弹出输入框让用户输入自定义金额（最小 1 元，最大 9999 元）

#### Scenario: Default selection
- **WHEN** 页面首次加载
- **THEN** ¥50 选项默认选中，底部按钮显示"立即充值 ¥50"

### Requirement: User can select payment method
页面 SHALL 展示支付方式列表（微信支付、支付宝），用户可选择其中一种。

#### Scenario: Default payment method
- **WHEN** 页面加载
- **THEN** 微信支付默认选中（蓝色圆点），支付宝未选中

#### Scenario: User switches payment method
- **WHEN** 用户点击支付宝
- **THEN** 支付宝变为选中状态，微信支付取消选中

### Requirement: User can enter promo code
页面 SHALL 提供优惠码输入框和兑换按钮，兑换成功后提示优惠信息。

#### Scenario: Valid promo code
- **WHEN** 用户输入有效优惠码并点击"兑换"
- **THEN** 显示兑换成功提示，充值金额区域展示优惠信息（如"充值100送30"）

#### Scenario: Invalid promo code
- **WHEN** 用户输入无效优惠码
- **THEN** 提示"优惠码无效或已使用"

### Requirement: User initiates recharge
页面 SHALL 在底部提供固定充值按钮，点击后调用后端 API 创建充值订单。

#### Scenario: Successful recharge
- **WHEN** 用户选择金额 ¥100、微信支付，点击"立即充值 ¥100"
- **THEN** 调用 `POST /api/wallet/recharge`，成功后更新余额显示，提示"充值成功"

#### Scenario: Recharge with promo code applied
- **WHEN** 用户已兑换优惠码（充100送30），选择 ¥100 并充值
- **THEN** 实际到账 ¥130，余额卡片更新为新的余额值

#### Scenario: Network error during recharge
- **WHEN** 网络异常导致充值请求失败
- **THEN** 按钮恢复可点击状态，提示"充值失败，请重试"

### Requirement: Recharge page follows existing app style
页面 SHALL 与 `prototype/recharge.html` 原型图保持一致，使用项目统一的 primary 色（#4F6EF7）、圆角卡片、底部固定按钮等设计规范。

#### Scenario: Visual consistency check
- **WHEN** 充值页面渲染完成
- **THEN** 页面布局、配色、间距与原型图一致，导航栏有返回箭头和标题"钱包充值"
