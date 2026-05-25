## MODIFIED Requirements

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

### Requirement: My bookings list page
系统 SHALL 将 br-app"订单"tab 页改造为我的预约列表页，参照 `prototype/orders.html`。每条记录展示门店名称、座位号、预约日期、时间段、状态标签（不同状态不同颜色）。支持按状态筛选（全部/已确认/已取消/已完成）。已确认状态的订单 SHALL 显示"查看座位"按钮，点击后跳转到座位选择页的只读查看模式。

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
