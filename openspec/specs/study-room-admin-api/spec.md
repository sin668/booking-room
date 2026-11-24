## Purpose

自习室管理后台 API 提供自习室的创建、查询、更新与状态管理接口，支撑 br-admin 的学习室运营管理流程。
## Requirements
### Requirement: Create study room admin API
系统 SHALL 提供 `POST /api/v1/admin/rooms/` 接口，允许管理员创建自习室。请求体包含 `name`（字符串，必填）、`description`（字符串，可选）、`cover_image`（字符串 URL，可选）、`address`（字符串，必填）、`business_hours`（字符串，可选）、`min_price`（数字，可选，默认 0），以及可选字段 `latitude`（-90~90）、`longitude`（-180~180），坐标采用 GCJ-02。当未提供坐标且 `address` 非空时，系统 SHALL 尝试调用腾讯位置服务地理编码补全坐标；编码失败、未配置 key 或超时 MUST NOT 阻塞创建。创建成功返回 HTTP 201。

#### Scenario: Successful room creation
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/`，body 为 `{"name": "安静自习室", "address": "北京市海淀区", "business_hours": "08:00-22:00", "min_price": 15.00}`
- **THEN** 返回 HTTP 201，响应包含完整的自习室信息，`id` 自增，`status` 默认为 "open"，`created_at` 和 `updated_at` 自动填充

#### Scenario: Room creation with coordinates
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/`，body 同时包含 `latitude: 39.9042`、`longitude: 116.4074`
- **THEN** 返回 HTTP 201，响应中的 `latitude` 和 `longitude` 与请求一致，且不再调用地理编码

#### Scenario: Room creation with geocode fallback
- **GIVEN** 已配置腾讯地图 key
- **WHEN** 管理员创建房间且未提供坐标，`address` 为可解析地址
- **THEN** 系统调用地理编码并将解析出的 GCJ-02 坐标写入响应，房间创建成功

#### Scenario: Geocode fallback failure does not block creation
- **GIVEN** 腾讯地图 key 未配置或地理编码返回异常
- **WHEN** 管理员创建房间且未提供坐标
- **THEN** 返回 HTTP 201，`latitude` 和 `longitude` 为 null，其他字段正常写入

#### Scenario: Room creation with missing required fields
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/`，body 缺少 `name` 或 `address`
- **THEN** 返回 HTTP 422，错误信息指明缺少必填字段

#### Scenario: Invalid coordinate range
- **WHEN** 管理员发送 `POST /api/v1/admin/rooms/`，`latitude` 为 100 或 `longitude` 为 200
- **THEN** 返回 HTTP 422，错误信息指明坐标超出范围

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
系统 SHALL 提供 `GET /api/v1/admin/rooms/{room_id}/` 接口，返回自习室完整详情，包括座位统计信息与 GCJ-02 坐标 `latitude`、`longitude`（可为 null）。

#### Scenario: Successful detail request
- **WHEN** 管理员发送 `GET /api/v1/admin/rooms/1/`
- **THEN** 返回 HTTP 200，响应包含自习室完整字段、`latitude`、`longitude` 及 `seat_count`（总座位数）和 `available_seat_count`（可用座位数）

#### Scenario: Room not found
- **WHEN** 管理员发送 `GET /api/v1/admin/rooms/999/`
- **THEN** 返回 HTTP 404

### Requirement: Update study room admin API
系统 SHALL 提供 `PUT /api/v1/admin/rooms/{room_id}/` 接口，允许管理员更新自习室信息。所有字段均为可选，仅更新传入的字段；`latitude`、`longitude` 可传入显式值以更新坐标，也可显式传 null 清除。当更新请求包含 `address` 且未提供坐标时，系统 SHALL 尝试地理编码补全；编码失败 MUST NOT 阻塞更新。

#### Scenario: Successful update
- **WHEN** 管理员发送 `PUT /api/v1/admin/rooms/1/`，body 为 `{"name": "安静自习室(升级版)", "min_price": 20.00}`
- **THEN** 返回 HTTP 200，响应包含更新后的自习室信息，`updated_at` 自动刷新

#### Scenario: Update coordinates
- **WHEN** 管理员发送 `PUT /api/v1/admin/rooms/1/`，body 包含 `latitude: 31.2304`、`longitude: 121.4737`
- **THEN** 返回 HTTP 200，响应中的坐标更新为新值，未传字段保持不变

#### Scenario: Update address with geocode fallback
- **GIVEN** 已配置腾讯地图 key
- **WHEN** 管理员更新 `address` 且未提供坐标
- **THEN** 系统尝试地理编码并写回坐标；失败时地址仍更新成功，坐标保持原值

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

