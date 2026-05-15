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

### Requirement: Seat database model
系统 SHALL 创建 `seats` 表，包含字段：`id`（主键，自增）、`room_id`（外键关联 study_rooms.id，非空）、`seat_number`（VARCHAR(10)，如 "A-01"，非空）、`zone`（VARCHAR(20)，枚举值 "quiet"/"keyboard"/"vip"，非空）、`position`（VARCHAR(20)，如 "靠窗"/"中间"/"独立"，可空）、`floor`（INTEGER，默认 3）、`price_per_hour`（DECIMAL(10,2)，非空）、`status`（VARCHAR(20)，默认 "available"，枚举值 "available"/"maintenance"）、`row`（INTEGER，座位图行号）、`col`（INTEGER，座位图列号）、`created_at`、`updated_at`。

#### Scenario: Create seat record
- **WHEN** 向 `seats` 表插入一条记录，`room_id=1`，`seat_number="A-01"`，`zone="quiet"`，`position="靠窗"`，`price_per_hour=6.00`，`row=1`，`col=1`
- **THEN** 记录成功创建，`id` 自增，`status` 默认为 "available"，`floor` 默认为 3

### Requirement: List available seats API
系统 SHALL 提供 `GET /api/v1/rooms/{room_id}/seats/` 接口，返回指定自习室的座位列表，支持查询参数 `date`（YYYY-MM-DD，可选）、`start_time`（HH:MM，可选）、`end_time`（HH:MM，可选）。当提供日期和时段参数时，每个座位额外返回 `is_available` 字段（布尔值，表示该时段是否可预约）。

#### Scenario: List all seats without time filter
- **WHEN** 客户端发送 `GET /api/v1/rooms/1/seats/` 不带时间参数
- **THEN** 返回 HTTP 200，响应为座位数组，每个座位包含 `id`、`seat_number`、`zone`、`position`、`floor`、`price_per_hour`、`status`、`row`、`col`

#### Scenario: List seats with availability filter
- **WHEN** 客户端发送 `GET /api/v1/rooms/1/seats/?date=2026-05-01&start_time=09:00&end_time=12:00`
- **THEN** 返回 HTTP 200，每个座位额外包含 `is_available` 字段，已被预约的座位 `is_available=false`

#### Scenario: Room not found
- **WHEN** 客户端发送 `GET /api/v1/rooms/999/seats/`
- **THEN** 返回 HTTP 404

### Requirement: Create booking API
系统 SHALL 提供 `POST /api/v1/bookings/` 接口，允许已登录用户创建座位预约。请求体包含 `seat_id`（整数，必填）、`date`（日期字符串 YYYY-MM-DD，必填）、`start_time`（时间字符串 HH:MM，必填）、`end_time`（时间字符串 HH:MM，必填）、`coupon_id`（整数，可选，指向当前用户持有的用户卡券）。创建成功返回 HTTP 201，响应包含预约详情。若传入 `coupon_id`，系统 MUST 在后端校验卡券归属、状态、有效期、适用范围和订单门槛，并计算抵扣后金额。

#### Scenario: Successful booking creation
- **GIVEN** 用户已登录
- **WHEN** 用户发送 `POST /api/v1/bookings/`，body 为 `{"seat_id": 1, "date": "2026-05-01", "start_time": "09:00", "end_time": "12:00"}`
- **THEN** 返回 HTTP 201
- **AND** 响应包含 `id`、`seat_id`、`user_id`、`room_id`、`date`、`start_time`、`end_time`、`status`（值为 "confirmed"）、`original_price`、`discount_amount`、`total_price`、`coupon_id`、`created_at`

#### Scenario: Successful booking creation with coupon
- **GIVEN** 用户已登录且拥有一张可用于该预约的卡券
- **WHEN** 用户发送 `POST /api/v1/bookings/` 并传入该 `coupon_id`
- **THEN** 返回 HTTP 201
- **AND** 响应中的 `discount_amount` 大于 0
- **AND** `total_price` 等于 `original_price - discount_amount`
- **AND** 该用户卡券状态变为 `used`

#### Scenario: Booking with invalid coupon
- **GIVEN** 用户已登录
- **WHEN** 用户发送 `POST /api/v1/bookings/` 并传入不存在、不属于自己、已使用、已过期或不适用该订单的 `coupon_id`
- **THEN** 返回 HTTP 400
- **AND** 不创建预约
- **AND** 不改变任何卡券状态

#### Scenario: Booking with non-existent seat
- **GIVEN** 用户已登录
- **WHEN** 用户发送 `POST /api/v1/bookings/`，`seat_id` 对应的座位不存在
- **THEN** 返回 HTTP 404，错误信息为"座位不存在"

#### Scenario: Booking with time conflict on same seat
- **GIVEN** 用户已登录
- **WHEN** 用户发送 `POST /api/v1/bookings/`，所选时间段与同一座位同日期已有预约重叠
- **THEN** 返回 HTTP 409，错误信息为"该座位该时段已被预约"

#### Scenario: Booking with invalid time range
- **GIVEN** 用户已登录
- **WHEN** 用户发送 `POST /api/v1/bookings/`，`end_time` 早于或等于 `start_time`
- **THEN** 返回 HTTP 422，错误信息提示结束时间必须晚于开始时间

#### Scenario: Booking seat under maintenance
- **GIVEN** 用户已登录
- **WHEN** 用户发送 `POST /api/v1/bookings/`，座位状态为 "maintenance"
- **THEN** 返回 HTTP 400，错误信息为"该座位正在维护中"

#### Scenario: Booking requires authentication
- **GIVEN** 用户未登录
- **WHEN** 用户发送 `POST /api/v1/bookings/`
- **THEN** 返回 HTTP 401

### Requirement: List my bookings API
系统 SHALL 提供 `GET /api/v1/bookings/` 接口，返回当前登录用户的预约列表。支持查询参数 `page`（默认 1）、`page_size`（默认 10，最大 50）、`status`（可选，筛选状态）。

#### Scenario: Successful list request with default pagination
- **WHEN** 已登录用户发送 `GET /api/v1/bookings/` 不带查询参数
- **THEN** 返回 HTTP 200，响应包含 `items`（预约数组）和 `total`、`page`、`page_size` 字段

#### Scenario: List bookings filtered by status
- **WHEN** 已登录用户发送 `GET /api/v1/bookings/?status=confirmed`
- **THEN** 返回 HTTP 200，`items` 中仅包含 `status` 为 "confirmed" 的预约

### Requirement: Get booking detail API
系统 SHALL 提供 `GET /api/v1/bookings/{booking_id}/` 接口，返回预约详情。用户只能查看自己的预约。

#### Scenario: Successful detail request
- **WHEN** 已登录用户请求 `GET /api/v1/bookings/1/`，booking_id=1 属于该用户
- **THEN** 返回 HTTP 200，响应包含预约完整信息、关联的座位信息（`seat` 字段，含 seat_number、zone、position、price_per_hour）及房间信息（`room` 字段，含 name、address）

#### Scenario: Request other user's booking
- **WHEN** 已登录用户请求 `GET /api/v1/bookings/2/`，booking_id=2 属于其他用户
- **THEN** 返回 HTTP 404

#### Scenario: Request non-existent booking
- **WHEN** 已登录用户请求 `GET /api/v1/bookings/999/`
- **THEN** 返回 HTTP 404

### Requirement: Cancel booking API
系统 SHALL 提供 `POST /api/v1/bookings/{booking_id}/cancel/` 接口，允许用户取消自己的预约。仅 `confirmed` 状态的预约可取消，取消后状态变为 `cancelled`。若该预约使用了卡券，系统 SHALL 在取消成功后恢复对应用户卡券为可使用状态。

#### Scenario: Successful cancellation
- **GIVEN** 已登录用户拥有状态为 "confirmed" 的预约
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** 预约状态变为 "cancelled"

#### Scenario: Cancel booking restores used coupon
- **GIVEN** 已登录用户拥有一笔使用卡券的 "confirmed" 预约
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** 预约状态变为 "cancelled"
- **AND** 对应用户卡券恢复为 `available`

#### Scenario: Cancel already cancelled booking
- **GIVEN** 已登录用户拥有状态为 "cancelled" 的预约
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 400，错误信息为"该预约已取消"

#### Scenario: Cancel other user's booking
- **GIVEN** 已登录用户请求其他用户的预约
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 404

### Requirement: Booking database model
系统 SHALL 创建 `bookings` 表，包含字段：`id`（主键，自增）、`seat_id`（外键关联 seats.id，非空）、`user_id`（外键关联 users.id，非空）、`room_id`（外键关联 study_rooms.id，非空）、`date`（DATE，非空）、`start_time`（TIME，非空）、`end_time`（TIME，非空）、`status`（VARCHAR(20)，默认 "confirmed"，枚举值 "confirmed"/"cancelled"/"completed"）、`original_price`（DECIMAL(10,2)，非空）、`discount_amount`（DECIMAL(10,2)，默认 0，非空）、`total_price`（DECIMAL(10,2)，非空，表示抵扣后实付金额）、`coupon_id`（外键关联 user_coupons.id，可空）、`created_at`、`updated_at`。

#### Scenario: Create booking record without coupon
- **GIVEN** 用户创建不使用卡券的预约
- **WHEN** 向 `bookings` 表插入一条记录，原价为 18.00
- **THEN** 记录成功创建
- **AND** `original_price=18.00`
- **AND** `discount_amount=0.00`
- **AND** `total_price=18.00`
- **AND** `coupon_id` 为空

#### Scenario: Create booking record with coupon
- **GIVEN** 用户创建使用卡券的预约
- **WHEN** 向 `bookings` 表插入一条记录，原价为 24.00，抵扣为 3.00
- **THEN** 记录成功创建
- **AND** `original_price=24.00`
- **AND** `discount_amount=3.00`
- **AND** `total_price=21.00`
- **AND** `coupon_id` 指向被使用的用户卡券

### Requirement: Booking response schema
预约列表/详情响应 SHALL 包含以下字段：`id`（整数）、`seat_id`（整数）、`user_id`（整数）、`room_id`（整数）、`date`（日期字符串 YYYY-MM-DD）、`start_time`（时间字符串 HH:MM）、`end_time`（时间字符串 HH:MM）、`status`（枚举字符串）、`original_price`（数字）、`discount_amount`（数字）、`total_price`（数字）、`coupon_id`（整数或 null）、`created_at`（ISO 时间字符串）、`seat`（对象，包含 id、seat_number、zone、position、price_per_hour）、`room`（对象，包含 id、name、address）。

#### Scenario: Response field validation
- **GIVEN** 客户端请求预约详情
- **WHEN** 后端返回预约详情
- **THEN** 响应包含 `id`、`seat_id`、`room_id`、`date`、`start_time`、`end_time`、`status`、`original_price`、`discount_amount`、`total_price`、`coupon_id`、`created_at`、`seat`、`room` 字段
