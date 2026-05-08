## ADDED Requirements

### Requirement: List study rooms API
系统 SHALL 提供 `GET /api/v1/rooms/` 接口，返回自习室分页列表。支持查询参数 `page`（默认 1）和 `page_size`（默认 10，最大 50）。仅返回 `status=open` 的自习室。

#### Scenario: Successful list request with default pagination
- **WHEN** 客户端发送 `GET /api/v1/rooms/` 不带查询参数
- **THEN** 返回 HTTP 200，响应包含 `items`（自习室数组）和 `total`、`page`、`page_size` 字段，`page_size` 默认为 10

#### Scenario: List request with custom page size
- **WHEN** 客户端发送 `GET /api/v1/rooms/?page=2&page_size=5`
- **THEN** 返回 HTTP 200，`page` 为 2，`page_size` 为 5，`items` 包含第 2 页的 5 条记录

#### Scenario: Page size exceeds maximum
- **WHEN** 客户端发送 `GET /api/v1/rooms/?page_size=100`
- **THEN** 返回 HTTP 200，`page_size` 被限制为最大值 50

### Requirement: Study room response schema
自习室列表响应中每个 item SHALL 包含以下字段：`id`（整数）、`name`（字符串）、`description`（字符串，可空）、`cover_image`（字符串 URL）、`address`（字符串）、`business_hours`（字符串，如 "08:00-22:00"）、`status`（枚举 "open"/"closed"）、`min_price`（数字，单位元）。

#### Scenario: Response field validation
- **WHEN** 客户端请求自习室列表
- **THEN** 每个 item 包含 `id`、`name`、`description`、`cover_image`、`address`、`business_hours`、`status`、`min_price` 字段，类型符合规范

### Requirement: Study room database model
系统 SHALL 创建 `study_rooms` 表，包含字段：`id`（主键，自增）、`name`（VARCHAR，非空）、`description`（TEXT，可空）、`cover_image`（VARCHAR，可空）、`address`（VARCHAR，非空）、`business_hours`（VARCHAR，可空）、`status`（VARCHAR，默认 "open"，枚举值 "open"/"closed"）、`min_price`（DECIMAL(10,2)，默认 0）、`created_at`、`updated_at`。

#### Scenario: Create study room record
- **WHEN** 向 `study_rooms` 表插入一条记录，`name="安静自习室"`，`address="北京市海淀区"`，`min_price=15.00`
- **THEN** 记录成功创建，`id` 自增，`status` 默认为 "open"，`created_at` 和 `updated_at` 自动填充
