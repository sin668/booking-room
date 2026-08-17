# Comet Design Handoff

- Change: course-booking
- Phase: design
- Mode: compact
- Context hash: 46e95459a46c77441bac2a944090e9d7bf973db8c190c8112764f42d26993e9e

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/course-booking/proposal.md

- Source: openspec/changes/course-booking/proposal.md
- Lines: 1-28
- SHA256: 23ed3b37ef881a44ab810664f8d371fb5e71b02c63b5a75b5495a125efa204eb

```md
## Why

平台目前仅支持自习室座位预约，培训课程页面（课程详情、课程列表）只提供浏览功能，用户无法直接预约课程。需要在 br-app 中新增课程预约下单功能，支持课时选择、全套课时优惠、优惠券抵扣和支付，并将课程预约订单纳入现有订单列表统一管理。

## What Changes

- **数据模型扩展**：在 `courses` 表新增全套课时优惠价格字段（`full_package_price`）；扩展 `bookings` 表支持课程预约类型（新增 `booking_type`、`course_id`、`lesson_ids`、`schedule_type` 字段，`seat_id` 改为可空）
- **新增课程预约 API**：在 br-server 新增课程预约路由和服务，支持获取课程课时列表、创建课程预约订单（含全套优惠计算）、课程订单支付与取消
- **新增课程预约页面**：在 br-app 新增 `pages/training/course-booking.vue` 页面，严格参考 `prototype/course-booking.html` 原型，包含预约类型切换、课时多选、全套课时一键选择与优惠价格、优惠券选择、支付方式选择、价格实时计算
- **扩展订单列表**：修改 `pages/orders/index.vue`，支持展示课程预约订单，显示课程名称、课时信息等差异化内容

## Capabilities

### New Capabilities

- `course-booking-api`: 课程预约后端 API —— 课时列表查询、课程预约下单（含固定班课/1V1/全套课时优惠定价逻辑）、课程订单支付与取消
- `course-booking-ui`: 课程预约前端页面 —— 参考高保真原型实现课时选择、全套课时展开、优惠价格展示、优惠券与支付选择、下单确认的完整流程

### Modified Capabilities

- `booking-payment`: 扩展支付流程以支持课程预约订单的创建、支付确认与取消退款

## Impact

- **后端**（br-server）：新增 `app/api/routes/course_booking.py` 路由、`app/services/course_booking_service.py` 服务、`app/schemas/course_booking.py` 数据模型；修改 `app/models/booking.py` 和 `app/models/course.py`；新增 Alembic 数据库迁移
- **前端**（br-app）：新增 `pages/training/course-booking.vue` 页面、`api/courseBooking.js` 接口模块；修改 `pages/orders/index.vue` 订单列表页、`pages.json` 路由注册
- **复用依赖**：复用现有优惠券系统（coupon）、钱包/微信支付（wallet/wechat-payment）、用户认证（auth）
- **回滚方案**：通过 feature flag 关闭课程预约入口；Alembic migration 提供 downgrade 路径；前端页面独立可删除，不影响现有自习室预约功能

```

## openspec/changes/course-booking/design.md

- Source: openspec/changes/course-booking/design.md
- Lines: 1-120
- SHA256: 97e424e3e51ee9690d8c0c9e3bfff3bfbab597211f33b21fa6834f1a32d54dd4

[TRUNCATED]

```md
## Context

现有预约系统围绕自习室座位设计：`Booking` 模型通过 `seat_id` + `room_id` + 时段创建预约。`Course` 和 `CourseLesson` 模型已存在但仅用于展示。需要在不破坏现有自习室预约的前提下，扩展 bookings 表支持课程预约类型，新增课程预约 API 和前端页面。

约束：
- bookings 表 `seat_id` 当前为 NOT NULL，需改为 nullable 以支持课程预约（无 seat）
- 订单列表页需同时展示两种预约类型，通过 `booking_type` 区分渲染逻辑
- 支付、优惠券、钱包基础设施完全复用

## Goals / Non-Goals

**Goals:**
- 扩展数据模型支持课程预约（booking_type、course_id、lesson_ids）
- 实现课程预约 API（课时查询、下单、支付、取消）
- 实现课程预约前端页面（参考原型图）
- 订单列表支持展示课程预约订单（差异化信息展示）
- 全套课时优惠定价逻辑

**Non-Goals:**
- 不实现 1V1 排课管理后台功能（仅前端 UI 切换展示）
- 不修改自习室座位预约的现有逻辑
- 不实现教师端课程管理
- 不实现课程评价/评分功能

## Decisions

### 决策 1：扩展 Booking 模型 vs 新建 CourseBooking 表

**选择**：扩展现有 `bookings` 表，新增 `booking_type`、`course_id`、`lesson_ids`、`schedule_type` 字段，`seat_id` 改为 nullable。

**理由**：
- 用户要求课程预约订单出现在同一订单列表页，共用 bookings 表可直接复用列表查询、支付、取消等逻辑
- 避免维护两套订单系统，降低复杂度
- 支付、优惠券、退款流程天然共享

**替代方案**：新建 `course_bookings` 表 → 需要 duplicating 大量支付/取消/列表逻辑，维护成本高

### 决策 2：课程定价字段存储位置

**选择**：在 `courses` 表新增 `custom_price`（1V1 单价）和 `full_package_price`（全套优惠价）字段。

**理由**：
- 定价与课程强关联，存储在 courses 表最直接
- 前端加载课程详情时一次性获取所有定价信息，无需额外请求

**替代方案**：新建 `course_pricing_rules` 表 → 过度设计，当前定价规则简单

### 决策 3：lesson_ids 存储方式

**选择**：在 `bookings` 表新增 `lesson_ids` 字段，使用 PostgreSQL `ARRAY(Integer)` 类型存储选中的课时 ID 列表。

**理由**：
- 课时选择是课程预约的核心信息，需要持久化
- ARRAY 类型在 PostgreSQL 中查询高效
- 避免新建关联表（booking_lessons）增加查询复杂度

**替代方案**：JSON 字符串存储 → 类型不安全，查询不便；关联表 → 过度设计

### 决策 4：前端页面路由设计

**选择**：新增 `pages/training/course-booking.vue` 独立页面，从课程详情页跳转进入。

**理由**：
- 课程预约流程复杂（课时选择、价格计算、优惠券、支付），独立页面更清晰
- 与现有 `pages/booking/confirm.vue`（自习室预约确认页）解耦，避免相互影响
- 复用 `pages/orders/index.vue` 订单列表展示

### 决策 5：课程预约 API 路由设计

**选择**：新增 `POST /api/v1/course-bookings` 独立路由，不复用 `POST /api/v1/bookings`。

**理由**：
- 课程预约请求参数（course_id、lesson_ids、schedule_type）与自习室预约（seat_id、date、start_time、end_time）完全不同
- 独立路由逻辑更清晰，避免在现有 booking 创建逻辑中增加大量条件分支
- 底层共享 Booking 模型和支付/取消服务

## Risks / Trade-offs

- **[bookings 表 seat_id nullable]** → 迁移时保持现有数据不变（已有记录 seat_id 都有值），新代码中自习室预约仍强制传 seat_id，课程预约不传。通过 booking_type 区分验证逻辑。
- **[ARRAY 类型兼容性]** → PostgreSQL ARRAY 类型在 uni-app 前端序列化为 JSON 数组，需确保 API 层正确处理。→ 缓解：Pydantic schema 使用 `list[int]` 类型。

```

Full source: openspec/changes/course-booking/design.md

## openspec/changes/course-booking/tasks.md

- Source: openspec/changes/course-booking/tasks.md
- Lines: 1-64
- SHA256: 6bee3c6b58e5e59be48aed7fa7e2ab5591c583e39a9f8abb01f1e4e3edb654fb

```md
# 课程预约功能 - 任务清单

## 1. 数据库模型与迁移

- [ ] Task 1.1: 扩展 Course 模型 — 新增 `custom_price`（Numeric(10,2)）和 `full_package_price`（Numeric(10,2), nullable）字段
- [ ] Task 1.2: 扩展 Booking 模型 — 新增 `booking_type`（String(20), default='seat'）、`course_id`（Integer, FK→courses, nullable）、`lesson_ids`（ARRAY(Integer), nullable）、`schedule_type`（String(20), nullable）字段；`seat_id` 改为 nullable
- [ ] Task 1.3: 生成 Alembic 迁移文件并验证迁移执行

## 2. 后端 Schema 定义

- [ ] Task 2.1: 创建 `app/schemas/course_booking.py` — 定义 `CourseBookingCreate`（course_id, booking_type, lesson_ids, schedule_type, payment_method, coupon_id）、`CourseBookingResponse`、`CourseLessonItem`（id, title, duration_minutes, sort_order, status）
- [ ] Task 2.2: 更新 `app/schemas/course.py` — `CourseResponse` 和 `CourseDetailResponse` 增加 `custom_price`、`full_package_price` 字段

## 3. 后端服务层

- [ ] Task 3.1: 创建 `app/services/course_booking_service.py` — 实现 `get_course_lessons(course_id)` 查询课时列表
- [ ] Task 3.2: 实现 `create_course_booking()` — 验证课程/课时、计算价格（固定/1V1/全套优惠）、验证优惠券、创建 booking 记录、处理余额支付
- [ ] Task 3.3: 实现课程预约微信支付集成 — 复用 `booking_payment_service.py` 的微信支付创建和回调逻辑，确保支持 course booking_type
- [ ] Task 3.4: 实现课程预约取消 — 复用现有取消退款逻辑，增加优惠券恢复逻辑

## 4. 后端 API 路由

- [ ] Task 4.1: 创建 `app/api/routes/course_booking.py` — `GET /api/v1/courses/{course_id}/lessons`（课时列表）、`POST /api/v1/course-bookings`（创建课程预约）
- [ ] Task 4.2: 扩展 `app/api/routes/booking.py` — 列表接口返回数据增加 `course_name`、`lesson_titles`、`booking_type` 字段；取消接口支持课程预约优惠券恢复
- [ ] Task 4.3: 在 `app/main.py` 注册 course_booking 路由

## 5. 后端测试

- [ ] Task 5.1: 编写 `tests/test_course_booking_service.py` — 测试价格计算逻辑（固定/1V1/全套优惠）、课时验证、优惠券验证
- [ ] Task 5.2: 编写 `tests/test_api_course_booking.py` — 集成测试课时查询、创建预约（余额/微信）、取消预约

## 6. 前端 API 模块

- [ ] Task 6.1: 创建 `br-app/src/api/courseBooking.js` — 封装 `getCourseLessons(courseId)`、`createCourseBooking(data)`、`getCourseBookingCoupons(courseId)` 接口

## 7. 前端课程预约页面

- [ ] Task 7.1: 创建 `br-app/src/pages/training/course-booking.vue` — 页面骨架 + 课程信息摘要区域（封面、名称、教师、单价）
- [ ] Task 7.2: 实现预约类型切换组件（固定班课/1V1 双列卡片，选中态切换，价格联动）
- [ ] Task 7.3: 实现课时多选组件（课时列表、checkbox 选中/取消、已选计数、价格实时更新）
- [ ] Task 7.4: 实现全套课时展开功能（"查看全套"推广条、点击全选、优惠价格展示、toast 提示）
- [ ] Task 7.5: 实现上课时间展示区域（固定班课时间表 / 1V1 日期时段选择器切换）
- [ ] Task 7.6: 实现优惠券选择（复用现有优惠券弹窗逻辑）
- [ ] Task 7.7: 实现支付方式选择（余额/微信 radio 切换，余额不足检测）
- [ ] Task 7.8: 实现价格摘要与底部操作栏（课程费明细、优惠券抵扣、实付金额、立即支付按钮）
- [ ] Task 7.9: 实现下单与支付流程（余额支付直接下单 / 微信支付调起 + 轮询结果 + 成功弹窗 + 跳转订单页）

## 8. 前端订单列表扩展

- [ ] Task 8.1: 修改 `br-app/src/pages/orders/index.vue` — 订单卡片根据 `booking_type` 区分渲染：课程预约显示课程名称+课时信息（替代门店名+座位信息）
- [ ] Task 8.2: 课程预约订单操作按钮适配（待支付→去支付/取消，已确认→取消，已完成→再来一单）

## 9. 前端入口与路由注册

- [ ] Task 9.1: 在 `br-app/src/pages.json` 注册 `pages/training/course-booking` 路由
- [ ] Task 9.2: 修改 `br-app/src/pages/training/course-detail.vue` — 添加"立即预约"按钮，跳转到课程预约页

## 10. 已知问题规避（参考 bug-fixed.md）

- [ ] Task 10.1: 确保 `onMounted` 从 `vue` 导入而非 `@dcloudio/uni-app`（BUG-14）
- [ ] Task 10.2: 确保不在 `<style>` 中使用 `@import '@/uni.scss'`（BUG-1）
- [ ] Task 10.3: 确保 WXML 中不使用 `<` `>` 字符，使用 Unicode 替代（BUG-20）
- [ ] Task 10.4: 确保 API 路由定义不带尾部斜杠（BUG-22）
- [ ] Task 10.5: 确保 datetime 字段使用 naive datetime（Asia/Shanghai），不混用 aware/naive（BUG-15）

```

## openspec/changes/course-booking/specs/booking-payment/spec.md

- Source: openspec/changes/course-booking/specs/booking-payment/spec.md
- Lines: 1-101
- SHA256: 6738a5724fbd024f8f5dfe25beacaf3e4314482c49577ecf6bb0186c7a010d07

[TRUNCATED]

```md
## MODIFIED Requirements

### Requirement: Booking payment with balance
系统 SHALL 在用户选择"账户余额"时，使用现有余额扣款逻辑创建预约，行为与改造前一致。此逻辑同时适用于自习室座位预约和课程预约订单。

#### Scenario: Pay with sufficient balance
- **GIVEN** 用户选择"账户余额"且余额充足
- **WHEN** 用户点击"立即支付"
- **THEN** 系统创建预约并扣除余额
- **AND** 预约 `payment_method='balance'`、`payment_status='paid'`
- **AND** 显示预约成功弹窗

#### Scenario: Pay with insufficient balance
- **GIVEN** 用户选择"账户余额"且余额不足
- **WHEN** 用户点击"立即支付"
- **THEN** 系统返回余额不足错误
- **AND** 显示"余额不足，请切换微信支付或先充值"提示

#### Scenario: Pay course booking with balance
- **GIVEN** 用户在课程预约页面选择"账户余额"且余额充足
- **WHEN** 用户点击"立即支付"
- **THEN** 系统创建课程预约 booking 记录并扣除余额
- **AND** 预约 `booking_type='course'`、`payment_method='balance'`、`payment_status='paid'`
- **AND** 显示课程预约成功弹窗

### Requirement: Booking payment with WeChat Pay
系统 SHALL 在用户选择"微信支付"时，创建 pending 状态的预约并返回微信 JSAPI 支付参数。此逻辑同时适用于自习室座位预约和课程预约订单。

#### Scenario: Create booking with WeChat payment
- **GIVEN** 用户选择"微信支付"且微信支付配置可用
- **WHEN** 用户点击"立即支付"
- **THEN** 系统创建预约，`payment_method='wechat'`、`payment_status='pending'`
- **AND** 系统调用微信支付 JSAPI 下单获取 `prepay_id`
- **AND** 返回 201，响应包含 `payment_params`（timeStamp、nonceStr、package、signType、paySign）
- **AND** 前端使用 `payment_params` 调用 `uni.requestPayment`

#### Scenario: Create course booking with WeChat payment
- **GIVEN** 用户在课程预约页面选择"微信支付"
- **WHEN** 用户点击"立即支付"
- **THEN** 系统创建课程预约 booking，`booking_type='course'`、`payment_status='pending'`
- **AND** 调用微信支付 JSAPI 下单
- **AND** 返回 `payment_params` 供前端唤起微信支付

### Requirement: Booking WeChat payment callback
系统 SHALL 提供 `POST /api/v1/bookings/wechat/notify` 处理微信支付订单的异步通知，支付成功后确认预约。回调处理 MUST 同时支持自习室预约和课程预约订单。

#### Scenario: Process successful course booking payment notification
- **GIVEN** 存在 `booking_type='course'` 且 `payment_status='pending'` 的课程预约
- **WHEN** 微信支付发送签名有效、金额匹配、`trade_state='SUCCESS'` 的通知
- **THEN** 系统更新预约 `payment_status='paid'`、`paid_at`、`transaction_id`
- **AND** 返回微信要求的成功响应

### Requirement: Booking cancellation refund settlement
系统 SHALL 在已支付预约取消成功时，将可退金额退回用户钱包，并记录扣款金额、退款金额和退款流水。退款金额 SHALL 基于预约 `total_price` 计算。余额支付和微信支付预约取消后均退回钱包余额。课程预约取消时，已使用的优惠券 MUST 恢复为可用状态。

#### Scenario: Refund based on paid amount
- **GIVEN** 预约 `original_price=120.00`、`discount_amount=20.00`、`total_price=100.00`
- **AND** 当前取消规则扣 10%
- **WHEN** 用户取消预约
- **THEN** 系统按 `total_price=100.00` 计算扣款
- **AND** `penalty_amount=10.00`
- **AND** `refund_amount=90.00`

#### Scenario: Balance payment refund to wallet
- **GIVEN** 用户使用余额支付了一笔预约
- **WHEN** 用户成功取消该预约
- **THEN** 系统将可退金额加回用户钱包余额
- **AND** 创建 `type='booking_refund'` 的预约取消退款钱包流水
- **AND** 钱包流水展示标题为"取消退款"

#### Scenario: WeChat payment refund to wallet
- **GIVEN** 用户使用微信支付且预约 `payment_status='paid'`
- **WHEN** 用户成功取消该预约
- **THEN** 系统将可退金额加到用户钱包余额
- **AND** 不调用微信原路退款
- **AND** 创建 `type='booking_refund'` 的预约取消退款钱包流水
- **AND** 钱包流水展示标题为"取消退款"

#### Scenario: Course booking cancellation restores coupon
- **GIVEN** 用户使用优惠券支付了课程预约

```

Full source: openspec/changes/course-booking/specs/booking-payment/spec.md

## openspec/changes/course-booking/specs/course-booking-api/spec.md

- Source: openspec/changes/course-booking/specs/course-booking-api/spec.md
- Lines: 1-107
- SHA256: 0c65fb25b22744c0282bd9e78a9692f0f55a2aa7d690c86b0fbb33aa44188872

[TRUNCATED]

```md
## Purpose

提供课程预约后端 API，支持查询课程课时列表、创建课程预约订单（含固定班课/1V1/全套课时优惠定价）、课程订单支付与取消，复用现有优惠券和支付基础设施。

## ADDED Requirements

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

```

Full source: openspec/changes/course-booking/specs/course-booking-api/spec.md

## openspec/changes/course-booking/specs/course-booking-ui/spec.md

- Source: openspec/changes/course-booking/specs/course-booking-ui/spec.md
- Lines: 1-152
- SHA256: 53651e2449bc29e66ca2bb72bfaf305b344981de24f9e67ed1229e1fd6b29867

[TRUNCATED]

```md
## Purpose

提供课程预约前端页面，用户可在培训课程详情页进入预约流程，选择预约类型和课时，享受全套课时优惠，选择优惠券和支付方式后完成下单。UI 严格参考 `prototype/course-booking.html` 高保真原型图。

## ADDED Requirements

### Requirement: Course booking page entry
系统 SHALL 在培训课程详情页（`pages/training/course-detail.vue`）提供"立即预约"入口，点击后跳转到课程预约页面（`pages/training/course-booking.vue`），传递 `course_id` 参数。

#### Scenario: Navigate to course booking page
- **WHEN** 用户在课程详情页点击"立即预约"按钮
- **THEN** 跳转到 `/pages/training/course-booking?course_id={id}`

### Requirement: Course info summary display
页面顶部 SHALL 展示课程摘要信息，包含课程封面图、课程名称、教师名称与头像、单价。UI 参照原型图 Course Info Summary 区域。

#### Scenario: Display course summary
- **GIVEN** 用户进入课程预约页面
- **WHEN** 页面加载完成
- **THEN** 顶部显示课程封面图（圆角方形）、课程名称、教师头像与姓名
- **AND** 右侧显示单价（如 ¥80/课时）

### Requirement: Booking type selection
页面 SHALL 提供两种预约类型选择：固定班课和 1V1 私人定制。以双列卡片形式展示，选中态显示蓝色边框和勾选图标。UI 参照原型图 Booking Type Selection 区域。

#### Scenario: Default booking type is fixed
- **WHEN** 页面加载完成
- **THEN** "固定班课"卡片显示选中态（蓝色边框 + 勾选图标）
- **AND** 显示固定班课时间表（如"每周二 14:00-16:00"）和单价

#### Scenario: Switch to custom 1V1
- **WHEN** 用户点击"1V1私人定制"卡片
- **THEN** "1V1私人定制"显示选中态，"固定班课"取消选中
- **AND** 单价更新为 1V1 价格（如 ¥200/课时）
- **AND** 上课时间区域切换为日期+时段选择器

#### Scenario: Switch back to fixed
- **WHEN** 用户从 1V1 切换回固定班课
- **THEN** 固定班课卡片恢复选中态
- **AND** 单价恢复为固定班课价格
- **AND** 上课时间区域显示固定时间表

### Requirement: Lesson multi-select
页面 SHALL 展示课程课时列表，每节课时显示序号、标题、时长、可预约状态和单价。用户可通过点击切换选中/取消，支持多选。UI 参照原型图 Lesson Selection 区域。

#### Scenario: Display lesson list
- **WHEN** 页面加载完成
- **THEN** 显示课时列表，每节包含 checkbox、图标、标题（如"第1讲 · 马克思主义基本原理"）、时长和单价
- **AND** 头部显示"已选 N 节"计数

#### Scenario: Toggle lesson selection
- **WHEN** 用户点击一节未选中的课时
- **THEN** 该课时显示选中态（蓝色背景 + checkbox 勾选）
- **AND** "已选"计数 +1
- **AND** 底部价格实时更新

#### Scenario: Deselect a lesson
- **WHEN** 用户点击一节已选中的课时
- **THEN** 该课时取消选中态
- **AND** "已选"计数 -1
- **AND** 底部价格实时更新

### Requirement: Full package expand and discount
页面 SHALL 在课时列表底部展示"全套课时更划算"推广条。点击后展开全部课时并自动全选，显示全套优惠价格。UI 参照原型图 Full course promo 区域。

#### Scenario: Show full package promo bar
- **GIVEN** 课程有多节课时可选
- **WHEN** 课时列表渲染完成
- **THEN** 列表底部显示推广条，包含"全套N课时更划算"和"立省¥XX"以及"查看全套 →"文字链

#### Scenario: Expand all lessons with full package price
- **WHEN** 用户点击"查看全套 →"
- **THEN** 展开全部课时（如果之前只显示部分）
- **AND** 所有课时自动全选
- **AND** 显示 toast 提示"已选择全套N课时，立省¥XX"
- **AND** 价格区域显示全套优惠价格

### Requirement: Schedule display
页面 SHALL 根据预约类型显示对应的上课时间信息。固定班课显示固定时间表，1V1 显示日期+时段选择器。UI 参照原型图 Schedule 区域。


```

Full source: openspec/changes/course-booking/specs/course-booking-ui/spec.md
