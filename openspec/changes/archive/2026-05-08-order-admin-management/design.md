## Context

系统已有用户端预约 API（`/api/v1/bookings`），支持创建、列表、详情、取消操作，但所有接口均绑定当前用户 `user_id`，管理员无法查看或管理全部用户的订单。

现有后台管理页面（自习室、座位、活动）遵循统一模式：
- 后端：`api/routes/admin_*.py` + service 层新增 admin 方法 + `get_current_admin` 认证
- 前端：`api/[entity]/index.ts` + `views/[entity]/list/index.vue` + `router/modules/[entity].ts`
- 表格组件：BasicTable + BasicForm + Modal

Booking 模型字段：`id, seat_id, user_id, room_id, date, start_time, end_time, status, total_price, created_at, updated_at`

## Goals / Non-Goals

**Goals:**
- 管理员可查看全部预约订单列表，支持多维度筛选
- 管理员可查看订单详情（含关联座位和自习室信息）
- 管理员可取消异常订单
- 前端页面复用现有 admin 页面模式，保持一致体验

**Non-Goals:**
- 退款功能（涉及支付系统对接，留待后续迭代）
- 订单数据导出
- 订单统计/报表
- 用户端预约功能变更

## Decisions

### 1. Admin API 独立于现有用户 API

复用现有 `booking_service.py` 新增 admin 方法（如 `admin_list_bookings`、`admin_get_booking`、`admin_cancel_booking`），不修改现有用户端方法。

**替代方案**: 在现有路由中增加 admin 参数判断 → 拒绝，职责混杂，违反单一职责原则。

**理由**: 与 activity、study_room、seat 的 admin 模式一致，独立 admin 路由文件 + service 方法，职责清晰。

### 2. 新增管理员响应 Schema

新增 `BookingAdminResponse`，在现有 `BookingResponse` 基础上增加 `user_id` 直接展示（用户端隐藏了 user_id 详情）和 `seat`/`room` 的更完整信息。

**理由**: 管理员需要看到关联的座位编号、自习室名称、用户 ID，便于定位和处理问题。

### 3. 前端仅提供列表页（无新建/编辑）

订单由用户在小程序端创建，管理员不需要在后台创建订单。因此前端仅提供列表页和操作（查看详情、取消），不需要新建和编辑表单。

**理由**: 订单的创建流程绑定了用户端选座、时间选择、支付等交互，不适合在后台复制。

### 4. 筛选维度

列表 API 支持查询参数：`status`（订单状态）、`room_id`（自习室）、`date_start` / `date_end`（日期范围）、`page` / `page_size`（分页）。

**理由**: 覆盖管理员日常处理异常订单的主要查询场景，不引入过度复杂的筛选。

### 5. 订单取消由管理员执行

管理员取消订单 API 直接将状态改为 `cancelled`，记录取消来源。不新增 `cancelled_by_admin` 字段，MVP 阶段保持简单。

**理由**: MVP 阶段保持最小实现，后续如需区分取消来源可扩展。

## Risks / Trade-offs

- **[订单量增长导致列表查询慢]** → 列表查询已按 `created_at` 降序索引，`date`、`room_id`、`status` 均有独立索引，分页限制最大 50 条。后续可加复合索引优化。
- **[管理员误操作取消订单]** → 前端取消操作需二次确认弹窗。后续可增加操作日志记录。
- **[并发取消]** → 当前使用乐观锁（检查状态后更新），MVP 阶段足够。
