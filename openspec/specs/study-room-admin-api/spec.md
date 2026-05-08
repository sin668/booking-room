## Requirements

### Requirement: Create study room admin API
系统 SHALL 提供 `POST /api/v1/admin/rooms/` 接口，允许管理员创建自习室。请求体包含 `name`（字符串，必填）、`description`（字符串，可选）、`cover_image`（字符串 URL，可选）、`address`（字符串，必填）、`business_hours`（字符串，可选）、`min_price`（数字，可选，默认 0）。创建成功返回 HTTP 201。

#### Scenario: Successful room creation
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/`，body 为 `{"name": "安静自习室", "address": "北京市海淀区", "business_hours": "08:00-22:00", "min_price": 15.00}`
- **THEN** 返回 HTTP 201，响应包含完整的自习室信息，`id` 自增，`status` 默认为 "open"，`created_at` 和 `updated_at` 自动填充

#### Scenario: Room creation with missing required fields
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/`，body 缺少 `name` 或 `address`
- **THEN** 返回 HTTP 422，错误信息指明缺少必填字段

#### Scenario: Non-admin user creates room
- **WHEN** 未提供 `X-Admin-Token` 或 token 无效时发送请求
- **THEN** 返回 HTTP 401

### Requirement: List study rooms admin API
系统 SHALL 提供 `GET /api/v1/admin/rooms/` 接口，返回所有自习室分页列表（包括 open 和 closed 状态）。支持查询参数 `page`（默认 1）、`page_size`（默认 10，最大 50）、`status`（可选，筛选状态）。

#### Scenario: Successful list request
- **WHEN** 管理员发送 `GET /api/v1/admin/rooms/`
- **THEN** 返回 HTTP 200，响应包含 `items`（自习室数组）和 `total`、`page`、`page_size` 字段，包含所有状态的自习室

#### Scenario: List rooms filtered by status
- **WHEN** 管理员发送 `GET /api/v1/admin/rooms/?status=open`
- **THEN** 返回 HTTP 200，`items` 中仅包含 `status` 为 "open" 的自习室

### Requirement: Get study room detail admin API
系统 SHALL 提供 `GET /api/v1/admin/rooms/{room_id}/` 接口，返回自习室完整详情，包括座位统计信息。

#### Scenario: Successful detail request
- **WHEN** 管理员发送 `GET /api/v1/admin/rooms/1/`
- **THEN** 返回 HTTP 200，响应包含自习室完整字段及 `seat_count`（总座位数）和 `available_seat_count`（可用座位数）

#### Scenario: Room not found
- **WHEN** 管理员发送 `GET /api/v1/admin/rooms/999/`
- **THEN** 返回 HTTP 404

### Requirement: Update study room admin API
系统 SHALL 提供 `PUT /api/v1/admin/rooms/{room_id}/` 接口，允许管理员更新自习室信息。所有字段均为可选，仅更新传入的字段。

#### Scenario: Successful update
- **WHEN** 管理员发送 `PUT /api/v1/admin/rooms/1/`，body 为 `{"name": "安静自习室(升级版)", "min_price": 20.00}`
- **THEN** 返回 HTTP 200，响应包含更新后的自习室信息，`updated_at` 自动刷新

#### Scenario: Update non-existent room
- **WHEN** 管理员发送 `PUT /api/v1/admin/rooms/999/`
- **THEN** 返回 HTTP 404

### Requirement: Delete study room admin API
系统 SHALL 提供 `DELETE /api/v1/admin/rooms/{room_id}/` 接口，允许管理员删除自习室。如果该房间存在活跃预约（confirmed 状态），拒绝删除。

#### Scenario: Successful deletion
- **WHEN** 管理员发送 `DELETE /api/v1/admin/rooms/1/`，该房间无活跃预约
- **THEN** 返回 HTTP 204，房间及其所有座位被删除

#### Scenario: Delete room with active bookings
- **WHEN** 管理员发送 `DELETE /api/v1/admin/rooms/1/`，该房间存在 confirmed 状态的预约
- **THEN** 返回 HTTP 409，错误信息为"该自习室存在活跃预约，无法删除"

#### Scenario: Delete non-existent room
- **WHEN** 管理员发送 `DELETE /api/v1/admin/rooms/999/`
- **THEN** 返回 HTTP 404

### Requirement: Toggle study room status admin API
系统 SHALL 提供 `PATCH /api/v1/admin/rooms/{room_id}/status/` 接口，允许管理员切换自习室营业状态。请求体包含 `status`（枚举 "open"/"closed"）。

#### Scenario: Close a room
- **WHEN** 管理员发送 `PATCH /api/v1/admin/rooms/1/status/`，body 为 `{"status": "closed"}`
- **THEN** 返回 HTTP 200，自习室 `status` 变为 "closed"，用户端列表不再显示该房间

#### Scenario: Reopen a room
- **WHEN** 管理员发送 `PATCH /api/v1/admin/rooms/1/status/`，body 为 `{"status": "open"}`
- **THEN** 返回 HTTP 200，自习室 `status` 变为 "open"

#### Scenario: Invalid status value
- **WHEN** 管理员发送 `PATCH /api/v1/admin/rooms/1/status/`，body 为 `{"status": "invalid"}`
- **THEN** 返回 HTTP 422
