## Requirements

### Requirement: Booking tab page
系统 SHALL 将 br-app"预约"tab 页改造为预约主页面，参照 `prototype/booking.html`。页面包含：顶部城市选择器（显示当前城市名，点击跳转城市选择页）、日期选择器（横向滚动，显示近 7 天）、时段选择网格（2 小时一档，可选/已满/已选三种状态）、区域筛选标签（全部/静音区/键盘区/VIP区）、座位平面图（按 row/col 布局，可选/已占/已选/VIP 四种样式）、底部座位信息栏（座位号、区域、位置、时段、费用）及"立即预约"按钮。城市选择器 SHALL 动态显示 store 中的当前城市名，不再硬编码。点击"立即预约"跳转到确认页。

#### Scenario: Display booking tab with dynamic city
- **WHEN** 用户点击底部"预约" tab
- **THEN** 页面顶部城市选择器显示当前城市名（从 store 读取），点击可跳转城市选择页

#### Scenario: Navigate to city selection
- **WHEN** 用户点击顶部城市选择器
- **THEN** 跳转到城市选择页 `pages/city-select/index`

#### Scenario: City updated after selection
- **GIVEN** 用户在城市选择页选择了新城市
- **WHEN** 返回预约页
- **THEN** 顶部城市名更新为所选城市，自习室列表按新城市过滤刷新

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
系统 SHALL 提供门店详情页（`pages/booking/detail.vue`），参照 `prototype/store-detail.html` 和 `prototype/training-room.html` 高保真原型图。页面 SHALL 根据 `room_type` 条件渲染不同内容：

**自习室（study）**：页面包含顶部封面大图、门店名称和营业状态标签、评分、地址（含距离）、营业时间、区域标签（静音区/键盘区/VIP区/WiFi/充电插座）、环境照片横向滚动列表、座位概况统计卡片（总座位/可用/已占/维护中）、底部固定栏（心状关注按钮 + "立即预约"按钮）。点击"立即预约"跳转到座位选择页。

**培训室（training）**：页面包含顶部封面大图、培训室名称和营业状态标签、评分、地址、营业时间、设施标签（多媒体教室/小班授课/一对一辅导/WiFi/空调开放）、培训室简介、环境照片横向滚动列表、教学设施网格（白板/投影仪/空调/隔音墙/WiFi/充电口）、教室概况统计卡片（培训教室数/小班容量/认证讲师/累计学员）、名师团队横向滚动卡片（教师头像、姓名、头衔、评分）、本培训室课程纵向列表（封面图、课程名、状态标签、教师信息、排课时间、价格、预约按钮）、底部固定栏（心状关注按钮 + "返回课程"按钮）。点击"返回课程"跳转到培训课程列表页。

**综合室（comprehensive）**：页面包含顶部封面大图、综合室名称和营业状态标签、评分、地址、营业时间、区域标签、环境照片横向滚动列表、座位概况统计卡片（总座位/可用/已占/维护中）、教室概况统计卡片（培训教室数/小班容量/认证讲师/累计学员）、名师团队横向滚动卡片、本培训室课程纵向列表、底部固定栏（心状关注按钮 + "预约自习室"按钮）。点击"预约自习室"跳转到座位选择页。

页面 SHALL 通过 `GET /api/v1/rooms/{room_id}` 获取房间基本信息（含 `room_type` 字段），当 `room_type` 为 `training` 或 `comprehensive` 时 SHALL 额外调用 `GET /api/v1/training/rooms/{room_id}` 获取教师和课程数据。当 `room_type` 为 `study` 或 `comprehensive` 时 SHALL 调用 `GET /api/v1/rooms/{room_id}/seats/stats` 获取座位统计数据。

#### Scenario: Display study room detail
- **GIVEN** 用户进入详情页，`room_id=1`，该房间 `room_type=study`
- **WHEN** 页面加载完成
- **THEN** 页面展示封面图、名称、营业状态、评分、地址、营业时间、区域标签、环境照片、座位概况统计卡片
- **AND** 底部固定栏显示心状关注按钮和"立即预约"按钮

#### Scenario: Study room navigate to seat select
- **WHEN** 用户在自习室详情页点击"立即预约"按钮
- **THEN** 跳转到座位选择页，传递 `room_id` 参数

#### Scenario: Display training room detail
- **GIVEN** 用户进入详情页，`room_id=4`，该房间 `room_type=training`
- **WHEN** 页面加载完成
- **THEN** 页面展示封面图、培训室名称、营业状态、评分、地址、营业时间、设施标签、培训室简介、环境照片、教学设施网格、教室概况统计卡片、名师团队横向滚动卡片、本培训室课程纵向列表
- **AND** 不显示座位概况统计卡片
- **AND** 底部固定栏显示心状关注按钮和"返回课程"按钮

#### Scenario: Training room navigate to course list
- **WHEN** 用户在培训室详情页点击"返回课程"按钮
- **THEN** 跳转到培训课程列表页（`pages/training/index`）

#### Scenario: Display comprehensive room detail
- **GIVEN** 用户进入详情页，`room_id=7`，该房间 `room_type=comprehensive`
- **WHEN** 页面加载完成
- **THEN** 页面展示封面图、综合室名称、营业状态、评分、地址、营业时间、区域标签、环境照片、座位概况统计卡片、教室概况统计卡片、名师团队横向滚动卡片、本培训室课程纵向列表
- **AND** 底部固定栏显示心状关注按钮和"预约自习室"按钮

#### Scenario: Comprehensive room navigate to seat select
- **WHEN** 用户在综合室详情页点击"预约自习室"按钮
- **THEN** 跳转到座位选择页，传递 `room_id` 参数

#### Scenario: Training room teachers display
- **GIVEN** 培训室有 3 位关联教师
- **WHEN** 培训室详情页加载完成
- **THEN** 名师团队区域横向滚动展示 3 张教师卡片，每张卡片包含头像、姓名、头衔和评分

#### Scenario: Training room courses display
- **GIVEN** 培训室有 5 门 `status=active` 的课程
- **WHEN** 培训室详情页加载完成
- **THEN** 本培训室课程区域纵向展示 5 张课程卡片，每张卡片包含封面图、课程名、状态标签、教师信息、排课时间、价格和预约入口

#### Scenario: Training room with no courses
- **GIVEN** 培训室没有关联任何课程
- **WHEN** 培训室详情页加载完成
- **THEN** 名师团队区域和本培训室课程区域显示空状态提示"暂无课程"

#### Scenario: Room not found
- **WHEN** 用户进入详情页，`room_id` 对应的房间不存在
- **THEN** 显示错误提示并返回上一页

#### Scenario: Follow room toggle
- **GIVEN** 用户在任意类型房间详情页
- **WHEN** 用户点击心状关注按钮
- **THEN** 切换关注状态，关注时显示红色心形图标，取消关注时显示灰色心形描边

#### Scenario: Conditional API calls based on room type
- **GIVEN** 用户进入详情页，`room_id` 对应的房间 `room_type=training`
- **WHEN** 页面加载数据
- **THEN** 调用 `GET /api/v1/rooms/{room_id}` 获取房间基本信息
- **AND** 调用 `GET /api/v1/training/rooms/{room_id}` 获取教师和课程数据
- **AND** 不调用 `GET /api/v1/rooms/{room_id}/seats/stats`

### Requirement: Seat select page
系统 SHALL 提供座位选择页（`pages/booking/seat-select.vue`），参照 `prototype/seat-select.html`。页面包含：区域 tab 切换（全部/静音区/键盘区/VIP区，显示对应单价）、楼层选择器、座位平面图（分区域展示，含桌面/过道元素、靠窗标记）、图例说明（可选/已选/已占/VIP）、底部已选座位信息栏（座位号、区域、位置、时段、费用）及"确认选座"按钮。页面 SHALL 支持通过 URL 参数 `mode=view` 进入只读查看模式，在该模式下隐藏日期选择器、时段选择器和底部确认栏，预定座位显示小人图标高亮，所有座位不可点击。

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

#### Scenario: Enter view mode from order list
- **WHEN** 用户从订单列表点击"查看座位"，URL 包含 `mode=view&room_id=X&seat_id=Y&date=D&start_time=S&end_time=E`
- **THEN** 页面以只读模式加载，自动设置日期和时段为订单参数，预定座位（seat_id 匹配）显示小人图标高亮，其余座位正常显示已占/可选状态

#### Scenario: View mode hides interactive elements
- **GIVEN** 页面处于 `mode=view` 查看模式
- **WHEN** 页面渲染完成
- **THEN** 隐藏日期选择器、时段选择器和底部确认栏，区域 tab 切换保持可用

#### Scenario: View mode disables seat interaction
- **GIVEN** 页面处于 `mode=view` 查看模式
- **WHEN** 用户点击任意座位
- **THEN** 无任何响应，座位不进入选中状态

#### Scenario: View mode highlights booked seat with person icon
- **GIVEN** 页面处于 `mode=view` 查看模式且 seat_id=Y
- **WHEN** 座位 Y 渲染完成
- **THEN** 座位 Y 上方显示小人图标（🧑），座位背景色为高亮样式，与可选/已占样式明显区分

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

### Requirement: My bookings list page
系统 SHALL 将 br-app"订单"tab 页改造为我的预约列表页，参照 `prototype/orders.html`。每条记录展示门店名称、座位号、预约日期、时间段、状态标签（不同状态不同颜色）。支持按状态筛选（全部/已确认/已取消/已完成）。已确认状态的订单 SHALL 显示"查看座位"按钮，点击后跳转到座位选择页的只读查看模式。对于 `can_cancel=true` 的已确认订单，页面 SHALL 在“查看座位”按钮右侧展示“取消”按钮。

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

#### Scenario: View seat from confirmed order
- **GIVEN** 订单列表中存在 status 为 "confirmed" 的订单
- **WHEN** 用户点击"查看座位"按钮
- **THEN** 跳转到座位选择页，传递 `room_id`、`seat_id`、`date`、`start_time`、`end_time`、`mode=view` 参数

#### Scenario: View seat button hidden for non-confirmed orders
- **GIVEN** 订单列表中存在 status 为 "cancelled" 或 "completed" 的订单
- **WHEN** 订单卡片渲染
- **THEN** 不显示"查看座位"按钮

#### Scenario: Display cancel button next to view seat
- **GIVEN** 用户进入订单列表
- **AND** 列表中存在状态为 "confirmed" 且 `can_cancel=true` 的预约
- **WHEN** 订单卡片渲染
- **THEN** “查看座位”按钮右侧显示“取消”按钮

#### Scenario: Hide cancel button for non-cancellable booking
- **GIVEN** 用户进入订单列表
- **AND** 列表中存在状态为 "cancelled"、"completed" 或 `can_cancel=false` 的预约
- **WHEN** 订单卡片渲染
- **THEN** 不显示“取消”按钮

#### Scenario: Confirm before cancellation
- **GIVEN** 订单卡片显示“取消”按钮
- **WHEN** 用户点击“取消”
- **THEN** 页面展示确认弹窗
- **AND** 弹窗说明取消后剩余金额退回钱包
- **AND** 如果本次取消需要扣款，弹窗展示扣款金额提醒
- **AND** 用户可选择确认或放弃

#### Scenario: Submit cancellation after confirmation
- **GIVEN** 用户已打开取消确认弹窗
- **WHEN** 用户确认取消
- **THEN** 前端调用 `POST /api/v1/bookings/{booking_id}/cancel/`
- **AND** 取消请求进行中时禁用重复点击

#### Scenario: Cancellation success updates order list
- **GIVEN** 用户确认取消且后端返回 HTTP 200
- **WHEN** 前端收到取消结果
- **THEN** 页面提示取消成功及退款金额
- **AND** 刷新订单列表
- **AND** 对应订单状态显示为“已取消”
- **AND** 不再展示“取消”按钮

#### Scenario: Cancellation rejected because booking started
- **GIVEN** 用户确认取消
- **WHEN** 后端返回预约已开始不可取消错误
- **THEN** 页面展示不可取消提示
- **AND** 刷新订单列表
- **AND** 对应订单状态显示为“已完成”

#### Scenario: Cancellation network failure
- **GIVEN** 用户确认取消
- **WHEN** 取消请求失败或网络异常
- **THEN** 页面展示“取消失败，请重试”提示
- **AND** 订单列表保持当前状态
