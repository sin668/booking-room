# course-booking-api Specification

## Purpose
提供课程预约后端 API，支持查询课程课时列表、创建课程预约订单（含固定班课/1V1/全套课时优惠定价）、课程订单支付与取消，复用现有优惠券和支付基础设施。
## Requirements
### Requirement: Course lessons query API
系统 SHALL 提供 `GET /api/v1/courses/{course_id}/lessons` 接口，返回指定课程的全部课时列表，包含课时序号、标题、时长、状态和单价信息。

#### Scenario: Query lessons for active course
- **WHEN** 客户端请求 `GET /api/v1/courses/{course_id}/lessons`
- **THEN** 返回 200，响应包含按 `sort_order` 升序排列的课时数组
- **AND** 每个课时包含 `id`、`title`、`duration_minutes`、`sort_order`、`status`（可预约/已满/已过期）

#### Scenario: Query lessons for non-existent course
- **WHEN** 客户端请求不存在的 course_id
- **THEN** 返回 404，错误信息为"课程不存在"

### Requirement: Course booking pricing logic
系统 SHALL 根据预约类型和课时数量计算课程预约价格。定价规则：
- **固定班课（fixed）**：`已选课时数 × course.price`
- **1V1私人定制（custom）**：`已选课时数 × course.custom_price`
- **全套课时（full_package）**：当已选课时数等于课程全部可预约课时数时，使用 `course.full_package_price` 优惠价格

优惠券抵扣在课程费基础上计算，实付金额 = 课程费 - 优惠券抵扣金额。

#### Scenario: Fixed booking type pricing
- **GIVEN** 课程 `price=80`，用户选择 3 节固定班课课时
- **WHEN** 系统计算价格
- **THEN** `original_price = 240.00`（3 × 80）

#### Scenario: Custom 1V1 booking type pricing
- **GIVEN** 课程 `custom_price=200`，用户选择 2 节 1V1 课时
- **WHEN** 系统计算价格
- **THEN** `original_price = 400.00`（2 × 200）

#### Scenario: Full package discount pricing
- **GIVEN** 课程共 12 节可预约课时，`price=80`，`full_package_price=860`
- **WHEN** 用户选择全部 12 节课时
- **THEN** `original_price = 860.00`（全套优惠价）
- **AND** `discount_amount = 100.00`（12 × 80 - 860）

#### Scenario: Partial selection does not trigger full package price
- **GIVEN** 课程共 12 节课时，`full_package_price=860`
- **WHEN** 用户选择 10 节课时（非全部）
- **THEN** `original_price = 800.00`（10 × 80，不享受全套优惠）

### Requirement: Course booking creation API
系统 SHALL 提供 `POST /api/v1/course-bookings` 接口创建课程预约订单。请求 MUST 包含 `course_id`、`booking_type`（fixed/custom）、`lesson_ids`（课时 ID 数组）、`schedule_type`（fixed/custom）、`payment_method`（balance/wechat），可选 `coupon_id`。

初始订单状态 SHALL 由预约类型与开课日期决定，判定逻辑 SHALL 收敛为领域层单一纯函数（不再由 `course_booking_service` 与 `booking_payment_service` 各持一份）：

- `booking_type='custom'`（1V1 私人定制）→ `status='pending_confirm'`（待管理员确认）
- `booking_type='fixed'`（固定班课）→ 取已预约第一课时日期 `first_lesson_date` 与今天（业务本地时区）比较：`first_lesson_date > today` → `status='pending_start'`；否则 → `status='in_progress'`
- 当 `first_lesson_date` 无法确定时 SHALL 回退为 `in_progress`（保持现行 `else` 分支行为）

`status='pending_confirm'` 的订单 SHALL NOT 被微信支付回调提前推进状态；其余订单在支付成功后 SHALL 按同一判定函数重新计算状态。

未支付订单（微信支付下单后）SHALL 为 `status='pending_start'` 且 `payment_status='pending'`。该组合同时被支付对账任务用作查询条件（`status='pending_start' AND payment_status='pending' AND payment_provider='wechat'`），是两个 `pending` 字面量在同一查询中共现的点，重命名 SHALL 只改动 `status` 侧。

#### Scenario: Create course booking with balance payment
- **GIVEN** 用户已登录，课程存在且状态为 active
- **WHEN** 用户提交课程预约，选择余额支付，余额充足
- **THEN** 系统创建 booking 记录，`booking_type='course'`、`course_id`、`lesson_ids`、`payment_method='balance'`、`payment_status='paid'`
- **AND** `status` 按预约类型与开课日期判定为 `pending_confirm`、`pending_start` 或 `in_progress`
- **AND** 返回 201，响应包含 `booking_id` 和订单摘要

#### Scenario: Create fixed course booking before first lesson date
- **GIVEN** 用户提交 `booking_type='fixed'` 的课程预约
- **AND** 已预约第一课时日期晚于今天
- **WHEN** 系统创建订单
- **THEN** `status` 为 "pending_start"

#### Scenario: Create fixed course booking on or after first lesson date
- **GIVEN** 用户提交 `booking_type='fixed'` 的课程预约
- **AND** 已预约第一课时日期早于或等于今天
- **WHEN** 系统创建订单
- **THEN** `status` 为 "in_progress"

#### Scenario: Create custom 1V1 course booking
- **GIVEN** 用户提交 `booking_type='custom'` 的 1V1 私人定制预约
- **WHEN** 系统创建订单
- **THEN** `status` 为 "pending_confirm"，等待管理员确认
- **AND** 用户选择的日期与时间段 SHALL 存入 booking 记录供管理员确认时使用

#### Scenario: Create course booking with WeChat payment
- **GIVEN** 用户已登录，选择微信支付
- **WHEN** 用户提交课程预约
- **THEN** 系统创建 booking 记录，`payment_status='pending'`、`status='pending_start'`
- **AND** 调用微信支付 JSAPI 下单
- **AND** 返回 201，响应包含 `payment_params`（用于前端 `uni.requestPayment`）

#### Scenario: WeChat payment callback does not advance pending-confirm booking
- **GIVEN** 一笔 `status='pending_confirm'` 的 1V1 定制课程预约
- **WHEN** 微信支付回调成功
- **THEN** `payment_status` 变为 "paid"
- **AND** `status` SHALL 保持 "pending_confirm"，SHALL NOT 被推进为 `in_progress` 或 `pending_start`

#### Scenario: WeChat payment callback recomputes other course booking status
- **GIVEN** 一笔 `status='pending_start'`、`payment_status='pending'` 的固定班课预约
- **WHEN** 微信支付回调成功
- **THEN** `payment_status` 变为 "paid"
- **AND** `status` SHALL 由与创建时相同的领域判定函数按开课日期重新计算

#### Scenario: Payment reconciliation query touches only status side
- **WHEN** 支付对账任务查询待核对的微信支付订单
- **THEN** 查询条件 SHALL 为 `status='pending_start' AND payment_status='pending' AND payment_provider='wechat'`
- **AND** `payment_status='pending'`（待支付）SHALL NOT 被重命名触及

#### Scenario: Create booking with coupon
- **GIVEN** 用户选择一张有效优惠券
- **WHEN** 用户提交课程预约
- **THEN** 系统将优惠券关联到 booking
- **AND** `total_price = original_price - coupon_discount`
- **AND** 优惠券标记为已使用

#### Scenario: Create booking with invalid course
- **WHEN** 用户提交不存在的 course_id
- **THEN** 返回 404，错误信息为"课程不存在"

#### Scenario: Create booking with empty lesson selection
- **WHEN** 用户提交 `lesson_ids` 为空数组
- **THEN** 返回 422，错误信息为"请至少选择一节课时"

#### Scenario: Create booking with insufficient balance
- **GIVEN** 用户选择余额支付，余额不足
- **WHEN** 用户提交课程预约
- **THEN** 返回 400，错误信息为"余额不足"

### Requirement: Course booking list query
系统 SHALL 在现有 `GET /api/v1/bookings` 列表中支持返回课程预约订单。课程预约通过 `booking_type='course'` 标识，与自习室预约共存于 bookings 表。

#### Scenario: Query all bookings including course bookings
- **WHEN** 用户请求预约列表
- **THEN** 返回结果包含自习室预约和课程预约
- **AND** 课程预约记录包含 `course_name`、`lesson_titles`、`booking_type='course'` 信息

### Requirement: Course booking cancellation
系统 SHALL 支持取消课程预约订单，复用现有取消退款逻辑。课程预约取消后，已使用的优惠券 MUST 恢复为可用状态。

可取消的课程预约状态 SHALL 为 `pending_start`（待开始）与 `pending_confirm`（待确认，1V1 定制）；`in_progress` 状态的课程订单按通用取消策略处理。取消管理端课程订单时，仅删除该订单专属的 `schedule_type='custom'`（定制）排课与对应课时记录，`schedule_type='fixed'`（固定班课）排课一律保留。

#### Scenario: Cancel paid course booking
- **GIVEN** 用户有一笔已支付且状态为 `in_progress` 的课程预约
- **WHEN** 用户请求取消
- **THEN** 预约状态变为 `cancelled`
- **AND** 退款金额按现有取消政策计算
- **AND** 使用的优惠券恢复为可用

#### Scenario: Cancel pending course booking
> 标题沿用主 spec 原名（MODIFIED 整块替换语义要求）。主 spec 该 Scenario 的“pending”指**待支付**（`payment_status='pending'`），与订单状态重命名无关，语义保持不变。
- **GIVEN** 用户有一笔 `status='pending_start'`、`payment_status='pending'`（待支付）的课程预约
- **WHEN** 用户请求取消
- **THEN** 预约状态变为 `cancelled`
- **AND** 不产生退款
- **AND** 使用的优惠券恢复为可用

#### Scenario: Cancel paid pending-start course booking
- **GIVEN** 用户有一笔 `status='pending_start'`、`payment_status='paid'` 的课程预约
- **WHEN** 用户请求取消
- **THEN** 预约状态变为 `cancelled`
- **AND** 全额退款，`penalty_amount` 为 0
- **AND** 使用的优惠券恢复为可用

#### Scenario: Cancel pending-confirm custom course booking
- **GIVEN** 用户有一笔 `status='pending_confirm'` 且已支付的 1V1 定制课程预约
- **WHEN** 用户请求取消
- **THEN** 预约状态变为 `cancelled`，全额退款
- **AND** 该订单专属的 `schedule_type='custom'` 排课与课时记录被删除

#### Scenario: Cancel course booking keeps fixed schedule
- **GIVEN** 用户取消的课程预约关联 `schedule_type='fixed'` 的排课
- **WHEN** 取消成功
- **THEN** `course_schedules` 与 `lesson_schedules` 记录 SHALL 保留不删除

