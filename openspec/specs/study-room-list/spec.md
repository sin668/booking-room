## ADDED Requirements

### Requirement: List study rooms API
系统 SHALL 提供 `GET /api/v1/rooms/` 接口，返回自习室分页列表。支持查询参数 `page`（默认 1）、`page_size`（默认 10，最大 50）、`city_id`（可选，整数，按城市过滤）。仅返回 `status=open` 的自习室。当 `city_id` 为空时返回全部城市的自习室。

#### Scenario: Successful list request with default pagination
- **WHEN** 客户端发送 `GET /api/v1/rooms/` 不带查询参数
- **THEN** 返回 HTTP 200，响应包含 `items`（自习室数组）和 `total`、`page`、`page_size` 字段，`page_size` 默认为 10，返回全部城市的自习室

#### Scenario: List request with custom page size
- **WHEN** 客户端发送 `GET /api/v1/rooms/?page=2&page_size=5`
- **THEN** 返回 HTTP 200，`page` 为 2，`page_size` 为 5，`items` 包含第 2 页的 5 条记录

#### Scenario: Page size exceeds maximum
- **WHEN** 客户端发送 `GET /api/v1/rooms/?page_size=100`
- **THEN** 返回 HTTP 200，`page_size` 被限制为最大值 50

#### Scenario: Filter rooms by city
- **WHEN** 客户端发送 `GET /api/v1/rooms/?city_id=1`
- **THEN** 返回 HTTP 200，`items` 仅包含 `city_id=1` 的自习室

#### Scenario: Filter by non-existent city
- **WHEN** 客户端发送 `GET /api/v1/rooms/?city_id=999`（不存在或 inactive 的城市）
- **THEN** 返回 HTTP 200，`items` 为空数组，`total` 为 0

### Requirement: Study room response schema
自习室列表响应中每个 item SHALL 包含以下字段：`id`（整数）、`name`（字符串）、`description`（字符串，可空）、`cover_image`（字符串 URL）、`address`（字符串）、`business_hours`（字符串，如 "08:00-22:00"）、`status`（枚举 "open"/"closed"）、`min_price`（数字，单位元）、`city_id`（整数或 null）、`city_name`（字符串或 null，城市名称）。

#### Scenario: Response field validation
- **WHEN** 客户端请求自习室列表
- **THEN** 每个 item 包含 `id`、`name`、`description`、`cover_image`、`address`、`business_hours`、`status`、`min_price`、`city_id`、`city_name` 字段，类型符合规范

#### Scenario: Room without city
- **WHEN** 客户端请求包含 `city_id=null` 的自习室
- **THEN** 该 item 的 `city_id` 为 null，`city_name` 为 null

### Requirement: Study room database model
系统 SHALL 创建 `study_rooms` 表，包含字段：`id`（主键，自增）、`name`（VARCHAR，非空）、`description`（TEXT，可空）、`cover_image`（VARCHAR，可空）、`address`（VARCHAR，非空）、`city_id`（INTEGER，可空，外键关联 cities.id）、`business_hours`（VARCHAR，可空）、`status`（VARCHAR，默认 "open"，枚举值 "open"/"closed"）、`min_price`（DECIMAL(10,2)，默认 0）、`created_at`、`updated_at`。

#### Scenario: Create study room record
- **WHEN** 向 `study_rooms` 表插入一条记录，`name="安静自习室"`，`address="北京市海淀区"`，`min_price=15.00`
- **THEN** 记录成功创建，`id` 自增，`status` 默认为 "open"，`created_at` 和 `updated_at` 自动填充

### Requirement: Homepage study room list
首页（`pages/index/index.vue`）自习室列表 SHALL 按当前选中城市过滤。页面顶部 SHALL 显示城市选择器（与预约页一致），点击可跳转城市选择页。切换城市后列表自动刷新。

#### Scenario: Display homepage with city filter
- **WHEN** 用户进入首页
- **THEN** 首页顶部显示当前城市名，自习室列表按当前城市过滤

#### Scenario: Switch city from homepage
- **WHEN** 用户在首页点击城市名并选择新城市
- **THEN** 返回首页后城市名更新，自习室列表按新城市刷新

#### Scenario: Homepage without city selection
- **WHEN** 用户首次使用，无本地存储的城市偏好
- **THEN** 首页使用默认城市（服务端 sort_order 最小的 active 城市），自习室列表按默认城市过滤

### Requirement: Store detail page
系统 SHALL 提供门店详情页（`pages/booking/detail.vue`）。页面包含：顶部封面大图、门店名称和营业状态标签、评分、地址（含距离）、营业时间、区域标签、环境照片横向滚动列表、座位概况统计卡片（总座位/可用/已占/维护中）、底部固定栏（收藏按钮 + "立即预约"按钮）。地址前 SHALL 显示城市名称（当 `city_name` 不为空时）。

#### Scenario: Display store detail with city
- **WHEN** 用户进入详情页，自习室关联了城市
- **THEN** 地址显示为"茂名市 茂南区油城三路88号"格式（城市名 + 地址）

#### Scenario: Display store detail without city
- **WHEN** 用户进入详情页，自习室未关联城市（`city_name` 为 null）
- **THEN** 地址仅显示原始 address 字段内容，不添加城市名前缀
