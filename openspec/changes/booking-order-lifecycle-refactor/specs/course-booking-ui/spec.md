## MODIFIED Requirements

### Requirement: Course booking order display in order list
订单列表页（`pages/orders/index.vue`）SHALL 支持展示课程预约订单，与自习室预约订单共存。课程预约订单展示差异化的信息。

状态标签 SHALL 使用新词表，与自习室预约共用 `constants/booking.js` 的 `BOOKING_STATUS_LABELS` 单一映射：待确认（`pending_confirm`）/待开始（`pending_start`）/进行中（`in_progress`）/已完成（`completed`）/已取消（`cancelled`）。「待支付」不由 `status` 派生，而由 `payment_status='pending'` 派生（详见 `study-room-booking-ui` 的 My bookings list page）。映射表中旧词表键 `pending` 与 `confirmed` SHALL 被删除。

课时高亮区块的可见性判定 SHALL 直接引用 `order.status`：`in_progress` 时展示高亮课时（`highlighted_lesson_id`）或最近课时，`pending_start` 时展示课时展开开关。原基于 `displayStatus(order)` 的三处判定 SHALL 随该派生函数一并移除。

课程订单的操作按钮判定（"查看课程"）SHALL 覆盖 `in_progress`、`pending_start`、`pending_confirm` 三种状态且 `payment_status !== 'pending'`，原判定中对旧词表 `confirmed` 与 `in_progress` 的重复比较 SHALL 收敛为对新词表的一次判定。

`time_slots` 的**展示文案**属 br-app 自身职责，SHALL 保持现有实现（1-based 的 `COURSE_WEEKDAY_NAMES` 查表、口语化输出如「每周三 14:00上课」、「工作日 14:00上课」、旧版纯文本原样返回），SHALL NOT 为与 br-admin 统一文案而改变输出；仅 JSON **数据契约**（`weekday` 取值 1-7、`time_slot` 为 `HH:MM-HH:MM`）与后端统一。

#### Scenario: Display course booking in order list
- **GIVEN** 用户有课程预约订单
- **WHEN** 用户进入订单列表页
- **THEN** 课程预约订单卡片显示课程名称（替代门店名）
- **AND** 显示课时信息（如"第1讲 · 共3课时"替代座位信息）
- **AND** 显示上课时间和价格
- **AND** 状态标签与自习室预约共用同一映射表（待支付/待确认/待开始/进行中/已完成/已取消）

#### Scenario: Course booking order actions
> 标题沿用主 spec 原名（MODIFIED 整块替换语义要求）。主 spec 该 Scenario 的“`pending` 状态”指**待支付**（`payment_status='pending'`），与订单状态重命名无关；重构后该判定 SHALL 明确依据 `payment_status` 而非 `status`。
- **GIVEN** 课程预约订单 `status='pending_start'` 且 `payment_status='pending'`（待支付）
- **WHEN** 订单卡片渲染操作按钮
- **THEN** 显示"去支付"和"取消"按钮，行为与自习室预约一致
- **AND** 该判定 SHALL 依据 `payment_status` 而非 `status`

#### Scenario: Course booking order actions for pending-confirm booking
- **GIVEN** 课程预约订单 `status='pending_confirm'`（1V1 定制待管理员确认）且已支付
- **WHEN** 订单卡片渲染操作按钮
- **THEN** 显示"查看课程"与"取消"按钮
- **AND** SHALL NOT 显示"去支付"按钮

#### Scenario: Course booking order actions for in-progress booking
- **GIVEN** 课程预约订单 `status='in_progress'` 且已支付
- **WHEN** 订单卡片渲染操作按钮
- **THEN** 显示"查看课程"按钮
- **AND** SHALL NOT 显示"去支付"按钮

#### Scenario: Lesson highlight block visibility uses status directly
- **GIVEN** 课程预约订单 `status='in_progress'`
- **WHEN** 订单卡片渲染课时区块
- **THEN** 存在 `highlighted_lesson_id` 时展示高亮课时，否则展示最近课时
- **AND** 判定 SHALL 直接引用 `order.status`，SHALL NOT 经过 `displayStatus()` 派生

#### Scenario: Lesson expand toggle for pending-start booking
- **GIVEN** 课程预约订单 `status='pending_start'`
- **WHEN** 订单卡片渲染课时区块
- **THEN** 展示课时展开开关

#### Scenario: Course schedule text formatting is unchanged
- **WHEN** 课程订单渲染上课时间文案
- **THEN** br-app SHALL 保持其现有输出口径（如「每周三 14:00上课」、「工作日 14:00上课」、旧版纯文本原样返回）
- **AND** SHALL NOT 改为 br-admin 的「周三 10:00-12:00、周六 12:00-14:00」格式

#### Scenario: Mixed order list
- **GIVEN** 用户同时有自习室预约和课程预约订单
- **WHEN** 用户查看订单列表
- **THEN** 两种订单按创建时间倒序混合展示
- **AND** 各自显示差异化的信息内容
- **AND** 状态标签来自同一映射表
