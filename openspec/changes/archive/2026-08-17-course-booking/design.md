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
- **[订单列表混合展示性能]** → 两种预约类型混合查询可能影响性能。→ 缓解：booking_type 字段加索引，列表查询优化。
- **[全套优惠价格一致性]** → 前端展示的全套优惠价需与后端一致。→ 缓解：价格统一由后端计算，前端仅展示。

## Migration Plan

1. **数据库迁移**：Alembic migration 添加 courses 表新字段（custom_price、full_package_price）和 bookings 表新字段（booking_type、course_id、lesson_ids、schedule_type），seat_id 改为 nullable
2. **后端 API**：新增 course_booking 路由和服务，注册路由
3. **前端页面**：新增 course-booking.vue 页面，修改订单列表页，注册路由
4. **灰度发布**：通过课程详情页"立即预约"按钮控制入口，可随时隐藏
5. **回滚**：Alembic downgrade 移除新字段和路由，前端移除课程预约页面

## 课程预约下单序列图

```
用户          前端(course-booking)      API              CourseBookingService     DB
 |               |                      |                      |                  |
 |-- 进入页面 -->|                      |                      |                  |
 |               |-- GET /courses/{id} -->|--- 获取课程+课时 --->|                  |
 |               |<-- 课程+课时+定价 ----|<---------------------|                  |
 |               |                      |                      |                  |
 |-- 选择课时 -->|                      |                      |                  |
 |-- 选择优惠券->|                      |                      |                  |
 |-- 点击支付 -->|                      |                      |                  |
 |               |-- POST /course-bookings -->|--- 创建订单 --->|                  |
 |               |                      |                      |-- 验证课程/课时 -->|
 |               |                      |                      |-- 计算价格       |
 |               |                      |                      |-- 验证优惠券 --->|
 |               |                      |                      |-- 创建booking -->|
 |               |                      |                      |                  |
 |               |                      |    [余额支付]         |-- 扣减余额 ----->|
 |               |                      |<-- booking_id+摘要 --|<- 更新状态 ------|
 |               |<-- 201 成功 ---------|                      |                  |
 |               |                      |    [微信支付]         |-- 创建pending -->|
 |               |                      |                      |-- 微信下单 ------>|
 |               |                      |<-- payment_params ---|<- 返回prepay_id -|
 |               |<-- 201 支付参数 -----|                      |                  |
 |               |-- uni.requestPayment -->                    |                  |
 |               |<-- 支付成功 ---------|                      |                  |
 |-- 成功弹窗 -->|                      |                      |                  |
```
