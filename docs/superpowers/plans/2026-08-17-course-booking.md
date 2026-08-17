---
change: course-booking
design-doc: docs/superpowers/specs/2026-08-17-course-booking-design.md
base-ref: 7180f81b70151a5d2881b9005459d5bde322e9c4
---

# 课程预约功能 — 实施计划

## 概述

基于 Design Doc 和 OpenSpec tasks.md，将课程预约功能拆分为可独立执行的任务。任务按依赖顺序排列：数据模型 → Schema → 服务层 → API 路由 → 测试 → 前端 API → 前端页面 → 订单列表 → 路由注册。

## 执行顺序

### Phase 1: 后端基础设施（Task 1-2）

**Task 1.1-1.3: 数据库模型与迁移**
- 修改 `br-server/app/models/course.py`：新增 `custom_price`、`full_package_price`
- 修改 `br-server/app/models/booking.py`：新增 `booking_type`、`course_id`、`lesson_ids`、`schedule_type`；`seat_id` 改 nullable
- 运行 `alembic revision --autogenerate -m "add course booking fields"` 生成迁移
- 运行 `alembic upgrade head` 验证迁移

**Task 2.1-2.2: Schema 定义**
- 创建 `br-server/app/schemas/course_booking.py`：`CourseBookingCreate`、`CourseBookingResponse`、`CourseLessonItem`
- 修改 `br-server/app/schemas/course.py`：增加 `custom_price`、`full_package_price` 到响应 schema

### Phase 2: 后端业务逻辑（Task 3-4）

**Task 3.1-3.4: 服务层**
- 创建 `br-server/app/services/course_booking_service.py`
- 实现 `get_course_with_lessons()`、`calculate_price()`、`create_course_booking()`、`cancel_course_booking()`
- 集成 `coupon_service`（验证/使用/恢复）、`wallet_service`（扣款/退款）、`booking_payment_service`（微信支付）

**Task 4.1-4.3: API 路由**
- 创建 `br-server/app/api/routes/course_booking.py`
- 实现 `GET /api/v1/courses/{course_id}/lessons`、`POST /api/v1/course-bookings`
- 修改 `br-server/app/api/routes/booking.py`：列表返回增加 `booking_type`、`course_name`、`lesson_titles`
- 修改 `br-server/app/main.py`：注册新路由

### Phase 3: 后端测试（Task 5）

**Task 5.1-5.2: 测试**
- 创建 `tests/test_course_booking_service.py`：价格计算、课时验证、优惠券验证
- 创建 `tests/test_api_course_booking.py`：集成测试（创建/支付/取消/列表）

### Phase 4: 前端实现（Task 6-9）

**Task 6.1: 前端 API 模块**
- 创建 `br-app/src/api/courseBooking.js`

**Task 7.1-7.9: 课程预约页面**
- 创建 `br-app/src/pages/training/course-booking.vue`
- 参考 `prototype/course-booking.html` 实现完整 UI
- 复用 `booking/confirm.vue` 的优惠券弹窗和支付逻辑

**Task 8.1-8.2: 订单列表扩展**
- 修改 `br-app/src/pages/orders/index.vue`：根据 `booking_type` 条件渲染课程/自习室信息

**Task 9.1-9.2: 路由注册与入口**
- 修改 `br-app/src/pages.json`：注册新路由
- 修改 `br-app/src/pages/training/course-detail.vue`：添加"立即预约"按钮

### Phase 5: 已知问题规避检查（Task 10）

- 验证所有 bug-fixed.md 中的已知问题在新代码中不重现

## 关键文件清单

| 操作 | 文件路径 |
|------|---------|
| 修改 | `br-server/app/models/course.py` |
| 修改 | `br-server/app/models/booking.py` |
| 新建 | `br-server/app/schemas/course_booking.py` |
| 修改 | `br-server/app/schemas/course.py` |
| 新建 | `br-server/app/services/course_booking_service.py` |
| 新建 | `br-server/app/api/routes/course_booking.py` |
| 修改 | `br-server/app/api/routes/booking.py` |
| 修改 | `br-server/app/main.py` |
| 新建 | `br-server/tests/test_course_booking_service.py` |
| 新建 | `br-server/tests/test_api_course_booking.py` |
| 新建 | `br-app/src/api/courseBooking.js` |
| 新建 | `br-app/src/pages/training/course-booking.vue` |
| 修改 | `br-app/src/pages/orders/index.vue` |
| 修改 | `br-app/src/pages.json` |
| 修改 | `br-app/src/pages/training/course-detail.vue` |
| 新建 | Alembic migration 文件 |
