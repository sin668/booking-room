## MODIFIED Requirements

### Requirement: Order confirm page
系统 SHALL 提供订单确认页（`pages/booking/confirm.vue`），参照 `prototype/order-confirm.html`。页面包含：门店信息卡片（名称、楼层）、座位信息卡片（座位号、区域、位置）、日期和时段信息、卡券选择区、费用明细（座位费、优惠券抵扣、实付金额）、底部固定栏（合计金额 + "立即支付"按钮）。MVP 阶段"立即支付"直接创建预约，不接入真实支付。提交成功后弹出预约成功弹窗，关闭后跳转到"订单"tab 页。

#### Scenario: Display booking summary
- **GIVEN** 用户进入确认页
- **WHEN** 页面加载预约参数
- **THEN** 页面展示门店名称、楼层、座位号、区域、位置、预约日期、时段、费用明细

#### Scenario: Load available coupons for booking
- **GIVEN** 用户进入确认页且预约参数完整
- **WHEN** 页面加载完成
- **THEN** 页面请求 `GET /api/v1/coupons/available-for-booking`
- **AND** 展示该订单可用的卡券数量和列表入口

#### Scenario: Select coupon and update payable amount
- **GIVEN** 确认页存在可用卡券
- **WHEN** 用户选择一张卡券
- **THEN** 费用明细展示该卡券抵扣金额
- **AND** 底部合计金额更新为抵扣后的实付金额

#### Scenario: Clear selected coupon
- **GIVEN** 用户已选择一张卡券
- **WHEN** 用户取消选择卡券
- **THEN** 费用明细中的优惠券抵扣恢复为 0
- **AND** 底部合计金额恢复为订单原价

#### Scenario: Confirm booking successfully
- **GIVEN** 用户位于确认页
- **WHEN** 用户点击"立即支付"按钮，后端返回 201
- **THEN** 显示预约成功弹窗（含订单编号、预约摘要、原价、抵扣金额和实付金额）
- **AND** 关闭弹窗后跳转到"订单"tab 页

#### Scenario: Submit booking with selected coupon
- **GIVEN** 用户已选择一张可用卡券
- **WHEN** 用户点击"立即支付"按钮
- **THEN** 前端创建预约请求体包含 `coupon_id`

#### Scenario: Handle coupon unavailable during submit
- **GIVEN** 用户选择的卡券在提交前已失效或被使用
- **WHEN** 用户点击"立即支付"按钮且后端返回卡券不可用错误
- **THEN** 页面显示“卡券不可用，请重新选择”
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
