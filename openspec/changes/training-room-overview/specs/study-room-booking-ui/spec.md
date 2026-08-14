## MODIFIED Requirements

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
