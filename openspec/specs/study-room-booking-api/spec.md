## Purpose

自习室预约系统 API 提供自习室浏览、座位选择、预约创建和管理功能，支撑 br-app 前端的自习室预约流程。
## Requirements
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
系统 SHALL 提供 `POST /api/v1/bookings/` 接口，允许已登录用户创建座位预约。请求体包含 `seat_id`（整数，必填）、`date`（日期字符串 YYYY-MM-DD，必填）、`start_time`（时间字符串 HH:MM，必填）、`end_time`（时间字符串 HH:MM，必填）、`payment_method`（字符串，必填，枚举值 "balance"/"wechat"，默认 "balance"）、`coupon_id`（整数，可选，指向当前用户持有的用户卡券）。创建成功返回 HTTP 201，响应包含预约详情。若传入 `coupon_id`，系统 MUST 在后端校验卡券归属、状态、有效期、适用范围和订单门槛，并计算抵扣后金额。

初始订单状态 SHALL 由业务本地时间（`app/utils/timezone.py` 的 `booking_now()`）与预约开始时刻（`date + start_time`）比较决定：

- 当 `payment_method='balance'` 时，系统 SHALL 原子扣除用户余额并创建 `payment_status='paid'` 的预约；其 `status` SHALL 为 `pending_start`（当 `now < date+start_time`）或 `in_progress`（当 `now >= date+start_time`）
- 当 `payment_method='wechat'` 时，系统 SHALL 创建 `payment_status='pending'` 且 `status='pending_start'` 的预约（**不因时间而变**），调用微信支付 JSAPI 下单，响应额外包含 `payment_params` 字段。若微信支付配置不可用或下单失败，SHALL NOT 创建预约记录

`status='pending_start'` 与 `payment_status='pending'` 的组合表示「已下单待支付」，与「已支付待开始」（`pending_start` + `paid`）共用同一 `status` 值，二者 SHALL 由 `payment_status` 区分。

#### Scenario: Successful booking creation with balance payment
> 标题沿用主 spec 原名（MODIFIED 整块替换语义要求）。**修正主 spec 错误断言**：原文写“余额支付 → `status` 为 `confirmed`”不完整；实测 `booking_service.py:283-292` 对余额支付同样做**时间条件判定**：未来时段 → `pending`（新词表 `pending_start`），已开始时段 → `confirmed`（新词表 `in_progress`）。本 Scenario 覆盖未来时段分支，已开始时段分支见下一个 Scenario。
- **GIVEN** 用户已登录且余额充足
- **AND** 当前业务本地时间早于 `date + start_time`
- **WHEN** 用户发送 `POST /api/v1/bookings/`，body 为 `{"seat_id": 1, "date": "2026-05-01", "start_time": "09:00", "end_time": "12:00", "payment_method": "balance"}`
- **THEN** 返回 HTTP 201
- **AND** 响应包含 `id`、`seat_id`、`user_id`、`room_id`、`date`、`start_time`、`end_time`、`status`（值为 "pending_start"）、`original_price`、`discount_amount`、`total_price`、`coupon_id`、`payment_method`（值为 "balance"）、`payment_status`（值为 "paid"）、`created_at`

#### Scenario: Successful booking creation with balance payment for an already-started slot
- **GIVEN** 用户已登录且余额充足
- **AND** 当前业务本地时间已到达或晚于 `date + start_time`
- **WHEN** 用户发送 `POST /api/v1/bookings/` 且 `payment_method` 为 "balance"
- **THEN** 返回 HTTP 201
- **AND** `status` 值为 "in_progress"，`payment_status` 值为 "paid"

#### Scenario: Successful booking creation with WeChat payment
- **GIVEN** 用户已登录且微信支付配置可用
- **WHEN** 用户发送 `POST /api/v1/bookings/`，body 为 `{"seat_id": 1, "date": "2026-05-01", "start_time": "09:00", "end_time": "12:00", "payment_method": "wechat"}`
- **THEN** 返回 HTTP 201
- **AND** 响应包含预约详情及 `payment_method="wechat"`、`payment_status="pending"`、`payment_params`（包含 timeStamp、nonceStr、package、signType、paySign）
- **AND** `status` 值为 "pending_start"，无论当前时间与 `date + start_time` 的先后关系
- **AND** 用户余额不变

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

#### Scenario: Balance payment insufficient balance
- **GIVEN** 用户已登录且 `payment_method='balance'`
- **WHEN** 用户余额不足
- **THEN** 返回 HTTP 402
- **AND** 错误信息为"余额不足"

#### Scenario: WeChat Pay disabled
- **GIVEN** 用户已登录且 `payment_method='wechat'`
- **AND** `WECHAT_PAY_ENABLED=false`
- **WHEN** 用户创建预约
- **THEN** 返回 HTTP 503
- **AND** 错误信息说明微信支付暂不可用

#### Scenario: Booking requires authentication
- **GIVEN** 用户未登录
- **WHEN** 用户发送 `POST /api/v1/bookings/`
- **THEN** 返回 HTTP 401

### Requirement: List my bookings API
系统 SHALL 提供 `GET /api/v1/bookings/` 接口，返回当前登录用户的预约列表。支持查询参数 `page`（默认 1）、`page_size`（默认 10，最大 50）、`status`（可选，筛选状态）。

`status` 参数取值为新词表（`pending_confirm`/`pending_start`/`in_progress`/`completed`/`cancelled`）。其中 `pending_start` 与 `in_progress` 为**派生筛选**，其余为纯列匹配：

- `?status=pending_start` → `status IN ('pending_start','pending_confirm') AND payment_status='paid'`
- `?status=in_progress` → `status='in_progress' AND payment_status='paid'`；随后 SHALL 对课程订单做**后置过滤**，仅保留存在 `CourseSchedule.start_date <= today` 的订单，座位订单不做二次过滤

该派生口径与管理端 `GET /api/v1/admin/bookings/` 的同名参数（纯列匹配）语义不同，属既有已知行为，本次重命名 SHALL NOT 统一。

#### Scenario: Successful list request with default pagination
- **WHEN** 已登录用户发送 `GET /api/v1/bookings/` 不带查询参数
- **THEN** 返回 HTTP 200，响应包含 `items`（预约数组）和 `total`、`page`、`page_size` 字段

#### Scenario: List bookings filtered by status
> 标题沿用主 spec 原名（MODIFIED 整块替换语义要求）。主 spec 原写 `?status=confirmed` 仅做纯列匹配；实测 C 端该筛选为**派生口径**（附加 `payment_status='paid'`），且取值已重命名为 `in_progress`。派生口径本次 SHALL 保持不变（行为零变更）。
- **WHEN** 已登录用户发送 `GET /api/v1/bookings/?status=in_progress`
- **THEN** 返回 HTTP 200，`items` 中仅包含 `status='in_progress'` 且 `payment_status='paid'` 的预约

#### Scenario: In-progress filter post-filters course bookings by start date
- **GIVEN** 用户有两笔 `status='in_progress'` 且已支付的课程预约，其课程的 `CourseSchedule.start_date` 分别为今天之前与今天之后
- **WHEN** 用户发送 `GET /api/v1/bookings/?status=in_progress`
- **THEN** `items` 中仅包含 `start_date <= today` 的那一笔

#### Scenario: In-progress filter does not post-filter seat bookings
- **GIVEN** 用户有一笔 `status='in_progress'` 且已支付的座位预约，其 `date` 晚于今天
- **WHEN** 用户发送 `GET /api/v1/bookings/?status=in_progress`
- **THEN** 该预约 SHALL 出现在 `items` 中（座位订单不做开课日期二次过滤）

#### Scenario: List bookings filtered by pending-start status
- **WHEN** 已登录用户发送 `GET /api/v1/bookings/?status=pending_start`
- **THEN** 返回 HTTP 200，`items` 中包含 `status='pending_start'` 与 `status='pending_confirm'` 且 `payment_status='paid'` 的预约
- **AND** `payment_status='pending'`（待支付）的预约 SHALL NOT 出现在结果中

#### Scenario: Unpaid bookings appear only without status filter
- **GIVEN** 用户有一笔 `status='pending_start'` 且 `payment_status='pending'` 的微信支付预约
- **WHEN** 用户发送 `GET /api/v1/bookings/`（不带 `status`）
- **THEN** 该预约 SHALL 出现在 `items` 中，供前端展示「去支付」入口

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
系统 SHALL 提供 `POST /api/v1/bookings/{booking_id}/cancel/` 接口，允许用户取消自己的预约。可取消条件 SHALL 由领域函数 `can_cancel_paid_booking`（`app/domain/booking_rules.py`）单一判定：`status IN ('in_progress','pending_start')` **且** `payment_status='paid'` **且** 预约尚未开始（`datetime.combine(date, start_time) > now`，`now` 取业务本地时间）。服务层 SHALL NOT 内联第二份同语义判定。

系统 MUST 使用服务端业务本地时间与预约开始时间（`date + start_time`）计算取消规则：超过 2 天取消不扣款并全额退款；1 天到 2 天之间扣 10% 订单金额；2 小时到 24 小时之间扣 20% 订单金额；2 小时内扣 50% 订单金额；到达预约开始时间点及之后不可取消。取消成功后预约状态变为 `cancelled`，记录取消时间、扣款金额和退款金额，剩余金额退回用户钱包，并生成一条钱包入账流水。若该预约使用了卡券，系统 SHALL 在取消成功后恢复对应用户卡券为可使用状态。

取消被拒绝时系统 SHALL 调用 `_sync_booking_completion`；但该同步**仅在预约结束时刻（`date + end_time`）已到达时**才真正把状态置为 `completed`。因此在「已开始但未结束」的窗口内，被拒绝取消的预约状态 SHALL 保持 `in_progress` 不变。

#### Scenario: Successful cancellation more than two days before start
- **GIVEN** 已登录用户拥有状态为 "in_progress"、`payment_status='paid'`、实付金额为 100.00 的预约
- **AND** 当前服务端业务本地时间距离预约开始时间超过 48 小时
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** 预约状态变为 "cancelled"
- **AND** `penalty_amount` 为 0.00
- **AND** `refund_amount` 为 100.00
- **AND** 用户钱包余额增加 100.00
- **AND** 系统创建一条 `type='booking_refund'`、标题为“取消退款”的钱包流水

#### Scenario: Successful cancellation of a paid pending-start booking
- **GIVEN** 已登录用户拥有状态为 "pending_start"、`payment_status='paid'`、尚未到开始时间的预约
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200，预约状态变为 "cancelled"
- **AND** 扣款档位按距开始时间的远近计算，与 "in_progress" 订单适用同一规则

#### Scenario: Cancellation one to two days before start
- **GIVEN** 已登录用户拥有状态为 "in_progress"、`payment_status='paid'`、实付金额为 100.00 的预约
- **AND** 当前服务端业务本地时间距离预约开始时间大于 24 小时且小于等于 48 小时
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** `penalty_amount` 为 10.00
- **AND** `refund_amount` 为 90.00
- **AND** 用户钱包余额增加 90.00

#### Scenario: Cancellation two to twenty four hours before start
- **GIVEN** 已登录用户拥有状态为 "in_progress"、`payment_status='paid'`、实付金额为 100.00 的预约
- **AND** 当前服务端业务本地时间距离预约开始时间大于 2 小时且小于等于 24 小时
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** `penalty_amount` 为 20.00
- **AND** `refund_amount` 为 80.00
- **AND** 用户钱包余额增加 80.00

#### Scenario: Cancellation within two hours before start
- **GIVEN** 已登录用户拥有状态为 "in_progress"、`payment_status='paid'`、实付金额为 100.00 的预约
- **AND** 当前服务端业务本地时间距离预约开始时间大于 0 且小于等于 2 小时
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** `penalty_amount` 为 50.00
- **AND** `refund_amount` 为 50.00
- **AND** 用户钱包余额增加 50.00

#### Scenario: Cancel booking at or after start time
> 标题沿用主 spec 原名（MODIFIED 整块替换语义要求）。**修正主 spec 错误断言**：原文写“取消已开始预约 → 状态变为 `completed`”不完整；实测 `should_mark_booking_completed` 用的是 **`end_time`** 而非 `start_time`（`domain/booking_rules.py:49-54`），因此“已开始未结束”窗口内取消被拒时状态 SHALL **保持 `in_progress`**。已过 `end_time` 的分支见下一个 Scenario。
- **GIVEN** 已登录用户拥有状态为 "in_progress" 的预约
- **AND** 当前服务端业务本地时间已到达或晚于预约开始时间，但**尚未到达结束时间**（`date + end_time`）
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 400 或 HTTP 409
- **AND** 错误信息说明预约已开始不可取消
- **AND** 预约状态 SHALL 保持 "in_progress"（自动完成同步仅在结束时刻已到达时生效）
- **AND** 不增加用户钱包余额
- **AND** 不创建退款流水

#### Scenario: Cancel booking after end time marks it completed
- **GIVEN** 已登录用户拥有状态为 "in_progress" 的预约
- **AND** 当前服务端业务本地时间已到达或晚于预约结束时间（`date + end_time`）
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 400 或 HTTP 409
- **AND** 预约状态变为 "completed"

#### Scenario: Cancel booking restores used coupon
- **GIVEN** 已登录用户拥有一笔使用卡券的 "in_progress" 预约
- **AND** 预约尚未到开始时间且支付状态为 "paid"
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** 预约状态变为 "cancelled"
- **AND** 对应用户卡券恢复为 `available`

#### Scenario: Cancel already cancelled booking
- **GIVEN** 已登录用户拥有状态为 "cancelled" 的预约
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 400，错误信息为"该预约已取消"
- **AND** 不增加用户钱包余额
- **AND** 不创建退款流水

#### Scenario: Cancel unpaid booking
- **GIVEN** 已登录用户拥有 `status='pending_start'` 且 `payment_status='pending'`（待支付）的预约
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 400
- **AND** 错误信息说明未支付预约不可按退款规则取消
- **AND** 不增加用户钱包余额

#### Scenario: Cancel other user's booking
- **GIVEN** 已登录用户请求其他用户的预约
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 404

#### Scenario: Duplicate cancellation does not refund twice
- **GIVEN** 已登录用户拥有一笔已成功取消且已退款的预约
- **WHEN** 用户再次发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 400
- **AND** 用户钱包余额不再变化
- **AND** 不创建第二条退款流水

### Requirement: Booking database model
系统 SHALL 更新 `bookings` 表，包含字段：`id`（主键，自增）、`seat_id`（外键关联 seats.id，非空）、`user_id`（外键关联 users.id，非空）、`room_id`（外键关联 study_rooms.id，非空）、`date`（DATE，非空）、`start_time`（TIME，非空）、`end_time`（TIME，非空）、`status`（VARCHAR(20)，默认 "in_progress"，枚举值 "pending_confirm"/"pending_start"/"in_progress"/"completed"/"cancelled"）、`original_price`（DECIMAL(10,2)，非空）、`discount_amount`（DECIMAL(10,2)，默认 0，非空）、`total_price`（DECIMAL(10,2)，非空，表示抵扣后实付金额）、`coupon_id`（外键关联 user_coupons.id，可空）、`payment_method`（VARCHAR(20)，默认 "balance"，枚举值 "balance"/"wechat"）、`payment_status`（VARCHAR(20)，默认 "paid"，枚举值 "pending"/"paid"/"failed"）、`payment_provider`（VARCHAR(20)，可空）、`prepay_id`（VARCHAR(64)，可空）、`transaction_id`（VARCHAR(64)，可空）、`paid_at`（TIMESTAMP，可空）、`cancelled_at`（TIMESTAMP，可空）、`penalty_amount`（DECIMAL(10,2)，默认 0，非空）、`refund_amount`（DECIMAL(10,2)，默认 0，非空）、`cancel_policy`（VARCHAR(32)，可空，用于记录扣费档位）、`created_at`、`updated_at`。

`status` 列类型为 `VARCHAR(20)` 且**无数据库层 enum 或 CHECK 约束**，新词表最长值 `pending_start`（13 字符）不超过列宽，因此本次重命名 SHALL NOT 需要任何 DDL 变更，仅需一条数据迁移 `UPDATE`。列默认值 SHALL 同步更新为新词表，避免残留旧字面量。

`payment_status` 的 `pending` 值语义为「待支付」，SHALL NOT 被本次重命名触及。

#### Scenario: Create booking record with balance payment
- **GIVEN** 用户使用余额支付创建预约
- **WHEN** 向 `bookings` 表插入一条记录
- **THEN** 记录成功创建
- **AND** `payment_method='balance'`、`payment_status='paid'`
- **AND** `status` 为 `pending_start` 或 `in_progress`（取决于当前业务本地时间与 `date + start_time` 的比较）
- **AND** `penalty_amount=0`、`refund_amount=0`、`cancelled_at` 为空

#### Scenario: Create booking record with WeChat payment
- **GIVEN** 用户使用微信支付创建预约
- **WHEN** 向 `bookings` 表插入一条记录
- **THEN** 记录成功创建
- **AND** `payment_method='wechat'`、`payment_status='pending'`、`status='pending_start'`、`prepay_id` 不为空
- **AND** `penalty_amount=0`、`refund_amount=0`、`cancelled_at` 为空

#### Scenario: Status column requires no DDL change
- **WHEN** 执行本次重命名的数据迁移
- **THEN** SHALL NOT 产生任何 `ALTER TABLE` 语句
- **AND** 迁移 SHALL 仅为限定 `status` 列的 `UPDATE`，且 WHERE 子句只命中旧值 `pending` 与 `confirmed`，可安全重跑

#### Scenario: Persist cancellation audit fields
- **GIVEN** 用户成功取消预约
- **WHEN** 系统更新 `bookings` 表
- **THEN** `status='cancelled'`
- **AND** `cancelled_at` 不为空
- **AND** `penalty_amount` 和 `refund_amount` 为本次取消计算结果
- **AND** `cancel_policy` 记录对应扣费档位

### Requirement: Booking response schema
预约列表/详情响应 SHALL 包含以下字段：`id`（整数）、`seat_id`（整数）、`user_id`（整数）、`room_id`（整数）、`date`（日期字符串 YYYY-MM-DD）、`start_time`（时间字符串 HH:MM）、`end_time`（时间字符串 HH:MM）、`status`（枚举字符串，取值为新词表五值）、`original_price`（数字）、`discount_amount`（数字）、`total_price`（数字）、`coupon_id`（整数或 null）、`payment_method`（字符串，枚举值 "balance"/"wechat"）、`payment_status`（字符串，枚举值 "pending"/"paid"/"failed"）、`paid_at`（ISO 时间字符串或 null）、`cancelled_at`（ISO 时间字符串或 null）、`penalty_amount`（数字）、`refund_amount`（数字）、`cancel_policy`（字符串或 null）、`refund_transaction_id`（整数或 null）、`cancel_penalty_amount`（数字或 null）、`cancel_refund_amount`（数字或 null）、`can_cancel`（布尔值）、`started`（布尔值或 null，仅课程订单赋值）、`created_at`（ISO 时间字符串）、`seat`（对象，包含 id、seat_number、zone、position、price_per_hour）、`room`（对象，包含 id、name、address）。

`can_cancel` SHALL 由领域函数 `can_cancel_paid_booking` 计算，与取消接口使用同一判定，SHALL NOT 存在第二份实现。

`started` 字段 SHALL 仅对课程订单赋值为 `start_date <= today`（1V1 定制订单的 `start_date` 取 `bookings.date`），座位订单 SHALL 为 `null`。

后端 SHALL NOT 新增 `display_status` 只读派生字段：重命名后展示状态与落库状态为恒等映射，前端直接消费 `status`。

#### Scenario: Response field validation
- **GIVEN** 客户端请求预约详情
- **WHEN** 后端返回预约详情
- **THEN** 响应包含 `id`、`seat_id`、`room_id`、`date`、`start_time`、`end_time`、`status`、`original_price`、`discount_amount`、`total_price`、`coupon_id`、`payment_method`、`payment_status`、`paid_at`、`cancelled_at`、`penalty_amount`、`refund_amount`、`cancel_policy`、`cancel_penalty_amount`、`cancel_refund_amount`、`can_cancel`、`started`、`created_at`、`seat`、`room` 字段

#### Scenario: Confirmed future booking can cancel
> 标题沿用主 spec 原名（MODIFIED 整块替换语义要求）；旧状态值 `confirmed` 已重命名为 `in_progress`。
- **GIVEN** 客户端请求尚未开始且已支付的 `in_progress` 预约
- **WHEN** 后端返回预约详情或列表项
- **THEN** `can_cancel` 为 true

#### Scenario: Paid pending-start booking can cancel
- **GIVEN** 客户端请求 `status='pending_start'`、`payment_status='paid'` 且尚未到开始时间的预约
- **WHEN** 后端返回预约详情或列表项
- **THEN** `can_cancel` 为 true

#### Scenario: Unpaid booking cannot cancel
- **GIVEN** 客户端请求 `status='pending_start'` 且 `payment_status='pending'`（待支付）的预约
- **WHEN** 后端返回预约详情或列表项
- **THEN** `can_cancel` 为 false

#### Scenario: Started booking cannot cancel
- **GIVEN** 客户端请求已到达开始时间的预约
- **WHEN** 后端返回预约详情或列表项
- **THEN** `can_cancel` 为 false

#### Scenario: No display_status field is added
- **WHEN** 重构完成后检查预约响应 schema
- **THEN** SHALL NOT 存在名为 `display_status` 的字段
- **AND** 前端展示状态 SHALL 直接由 `status` 决定

### Requirement: Auto-complete started bookings
系统 SHALL 在预约**结束时刻**（`date + end_time`）及之后将仍为 `in_progress` 的已支付**座位**预约变为 `completed`，确保已开始预约不可取消。该判定 SHALL 由领域函数 `should_mark_booking_completed`（`app/domain/booking_rules.py`）单一提供，条件为 `status='in_progress' AND payment_status='paid' AND datetime.combine(date, end_time) <= now`。

自动完成的批量同步 SHALL 限定 `booking_type != 'course'`（课程订单的完成由订单状态定时任务按课时进度处理，不走此路径）。

「不可取消」的边界由**开始时间**决定（`has_booking_started` 使用 `start_time`），而「自动完成」的边界由**结束时间**决定，二者不同；因此在「已开始但未结束」的窗口内，预约状态 SHALL 保持 `in_progress` 且 `can_cancel` 为 false。

#### Scenario: Sync completed booking during list query
- **GIVEN** 当前用户存在一笔已到**结束时间**且状态为 "in_progress" 的已支付座位预约
- **WHEN** 用户请求 `GET /api/v1/bookings/`
- **THEN** 系统将该预约状态同步为 "completed"
- **AND** 列表响应中该预约不可取消

#### Scenario: Booking started but not ended stays in progress
- **GIVEN** 当前用户存在一笔已过开始时间但尚未到结束时间的已支付座位预约
- **WHEN** 用户请求 `GET /api/v1/bookings/`
- **THEN** 该预约状态 SHALL 保持 "in_progress"，SHALL NOT 被同步为 "completed"
- **AND** `can_cancel` 为 false

#### Scenario: Sync completed booking during cancellation attempt
- **GIVEN** 当前用户存在一笔已到结束时间且状态为 "in_progress" 的已支付座位预约
- **WHEN** 用户请求取消该预约
- **THEN** 系统将该预约状态同步为 "completed"
- **AND** 拒绝取消

#### Scenario: Unpaid booking is not auto-completed
- **GIVEN** 当前用户存在一笔已到结束时间但 `payment_status='pending'` 的座位预约
- **WHEN** 用户请求 `GET /api/v1/bookings/`
- **THEN** 该预约状态 SHALL NOT 被同步为 "completed"

#### Scenario: Course bookings are excluded from seat auto-completion
- **GIVEN** 当前用户存在一笔 `booking_type='course'` 且已到结束时间的已支付预约
- **WHEN** 座位预约自动完成同步执行
- **THEN** 该课程预约 SHALL NOT 被此路径修改状态
- **AND** 其状态流转由订单状态定时任务按课时进度处理

