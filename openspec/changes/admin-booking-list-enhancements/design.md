# Design: admin-booking-list-enhancements

## 总体说明

后端扩展现有 `admin_get_booking` / `admin_cancel_booking`，不新增路由；前端在 `/booking/list` 页面新增详情弹窗组件并调整操作列逻辑。

## 1. 订单详情聚合（需求 1）

**Schema**（`br-server/app/schemas/booking.py`）：

- `BookingAdminResponse` 新增列表级字段：`booking_type`、`schedule_type`、`time_slots`（原始 JSON 字符串，前端格式化展示）。
- 新增 `BookingAdminDetailResponse`（继承 `BookingAdminResponse`），补充关联信息：
  - `user`：`user_id` / `nickname` / `phone` / `avatar`（users 表）
  - `course`：`id` / `name` / `category`（courses 表，仅课程订单）
  - `teacher`：`id` / `name`（teachers 表，取 `booking.teacher_id`，为空时回退排课 `teacher_id`）
  - `schedule`：`id` / `start_date` / `end_date` / `schedule_type` / `schedule_status` / `time_slots`（course_schedules 表，按 `booking.schedule_id`）
  - `lesson_schedules`：课时列表，含 `lesson_title` / `lesson_date` / `lesson_time_slot` / `sort_order`（lesson_schedules JOIN course_lessons）
  - `coupon`：`id` / `name` / `discount`（booking.coupon_id → user_coupons → coupons）
  - `refund_transaction`：钱包退款流水（wallet_transactions 中 `booking_id` + `type='booking_refund'`，取 `amount` / `balance_after` / `created_at`）
  - 订单自身补充字段：`lesson_ids`、`schedule_id`、`teacher_id`、`prepay_id`、`transaction_id`、`payment_check_count`

**Service**（`admin_get_booking`）：沿用现有"手动逐表查询 + 纯 Pydantic 组装"模式，禁止返回带懒加载 relationship 的 ORM 对象（参照 BUG-16 MissingGreenlet 教训与 ORM 序列化陷阱）。列表接口 `_build_admin_booking_response` 同步补充 3 个新字段。

**前端**：`handleView` 改为调用 `getBookingDetail(id)` 拉取完整详情，打开新组件 `BookingDetailModal.vue`，使用 `n-descriptions` 分区展示：订单基本信息 / 用户信息 / 自习室与座位 / 课程与排课 / 课时安排 / 价格与支付 / 取消与退款。非对应预约类型的区块显示占位文本或不渲染。

## 2. 自习室订单隐藏取消按钮（需求 2）

前端操作列：`取消` 按钮仅在 `booking_type === 'course'` 且 `status ∈ ('pending', 'pending_confirm')` 时显示。自习室（`seat`）订单不显示取消按钮。`确认` 按钮逻辑不变。

## 3. 时段列展示 time_slots（需求 3）

- 后端列表响应已含 `booking_type` 与 `time_slots`。
- 前端 `builders.ts` 的"时段"列：课程预约订单解析 `time_slots` JSON 并格式化，自习室订单保持 `start_time~end_time`。
- 格式化工具（新建于 `br-admin/src/views/booking/list/builders.ts`）：
  - 输入兼容三种历史格式：`[{"weekday": N, "time_slot": "HH:MM-HH:MM"}]`、`["HH:MM-HH:MM"]`（旧数据，缺省周几）、`{"weekday": N, "start": "HH:MM", "end": "HH:MM"}`
  - weekday 1-7 → 周一~周日（与 `ScheduleModal.vue` 的 weekdayIndexMap 语义一致，1=周一，7=周日）
  - 输出用"、"连接，如"周三 10:00-12:00、周六 12:00-14:00"；解析失败回退展示原始 `start_time~end_time`

## 4. 课程预约"待开始"订单取消（需求 4）

**后端**（`admin_cancel_booking` 新增分支，位于现有 `pending_confirm` 分支之前/整合）：

触发条件：`booking_type == 'course'` 且 `status ∈ ('pending', 'pending_confirm')`。

执行步骤（单事务）：
1. 已支付（`payment_status == 'paid'`）：全额退款——`refund_amount = total_price`、`penalty_amount = 0`、`cancel_policy = 'full_refund'`，余额退回 `user.balance`，写 `WalletTransaction(type='booking_refund')`，并恢复优惠券（复用 `coupon_service.restore_user_coupon_for_booking`）；未支付则仅改状态。
2. 状态置为 `cancelled`，写 `cancelled_at`。
3. **删除排课记录**：当 `booking.schedule_id` 存在，且不存在其他**非取消**订单引用该排课时，判定为订单专属排课，执行删除：
   - 先 `UPDATE bookings SET schedule_id = NULL WHERE schedule_id = :sid`（清除包括本订单在内的外键引用，避免 FK 约束报错）
   - `DELETE FROM lesson_schedules WHERE schedule_id = :sid`
   - `DELETE FROM course_schedules WHERE id = :sid`
   - 使用显式 SQL 删除，不触发 ORM relationship 懒加载
   - 若排课仍被其他非取消订单共享（固定班课场景），保留排课记录不删除
4. 返回前统一调用 `await admin_get_booking(db, booking_id)` 重建响应（BUG-26 教训：避免 `flush` 后对象状态问题）。

**不使用 `with_for_update()`**（BUG-26 教训：嵌套行锁导致 MissingGreenlet）。

**前端**：取消确认文案对课程订单提示"取消后将全额退款，并删除对应排课与课时记录"。

## 复用与兼容

- 复用现有 `BOOKING_STATUS_TAGS`、`createTagColumn` 等共享构建器。
- 前端类型扩展为可选字段，旧数据（自习室订单无 `time_slots`）不受影响。
- 路由权限不变：查看 `booking:view`，取消 `booking:cancel`。
