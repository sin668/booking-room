## ADDED Requirements

### Requirement: Create seat admin API
系统 SHALL 提供 `POST /api/v1/admin/rooms/{room_id}/seats/` 接口，允许管理员为指定自习室创建单个座位。请求体包含 `seat_number`（字符串，必填）、`zone`（枚举 "quiet"/"keyboard"/"vip"，必填）、`position`（字符串，可选）、`floor`（整数，可选，默认 3）、`price_per_hour`（数字，必填）、`row`（整数，可选）、`col`（整数，可选）。

#### Scenario: Successful seat creation
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/1/seats/`，body 为 `{"seat_number": "A-01", "zone": "quiet", "price_per_hour": 6.00, "row": 1, "col": 1}`
- **THEN** 返回 HTTP 201，响应包含座位完整信息，`status` 默认为 "available"

#### Scenario: Duplicate seat number in same room
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/1/seats/`，`seat_number` 与该房间已有座位重复
- **THEN** 返回 HTTP 409，错误信息为"该房间已存在相同编号的座位"

#### Scenario: Room not found
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/999/seats/`
- **THEN** 返回 HTTP 404

### Requirement: Bulk create seats admin API
系统 SHALL 提供 `POST /api/v1/admin/rooms/{room_id}/seats/bulk/` 接口，允许管理员批量生成座位。请求体包含 `seats`（数组，每项包含 `zone`、`rows`、`cols`、`prefix`、`price_per_hour`、`floor`、`start_number`），系统按行列自动编号生成座位。

#### Scenario: Successful bulk creation
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/1/seats/bulk/`，body 为 `{"seats": [{"zone": "quiet", "rows": 4, "cols": 5, "prefix": "A", "price_per_hour": 6.00, "floor": 3, "start_number": 1}]}`
- **THEN** 返回 HTTP 201，生成 20 个座位（A-01~A-20），按 row 和 col 排列

#### Scenario: Bulk creation with multiple zones
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/1/seats/bulk/`，body 包含多个 zone 配置
- **THEN** 返回 HTTP 201，按配置生成所有分区座位

#### Scenario: Bulk creation with number conflict
- **WHEN** 管理员发送批量创建请求，部分 seat_number 已存在
- **THEN** 返回 HTTP 409，错误信息列出冲突的 seat_number，无座位被创建（原子操作）

#### Scenario: Empty seats array
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/1/seats/bulk/`，body 中 `seats` 为空数组
- **THEN** 返回 HTTP 422，错误信息为"至少需要一个分区配置"

### Requirement: List seats admin API
系统 SHALL 提供 `GET /api/v1/admin/rooms/{room_id}/seats/` 接口，返回指定自习室的所有座位列表（包含所有状态）。支持查询参数 `zone`（可选，按分区筛选）、`status`（可选，按状态筛选）。

#### Scenario: Successful list request
- **WHEN** 管理员发送 `GET /api/v1/admin/rooms/1/seats/`
- **THEN** 返回 HTTP 200，响应为座位数组，包含所有状态（available/maintenance）的座位

#### Scenario: Filter by zone
- **WHEN** 管理员发送 `GET /api/v1/admin/rooms/1/seats/?zone=quiet`
- **THEN** 返回 HTTP 200，`items` 中仅包含 `zone` 为 "quiet" 的座位

#### Scenario: Filter by status
- **WHEN** 管理员发送 `GET /api/v1/admin/rooms/1/seats/?status=maintenance`
- **THEN** 返回 HTTP 200，`items` 中仅包含 `status` 为 "maintenance" 的座位

### Requirement: Get seat detail admin API
系统 SHALL 提供 `GET /api/v1/admin/seats/{seat_id}/` 接口，返回座位完整详情。

#### Scenario: Successful detail request
- **WHEN** 管理员发送 `GET /api/v1/admin/seats/1/`
- **THEN** 返回 HTTP 200，响应包含座位完整字段及关联的房间名称

#### Scenario: Seat not found
- **WHEN** 管理员发送 `GET /api/v1/admin/seats/999/`
- **THEN** 返回 HTTP 404

### Requirement: Update seat admin API
系统 SHALL 提供 `PUT /api/v1/admin/seats/{seat_id}/` 接口，允许管理员更新座位信息。所有字段均为可选。

#### Scenario: Successful update
- **WHEN** 管理员发送 `PUT /api/v1/admin/seats/1/`，body 为 `{"price_per_hour": 8.00, "position": "靠窗"}`
- **THEN** 返回 HTTP 200，响应包含更新后的座位信息

#### Scenario: Update seat number to duplicate
- **WHEN** 管理员发送 `PUT /api/v1/admin/seats/1/`，`seat_number` 与同房间其他座位重复
- **THEN** 返回 HTTP 409

#### Scenario: Update non-existent seat
- **WHEN** 管理员发送 `PUT /api/v1/admin/seats/999/`
- **THEN** 返回 HTTP 404

### Requirement: Delete seat admin API
系统 SHALL 提供 `DELETE /api/v1/admin/seats/{seat_id}/` 接口，允许管理员删除座位。如果该座位存在活跃预约，拒绝删除。

#### Scenario: Successful deletion
- **WHEN** 管理员发送 `DELETE /api/v1/admin/seats/1/`，该座位无活跃预约
- **THEN** 返回 HTTP 204

#### Scenario: Delete seat with active bookings
- **WHEN** 管理员发送 `DELETE /api/v1/admin/seats/1/`，该座位存在 confirmed 状态的预约
- **THEN** 返回 HTTP 409，错误信息为"该座位存在活跃预约，无法删除"

### Requirement: Toggle seat status admin API
系统 SHALL 提供 `PATCH /api/v1/admin/seats/{seat_id}/status/` 接口，允许管理员切换座位维护状态。请求体包含 `status`（枚举 "available"/"maintenance"）。

#### Scenario: Set seat to maintenance
- **WHEN** 管理员发送 `PATCH /api/v1/admin/seats/1/status/`，body 为 `{"status": "maintenance"}`
- **THEN** 返回 HTTP 200，座位 `status` 变为 "maintenance"，用户端显示该座位不可预约

#### Scenario: Restore seat to available
- **WHEN** 管理员发送 `PATCH /api/v1/admin/seats/1/status/`，body 为 `{"status": "available"}`
- **THEN** 返回 HTTP 200，座位 `status` 变为 "available"

#### Scenario: Invalid status value
- **WHEN** 管理员发送 `PATCH /api/v1/admin/seats/1/status/`，body 为 `{"status": "invalid"}`
- **THEN** 返回 HTTP 422
