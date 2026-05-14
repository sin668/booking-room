## ADDED Requirements

### Requirement: Booking tab page
系统 SHALL 将 br-app"预约"tab 页改造为预约主页面，参照 `prototype/booking.html`。页面包含：顶部日期选择器（横向滚动，显示近 7 天）、时段选择网格（2 小时一档，可选/已满/已选三种状态）、区域筛选标签（全部/静音区/键盘区/VIP区）、座位平面图（按 row/col 布局，可选/已占/已选/VIP 四种样式）、底部座位信息栏（座位号、区域、位置、时段、费用）及"立即预约"按钮。点击"立即预约"跳转到确认页。

#### Scenario: Display booking tab with date and time selection
- **WHEN** 用户点击底部"预约" tab
- **THEN** 页面展示日期选择器（默认选中今天）、时段网格、区域筛选标签、座位平面图，底部显示"请选择座位"提示

#### Scenario: Select date and time slot
- **WHEN** 用户选择日期为 "2026-05-01"，时段为 "10:00-12:00"
- **THEN** 座位平面图更新显示该日期该时段的座位可用状态，已预约座位显示为已占样式

#### Scenario: Filter seats by zone
- **WHEN** 用户点击区域筛选标签选择"静音区"
- **THEN** 座位平面图仅显示 zone 为 "quiet" 的座位

#### Scenario: Select a seat
- **WHEN** 用户点击座位图中一个可选座位（如 A-01）
- **THEN** 座位高亮为已选样式，底部显示座位号（A-01号）、区域（静音区）、位置（靠窗）、时段（10:00-12:00）、费用（¥12.00），"立即预约"按钮变为可点击状态

#### Scenario: Navigate to confirm page
- **WHEN** 用户选择完座位后点击"立即预约"按钮
- **THEN** 跳转到订单确认页，传递 room_id、seat_id、date、start_time、end_time 参数

#### Scenario: Seat occupied display
- **WHEN** 某座位在所选时段已被预约
- **THEN** 座位显示为灰色已占样式，不可点击

### Requirement: Store detail page
系统 SHALL 提供门店详情页（`pages/booking/detail.vue`），参照 `prototype/store-detail.html`。页面包含：顶部封面大图、门店名称和营业状态标签、评分、地址（含距离）、营业时间、区域标签（静音区/键盘区/VIP区/WiFi/充电插座）、环境照片横向滚动列表、座位概况统计卡片（总座位/可用/已占/维护中）、底部固定栏（收藏按钮 + "立即预约"按钮）。点击"立即预约"跳转到座位选择页。

#### Scenario: Display store detail
- **WHEN** 用户进入详情页，`room_id=1`
- **THEN** 页面展示封面图、名称、营业状态、评分、地址、营业时间、区域标签、环境照片、座位概况统计

#### Scenario: Seat stats display
- **WHEN** 详情页加载完成
- **THEN** 座位概况卡片显示总座位数、可用数量（绿色）、已占数量（红色）、维护中数量（橙色）

#### Scenario: Navigate to seat select page
- **WHEN** 用户点击底部"立即预约"按钮
- **THEN** 跳转到座位选择页，传递 `room_id` 参数

#### Scenario: Room not found
- **WHEN** 用户进入详情页，`room_id` 对应的自习室不存在
- **THEN** 显示错误提示并返回上一页

### Requirement: Seat select page
系统 SHALL 提供座位选择页（`pages/booking/seat-select.vue`），参照 `prototype/seat-select.html`。页面包含：区域 tab 切换（全部/静音区/键盘区/VIP区，显示对应单价）、楼层选择器、座位平面图（分区域展示，含桌面/过道元素、靠窗标记）、图例说明（可选/已选/已占/VIP）、底部已选座位信息栏（座位号、区域、位置、时段、费用）及"确认选座"按钮。

#### Scenario: Display seat map by zone
- **WHEN** 用户进入座位选择页
- **THEN** 页面展示按区域分组的座位平面图（静音区、键盘区、VIP区），每个区域有标签和排号

#### Scenario: Switch zone tab
- **WHEN** 用户点击"VIP区" tab
- **THEN** 座位平面图仅显示 VIP 区域的座位，其他区域座位隐藏或置灰

#### Scenario: Select and confirm seat
- **WHEN** 用户选择一个可选座位
- **THEN** 座位高亮为已选样式，底部显示座位信息和"确认选座"按钮

#### Scenario: Navigate to confirm page
- **WHEN** 用户点击"确认选座"按钮
- **THEN** 跳转到订单确认页

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

### Requirement: My bookings list page
系统 SHALL 将 br-app"订单"tab 页改造为我的预约列表页，参照 `prototype/orders.html`。每条记录展示门店名称、座位号、预约日期、时间段、状态标签（不同状态不同颜色）。支持按状态筛选（全部/已确认/已取消/已完成）。

#### Scenario: Display bookings on orders tab
- **WHEN** 用户点击底部"订单" tab
- **THEN** 页面展示预约记录列表，每条记录包含门店名称、座位号、日期、时间段、状态标签

#### Scenario: Filter by status
- **WHEN** 用户点击顶部筛选标签选择"已确认"
- **THEN** 列表仅显示 status 为 "confirmed" 的预约记录

#### Scenario: Empty bookings state
- **WHEN** 用户没有任何预约记录
- **THEN** 显示空状态提示"暂无预约记录"，并提供"去预约"按钮跳转到预约页

#### Scenario: Booking status display
- **WHEN** 预约列表中存在不同状态的记录
- **THEN** confirmed 显示绿色"已确认"标签，cancelled 显示灰色"已取消"标签，completed 显示蓝色"已完成"标签
