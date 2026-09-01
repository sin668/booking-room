# booking-admin-api Specification

## Purpose

定义管理端预约订单管理的 HTTP 接口（列表查询、订单详情、取消、确认），包括请求参数、响应结构、状态流转与权限验证。
## Requirements
### Requirement: List bookings admin API
系统 SHALL 提供 `GET /api/v1/admin/bookings/` 接口，返回所有用户的预约订单分页列表。支持查询参数 `page`（默认 1）、`page_size`（默认 10，最大 50）、`status`（可选，筛选订单状态）、`room_id`（可选，筛选自习室）、`date_start`（可选，起始日期）、`date_end`（可选，结束日期）。响应包含订单详情及关联的座位和自习室信息，并包含 `booking_type`（预约类型：seat/course）、`schedule_type`（fixed/custom）与 `time_slots`（课程订单上课时间段 JSON）字段。

#### Scenario: Successful list request
- **WHEN** 管理员发送 `GET /api/v1/admin/bookings/`
- **THEN** 返回 HTTP 200，响应包含 `items`（订单数组）和 `total`、`page`、`page_size` 字段，每个订单包含 `seat`（座位信息）、`room`（自习室信息）、`booking_type`、`schedule_type`、`time_slots` 字段，按创建时间降序排列

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
系统 SHALL 提供 `GET /api/v1/admin/bookings/{booking_id}` 接口，返回订单完整详情。管理员可查看任意用户的订单。响应除订单字段外，还包含关联表信息：`user`（用户昵称/手机号/头像）、`course`（课程名称/分类，仅课程订单）、`teacher`（授课老师）、`schedule`（排课记录）、`lesson_schedules`（课时安排列表）、`coupon`（优惠券）、`refund_transaction`（退款流水）。

#### Scenario: Successful detail request
- **WHEN** 管理员发送 `GET /api/v1/admin/bookings/1`
- **THEN** 返回 HTTP 200，响应包含订单完整字段及 `seat`、`room`、`user` 信息；课程订单还包含 `course`、`teacher`、`schedule`、`lesson_schedules` 信息

#### Scenario: Detail of cancelled booking with refund
- **WHEN** 管理员发送已取消且已退款订单的详情请求
- **THEN** 响应包含 `refund_transaction`（退款金额、退款后余额、退款时间）

#### Scenario: Booking not found
- **WHEN** 管理员发送 `GET /api/v1/admin/bookings/999`
- **THEN** 返回 HTTP 404

### Requirement: Cancel booking admin API
系统 SHALL 提供 `POST /api/v1/admin/bookings/{booking_id}/cancel` 接口，允许管理员取消任意用户的订单。`confirmed` 状态订单按通用取消策略取消；`pending_confirm` 已支付订单全额退款取消；课程预约（`booking_type='course'`）且状态为 `pending`/`pending_confirm` 的订单，已支付时全额退款、恢复优惠券、写退款流水，并仅删除该订单专属的 `schedule_type='custom'`（定制）的 `course_schedules` 与对应 `lesson_schedules` 记录；`schedule_type='fixed'`（固定班课）排课为课程共享资源，即使无其他订单引用也一律保留；排课仍被其他非取消订单共享时同样保留。

#### Scenario: Successful cancellation
- **WHEN** 管理员发送 `POST /api/v1/admin/bookings/1/cancel`，该订单状态为 "confirmed"
- **THEN** 返回 HTTP 200，订单状态变为 "cancelled"，`updated_at` 自动刷新

#### Scenario: Cancel pending course booking with full refund and schedule cleanup
- **WHEN** 管理员取消 `booking_type='course'`、状态为 "pending"、已支付且关联订单专属排课的订单
- **THEN** 返回 HTTP 200，订单状态变为 "cancelled"，`refund_amount` 等于 `total_price`，`penalty_amount` 为 0，用户余额增加相应金额，钱包新增 `booking_refund` 流水，对应 `course_schedules` 与 `lesson_schedules` 记录被删除

#### Scenario: Cancel pending course booking with shared schedule
- **WHEN** 管理员取消的课程订单关联的排课仍被其他非取消订单引用
- **THEN** 订单状态变为 "cancelled" 并全额退款，但排课与课时记录保留

#### Scenario: Cancel pending fixed course booking keeps fixed schedule
- **WHEN** 管理员取消的课程订单关联的排课 `schedule_type` 为 "fixed"，且无其他订单引用
- **THEN** 订单状态变为 "cancelled" 并全额退款，但 `course_schedules` 与 `lesson_schedules` 记录保留不删除

#### Scenario: Cancel already cancelled booking
- **WHEN** 管理员发送 `POST /api/v1/admin/bookings/1/cancel`，该订单状态已为 "cancelled"
- **THEN** 返回 HTTP 400，错误信息为"该预约已取消"

#### Scenario: Cancel non-existent booking
- **WHEN** 管理员发送 `POST /api/v1/admin/bookings/999/cancel`
- **THEN** 返回 HTTP 404

