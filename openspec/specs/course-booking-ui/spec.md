# course-booking-ui Specification

## Purpose
提供课程预约前端页面，用户可在培训课程详情页进入预约流程，选择预约类型和课时，享受全套课时优惠，选择优惠券和支付方式后完成下单。UI 严格参考 `prototype/course-booking.html` 高保真原型图。
## Requirements
### Requirement: Course booking page entry
系统 SHALL 在培训课程详情页（`pages/training/course-detail.vue`）提供"立即预约"入口，点击后跳转到课程预约页面（`pages/training/course-booking.vue`），传递 `course_id` 参数。

#### Scenario: Navigate to course booking page
- **WHEN** 用户在课程详情页点击"立即预约"按钮
- **THEN** 跳转到 `/pages/training/course-booking?course_id={id}`

### Requirement: Course info summary display
页面顶部 SHALL 展示课程摘要信息，包含课程封面图、课程名称、教师名称与头像、单价。UI 参照原型图 Course Info Summary 区域。

#### Scenario: Display course summary
- **GIVEN** 用户进入课程预约页面
- **WHEN** 页面加载完成
- **THEN** 顶部显示课程封面图（圆角方形）、课程名称、教师头像与姓名
- **AND** 右侧显示单价（如 ¥80/课时）

### Requirement: Booking type selection
页面 SHALL 提供两种预约类型选择：固定班课和 1V1 私人定制。以双列卡片形式展示，选中态显示蓝色边框和勾选图标。UI 参照原型图 Booking Type Selection 区域。

#### Scenario: Default booking type is fixed
- **WHEN** 页面加载完成
- **THEN** "固定班课"卡片显示选中态（蓝色边框 + 勾选图标）
- **AND** 显示固定班课时间表（如"每周二 14:00-16:00"）和单价

#### Scenario: Switch to custom 1V1
- **WHEN** 用户点击"1V1私人定制"卡片
- **THEN** "1V1私人定制"显示选中态，"固定班课"取消选中
- **AND** 单价更新为 1V1 价格（如 ¥200/课时）
- **AND** 上课时间区域切换为日期+时段选择器

#### Scenario: Switch back to fixed
- **WHEN** 用户从 1V1 切换回固定班课
- **THEN** 固定班课卡片恢复选中态
- **AND** 单价恢复为固定班课价格
- **AND** 上课时间区域显示固定时间表

### Requirement: Lesson multi-select
页面 SHALL 展示课程课时列表，每节课时显示序号、标题、时长、可预约状态和单价。用户可通过点击切换选中/取消，支持多选。UI 参照原型图 Lesson Selection 区域。

#### Scenario: Display lesson list
- **WHEN** 页面加载完成
- **THEN** 显示课时列表，每节包含 checkbox、图标、标题（如"第1讲 · 马克思主义基本原理"）、时长和单价
- **AND** 头部显示"已选 N 节"计数

#### Scenario: Toggle lesson selection
- **WHEN** 用户点击一节未选中的课时
- **THEN** 该课时显示选中态（蓝色背景 + checkbox 勾选）
- **AND** "已选"计数 +1
- **AND** 底部价格实时更新

#### Scenario: Deselect a lesson
- **WHEN** 用户点击一节已选中的课时
- **THEN** 该课时取消选中态
- **AND** "已选"计数 -1
- **AND** 底部价格实时更新

### Requirement: Full package expand and discount
页面 SHALL 在课时列表底部展示"全套课时更划算"推广条。点击后展开全部课时并自动全选，显示全套优惠价格。UI 参照原型图 Full course promo 区域。

#### Scenario: Show full package promo bar
- **GIVEN** 课程有多节课时可选
- **WHEN** 课时列表渲染完成
- **THEN** 列表底部显示推广条，包含"全套N课时更划算"和"立省¥XX"以及"查看全套 →"文字链

#### Scenario: Expand all lessons with full package price
- **WHEN** 用户点击"查看全套 →"
- **THEN** 展开全部课时（如果之前只显示部分）
- **AND** 所有课时自动全选
- **AND** 显示 toast 提示"已选择全套N课时，立省¥XX"
- **AND** 价格区域显示全套优惠价格

### Requirement: Schedule display
页面 SHALL 根据预约类型显示对应的上课时间信息。固定班课显示固定时间表，1V1 显示日期+时段选择器。UI 参照原型图 Schedule 区域。

#### Scenario: Display fixed schedule
- **GIVEN** 用户选择固定班课
- **THEN** 显示固定时间表区域（如"每周二 14:00-16:00"）
- **AND** 显示下次上课时间标签

#### Scenario: Display custom schedule picker
- **GIVEN** 用户选择 1V1 私人定制
- **THEN** 显示横向日期选择器（今天/明天/周几）
- **AND** 显示时段网格（如 09:00-11:00、14:00-16:00 等）
- **AND** 已满时段显示为不可选（灰色+删除线）

### Requirement: Coupon selection
页面 SHALL 提供优惠券选择入口，展示已选优惠券的抵扣金额。UI 参照原型图 Coupon Row 区域。

#### Scenario: Select coupon
- **WHEN** 用户点击优惠券行
- **THEN** 弹出优惠券选择弹窗
- **AND** 展示当前可用优惠券列表

#### Scenario: Display selected coupon discount
- **GIVEN** 用户已选择一张优惠券
- **THEN** 优惠券行显示抵扣金额（如"-¥5.00"，红色文字）

### Requirement: Payment method selection
页面 SHALL 提供支付方式选择，支持账户余额和微信支付。UI 参照原型图 Payment Method 区域。

#### Scenario: Display payment methods
- **WHEN** 页面加载完成
- **THEN** 显示"账户余额"选项（含当前余额金额）和"微信支付"选项
- **AND** 默认选中"账户余额"

### Requirement: Price summary and checkout
页面底部 SHALL 固定显示价格摘要和操作栏。价格摘要展示课程费明细、优惠券抵扣和实付金额。操作栏显示合计金额和"立即支付"按钮。UI 参照原型图 Price Summary 和 Bottom Action 区域。

#### Scenario: Display price breakdown
- **GIVEN** 用户选择了 N 节课时和优惠券
- **THEN** 价格摘要显示"课程费（N课时 × ¥XX）"小计
- **AND** 显示优惠券抵扣金额
- **AND** 显示实付金额（小计 - 优惠券）

#### Scenario: Submit course booking
- **WHEN** 用户点击"立即支付"
- **THEN** 按钮显示加载状态"支付中..."
- **AND** 根据支付方式执行余额扣款或微信支付
- **AND** 支付成功后显示预约成功弹窗
- **AND** 弹窗包含课程名称、教师、课时数、上课时间和支付金额

#### Scenario: Payment success completion
- **WHEN** 用户在成功弹窗点击"完成"
- **THEN** 关闭弹窗并跳转到订单列表页

### Requirement: Course booking order display in order list
订单列表页（`pages/orders/index.vue`）SHALL 支持展示课程预约订单，与自习室预约订单共存。课程预约订单展示差异化的信息。

#### Scenario: Display course booking in order list
- **GIVEN** 用户有课程预约订单
- **WHEN** 用户进入订单列表页
- **THEN** 课程预约订单卡片显示课程名称（替代门店名）
- **AND** 显示课时信息（如"第1讲 · 共3课时"替代座位信息）
- **AND** 显示上课时间和价格
- **AND** 状态标签与自习室预约一致（待支付/已确认/已完成/已取消）

#### Scenario: Course booking order actions
- **GIVEN** 课程预约订单处于 `pending` 状态
- **WHEN** 订单卡片渲染操作按钮
- **THEN** 显示"去支付"和"取消"按钮，行为与自习室预约一致

#### Scenario: Mixed order list
- **GIVEN** 用户同时有自习室预约和课程预约订单
- **WHEN** 用户查看订单列表
- **THEN** 两种订单按创建时间倒序混合展示
- **AND** 各自显示差异化的信息内容

