## ADDED Requirements

### Requirement: List bookings admin API
系统 SHALL 提供 `GET /api/v1/admin/bookings/` 接口，返回所有用户的预约订单分页列表。支持查询参数 `page`（默认 1）、`page_size`（默认 10，最大 50）、`status`（可选，筛选订单状态）、`room_id`（可选，筛选自习室）、`date_start`（可选，起始日期）、`date_end`（可选，结束日期）。响应包含订单详情及关联的座位和自习室信息。

#### Scenario: Successful list request
- **WHEN** 管理员发送 `GET /api/v1/admin/bookings/`
- **THEN** 返回 HTTP 200，响应包含 `items`（订单数组）和 `total`、`page`、`page_size` 字段，每个订单包含 `seat`（座位信息）和 `room`（自习室信息），按创建时间降序排列

#### Scenario: List bookings filtered by status
- **WHEN** 管理员发送 `GET /api/v1/admin/bookings/?status=confirmed`
- **THEN** 返回 HTTP 200，`items` 中仅包含 `status` 为 "confirmed" 的订单

#### Scenario: List bookings filtered by room
- **WHEN** 管理员发送 `GET /api/v1/admin/bookings/?room_id=1`
- **THEN** 返回 HTTP 200，`items` 中仅包含 `room_id` 为 1 的订单

#### Scenario: List bookings filtered by date range
- **WHEN** 管理员发送 `GET /api/v1/admin/bookings/?date_start=2026-05-01&date_end=2026-05-07`
- **THEN** 返回 HTTP 200，`items` 中仅包含 `date` 在 2026-05-01 至 2026-05-07 范围内的订单

#### Scenario: Combined filters
- **WHEN** 管理员发送 `GET /api/v1/admin/bookings/?status=confirmed&room_id=1&date_start=2026-05-01`
- **THEN** 返回 HTTP 200，`items` 中仅包含同时满足所有筛选条件的订单

#### Scenario: Non-admin user accesses admin bookings
- **WHEN** 未提供 `X-Admin-Token` 或 token 无效时发送请求
- **THEN** 返回 HTTP 401

### Requirement: Get booking detail admin API
系统 SHALL 提供 `GET /api/v1/admin/bookings/{booking_id}/` 接口，返回订单完整详情，包含关联的座位信息和自习室信息。管理员可查看任意用户的订单。

#### Scenario: Successful detail request
- **WHEN** 管理员发送 `GET /api/v1/admin/bookings/1/`
- **THEN** 返回 HTTP 200，响应包含订单完整字段及 `seat`（座位编号、区域、价格）和 `room`（自习室名称、地址）信息

#### Scenario: Booking not found
- **WHEN** 管理员发送 `GET /api/v1/admin/bookings/999/`
- **THEN** 返回 HTTP 404

### Requirement: Cancel booking admin API
系统 SHALL 提供 `POST /api/v1/admin/bookings/{booking_id}/cancel/` 接口，允许管理员取消任意用户的订单。仅 `confirmed` 状态的订单可被取消。

#### Scenario: Successful cancellation
- **WHEN** 管理员发送 `POST /api/v1/admin/bookings/1/cancel/`，该订单状态为 "confirmed"
- **THEN** 返回 HTTP 200，订单状态变为 "cancelled"，`updated_at` 自动刷新

#### Scenario: Cancel already cancelled booking
- **WHEN** 管理员发送 `POST /api/v1/admin/bookings/1/cancel/`，该订单状态已为 "cancelled"
- **THEN** 返回 HTTP 400，错误信息为"该订单已取消"

#### Scenario: Cancel non-existent booking
- **WHEN** 管理员发送 `POST /api/v1/admin/bookings/999/cancel/`
- **THEN** 返回 HTTP 404
