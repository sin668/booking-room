## MODIFIED Requirements

### Requirement: List study rooms API
系统 SHALL 提供 `GET /api/v1/rooms` 接口，返回自习室分页列表。支持查询参数 `page`（默认 1）、`page_size`（默认 10，最大 50）、`city_id`（可选，整数，按城市过滤）、`room_type`（可选，枚举值 "study"/"training"/"comprehensive"，按房间类型过滤）。仅返回 `status=open` 的房间。当 `city_id` 为空时返回全部城市的房间。当 `room_type` 为空时返回全部类型的房间。响应中每个 item SHALL 包含 `room_type` 字段。

#### Scenario: Successful list request with default pagination
- **WHEN** 客户端发送 `GET /api/v1/rooms` 不带查询参数
- **THEN** 返回 HTTP 200，响应包含 `items`（房间数组）和 `total`、`page`、`page_size` 字段，`page_size` 默认为 10，返回全部类型的房间

#### Scenario: List request with custom page size
- **WHEN** 客户端发送 `GET /api/v1/rooms?page=2&page_size=5`
- **THEN** 返回 HTTP 200，`page` 为 2，`page_size` 为 5，`items` 包含第 2 页的 5 条记录

#### Scenario: Page size exceeds maximum
- **WHEN** 客户端发送 `GET /api/v1/rooms?page_size=100`
- **THEN** 返回 HTTP 200，`page_size` 被限制为最大值 50

#### Scenario: Filter rooms by city
- **WHEN** 客户端发送 `GET /api/v1/rooms?city_id=1`
- **THEN** 返回 HTTP 200，`items` 仅包含 `city_id=1` 的房间

#### Scenario: Filter by non-existent city
- **WHEN** 客户端发送 `GET /api/v1/rooms?city_id=999`（不存在或 inactive 的城市）
- **THEN** 返回 HTTP 200，`items` 为空数组，`total` 为 0

#### Scenario: Filter rooms by room_type
- **WHEN** 客户端发送 `GET /api/v1/rooms?room_type=study`
- **THEN** 返回 HTTP 200，`items` 仅包含 `room_type=study` 的自习室

#### Scenario: Filter rooms by training type
- **WHEN** 客户端发送 `GET /api/v1/rooms?room_type=training`
- **THEN** 返回 HTTP 200，`items` 仅包含 `room_type=training` 的培训室

#### Scenario: Response includes room_type field
- **GIVEN** 房间列表有数据
- **WHEN** 客户端发送 `GET /api/v1/rooms`
- **THEN** 每个 item 包含 `room_type` 字段，值为 "study"、"training" 或 "comprehensive"

### Requirement: Study room response schema
自习室列表响应中每个 item SHALL 包含以下字段：`id`（整数）、`name`（字符串）、`description`（字符串，可空）、`cover_image`（字符串 URL）、`address`（字符串）、`business_hours`（字符串，如 "08:00-22:00"）、`status`（枚举 "open"/"closed"）、`room_type`（枚举 "study"/"training"/"comprehensive"）、`min_price`（数字，单位元）、`city_id`（整数或 null）、`city_name`（字符串或 null，城市名称）。

#### Scenario: Response field validation
- **WHEN** 客户端请求自习室列表
- **THEN** 每个 item 包含 `id`、`name`、`description`、`cover_image`、`address`、`business_hours`、`status`、`room_type`、`min_price`、`city_id`、`city_name` 字段，类型符合规范

#### Scenario: Room without city
- **WHEN** 客户端请求包含 `city_id=null` 的自习室
- **THEN** 该 item 的 `city_id` 为 null，`city_name` 为 null

#### Scenario: Room type field values
- **GIVEN** 存在 room_type 分别为 study、training、comprehensive 的房间
- **WHEN** 客户端请求房间列表
- **THEN** 每个 item 的 `room_type` 字段为 "study"、"training" 或 "comprehensive" 之一
