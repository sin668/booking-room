## MODIFIED Requirements

### Requirement: Order confirm page
系统 SHALL 提供订单确认页（`pages/booking/confirm.vue`），整体 UI 参照 `prototype/order-confirm.html` 原型图。页面包含：门店信息卡片（名称、楼层）、座位信息卡片（座位号、区域、位置）、日期和时段信息、卡券简洁行（ticket 图标 + "优惠券" + 折扣金额 + 右箭头，点击弹出选择弹窗）、支付方式选择区（账户余额/微信支付，radio 样式，默认选中余额）、费用明细（座位费、优惠券抵扣、实付金额）、底部固定栏（合计金额 + "立即支付"按钮）。选择余额支付时直接创建预约，选择微信支付时唤起微信支付控件并在支付成功后确认预约。提交成功后弹出预约成功弹窗（简洁 4 行摘要），关闭后跳转到"订单"tab 页。

#### Scenario: Display booking summary
- **GIVEN** 用户进入确认页
- **WHEN** 页面加载预约参数
- **THEN** 页面展示门店名称、楼层（如"3楼"）、座位号、区域、位置、预约日期、时段、卡券简洁行、支付方式选择、费用明细

#### Scenario: Display coupon row
- **GIVEN** 用户进入确认页
- **WHEN** 页面加载完成
- **THEN** 页面展示卡券简洁行，包含 ticket 图标、"优惠券"文字、右箭头图标
- **AND** 未选择卡券时行样式为引导点击状态

#### Scenario: Display coupon row with selected coupon
- **GIVEN** 用户已选择一张可用卡券
- **WHEN** 页面渲染
- **THEN** 卡券简洁行显示该卡券的折扣金额（如"-¥3.00"）和右箭头
- **AND** 费用明细中优惠券抵扣金额更新
- **AND** 底部合计金额更新为抵扣后的实付金额

#### Scenario: Open coupon selection popup
- **GIVEN** 页面加载了可用卡券列表
- **WHEN** 用户点击卡券简洁行
- **THEN** 弹出底部弹窗（bottom sheet），展示可用卡券列表
- **AND** 每张卡券显示名称、描述、折扣金额和实付金额
- **AND** 已选卡券显示选中态

#### Scenario: Select coupon from popup
- **GIVEN** 卡券选择弹窗已打开
- **WHEN** 用户在弹窗中选择一张卡券
- **THEN** 弹窗关闭
- **AND** 卡券简洁行更新为该卡券的折扣金额
- **AND** 费用明细和底部合计金额同步更新

#### Scenario: Clear selected coupon from popup
- **GIVEN** 卡券选择弹窗已打开且用户已选择一张卡券
- **WHEN** 用户在弹窗中选择"不使用卡券"
- **THEN** 弹窗关闭
- **AND** 卡券简洁行恢复为未选择状态
- **AND** 费用明细和底部合计金额恢复为原价

#### Scenario: No available coupons
- **GIVEN** 当前订单没有可用卡券
- **WHEN** 用户点击卡券简洁行
- **THEN** 显示提示"暂无可用卡券"
- **AND** 不弹出选择弹窗

#### Scenario: Load available coupons for booking
- **GIVEN** 用户进入确认页且预约参数完整
- **WHEN** 页面加载完成
- **THEN** 页面请求 `GET /api/v1/coupons/available-for-booking`
- **AND** 卡券简洁行根据可用卡券数量显示对应状态

#### Scenario: Clear selected coupon
- **GIVEN** 用户已选择一张卡券
- **WHEN** 用户取消选择卡券
- **THEN** 费用明细中的优惠券抵扣恢复为 0
- **AND** 底部合计金额恢复为订单原价

#### Scenario: Confirm booking with balance payment
- **GIVEN** 用户选择"账户余额"且余额充足
- **WHEN** 用户点击"立即支付"按钮，后端返回 201
- **THEN** 显示预约成功弹窗（简洁摘要：门店、座位、时间、支付金额）
- **AND** 关闭弹窗后跳转到"订单"tab 页

#### Scenario: Balance insufficient prompt
- **GIVEN** 用户选择"账户余额"且余额不足
- **WHEN** 用户点击"立即支付"按钮
- **THEN** 显示"余额不足，请切换微信支付或先充值"提示
- **AND** 留在当前页

#### Scenario: Confirm booking with WeChat payment
- **GIVEN** 用户选择"微信支付"
- **WHEN** 用户点击"立即支付"按钮，后端返回 201 含 `payment_params`
- **THEN** 前端使用 `payment_params` 调用 `uni.requestPayment`
- **AND** 支付处理中按钮不可重复点击

#### Scenario: WeChat payment success
- **GIVEN** 用户选择微信支付且 `uni.requestPayment` 返回 success
- **WHEN** 前端轮询 `GET /api/v1/bookings/{id}/payment-status` 且 `payment_status='paid'`
- **THEN** 显示预约成功弹窗
- **AND** 关闭弹窗后跳转到"订单"tab 页

#### Scenario: WeChat payment cancelled
- **GIVEN** 用户选择微信支付且 `uni.requestPayment` 返回取消
- **WHEN** 支付取消
- **THEN** 显示"支付已取消"提示
- **AND** 留在当前页，允许重新支付

#### Scenario: Submit booking with selected coupon
- **GIVEN** 用户已选择一张可用卡券
- **WHEN** 用户点击"立即支付"按钮
- **THEN** 前端创建预约请求体包含 `coupon_id`

#### Scenario: Handle coupon unavailable during submit
- **GIVEN** 用户选择的卡券在提交前已失效或被使用
- **WHEN** 用户点击"立即支付"按钮且后端返回卡券不可用错误
- **THEN** 页面显示"卡券不可用，请重新选择"
- **AND** 重新加载可用卡券列表

#### Scenario: Handle booking conflict
- **GIVEN** 用户位于确认页
- **WHEN** 用户点击"立即支付"按钮，后端返回 409 时间冲突
- **THEN** 显示错误提示"该座位该时段已被预约，请重新选择"
- **AND** 留在当前页

#### Scenario: Handle network error
- **GIVEN** 用户位于确认页
- **WHEN** 用户点击"立即支付"按钮，网络请求失败
- **THEN** 显示错误提示"预约失败，请重试"

#### Scenario: Payment method selector UI
- **GIVEN** 页面渲染完成
- **WHEN** 支付方式选择区显示
- **THEN** "账户余额"选项显示钱包图标和当前余额（如 ¥256.00），"微信支付"选项显示微信图标，两个选项以 radio 样式排列在独立卡片中，默认选中"账户余额"（蓝色选中态）

#### Scenario: Store info displays floor instead of address
- **GIVEN** 页面加载门店数据
- **WHEN** 门店信息卡片渲染
- **THEN** 卡片第二行显示楼层（如"3楼"），不显示完整地址

#### Scenario: Success modal displays simplified summary
- **GIVEN** 预约支付成功
- **WHEN** 成功弹窗显示
- **THEN** 弹窗包含：标题"预约成功"、订单编号、4 行摘要（门店、座位、时间、支付金额）
- **AND** 不显示原价和优惠抵扣字段

### Requirement: Visual style alignment
订单确认页 SHALL 参照 `prototype/order-confirm.html` 原型图的视觉风格，保持整体一致性。

#### Scenario: Card styling
- **GIVEN** 页面渲染
- **WHEN** 各卡片（门店信息、座位信息、卡券、支付方式、费用明细）显示
- **THEN** 卡片使用 `rounded-2xl` 圆角（16rpx）、白色背景、轻微阴影，与原型一致

#### Scenario: Icon styling
- **GIVEN** 页面渲染
- **WHEN** 各区域图标显示（门店、座位、日期、时钟、钱包、微信、卡券）
- **THEN** 图标使用原型中的颜色和尺寸：门店 primary-blue、座位 green、日期 amber、时钟 purple、钱包 primary-blue、微信 green、卡券 red
