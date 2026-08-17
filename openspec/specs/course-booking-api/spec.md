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

#### Scenario: Create course booking with balance payment
- **GIVEN** 用户已登录，课程存在且状态为 active
- **WHEN** 用户提交课程预约，选择余额支付，余额充足
- **THEN** 系统创建 booking 记录，`booking_type='course'`、`course_id`、`lesson_ids`、`payment_method='balance'`、`payment_status='paid'`
- **AND** 返回 201，响应包含 `booking_id` 和订单摘要

#### Scenario: Create course booking with WeChat payment
- **GIVEN** 用户已登录，选择微信支付
- **WHEN** 用户提交课程预约
- **THEN** 系统创建 booking 记录，`payment_status='pending'`
- **AND** 调用微信支付 JSAPI 下单
- **AND** 返回 201，响应包含 `payment_params`（用于前端 `uni.requestPayment`）

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

#### Scenario: Cancel paid course booking
- **GIVEN** 用户有一笔已支付的课程预约
- **WHEN** 用户请求取消
- **THEN** 预约状态变为 `cancelled`
- **AND** 退款金额按现有取消政策计算
- **AND** 使用的优惠券恢复为可用

#### Scenario: Cancel pending course booking
- **GIVEN** 用户有一笔待支付的课程预约
- **WHEN** 用户请求取消
- **THEN** 预约状态变为 `cancelled`
- **AND** 不产生退款
- **AND** 使用的优惠券恢复为可用

