## 设计概述

在 `NotificationService` 内新增预约生命周期与活动群发方法，业务服务只负责在正确的状态转换点调用，不重复实现消息拼装、偏好过滤和去重。

## 实现要点

### 1. 预约类通知（`booking`）

新增三个方法，内部统一走 `send_notification(respect_preferences=True)`：

- `notify_booking_paid(booking)`：title「预约成功通知」。
- `notify_booking_start_soon(booking, lesson=None)`：title「预约开始提醒」。
- `notify_booking_completed(booking)`：title「离店核销完成」。

内容按订单类型生成：

- 座位预约：读取 `StudyRoom.name`，content 包含学习室名称与使用时段。
- 课程预约：读取 `Course.name`，提醒场景附带课时开始时间。

目标信息统一 `target_type="booking"`、`target_id` 为订单 ID（课程提醒为 `订单ID-课时ID`），未显式传入时 `target_url` 使用默认订单列表 `/pages-sub/orders/index`。

去重规则：发送前按 `(user_id, type, target_type, target_id, title)` 查询已存在通知，存在则跳过，保证定时任务反复扫描、支付回调重试和核销/懒同步多路径下同一事件只发送一次。

### 2. 触发点

- 支付成功：`booking_service.create_booking`（余额）、`booking_service.pay_pending_booking`（余额）、`course_booking_service.create_course_booking`（余额）、`booking_payment_service.process_wechat_notify`（微信回调）、`booking_payment_service._apply_query_result`（支付对账）。
- 开始提醒：`order_status_scheduler.check_and_update_order_statuses` 中，对已支付的自习室订单使用 `date + start_time`，对课程订单使用 `LessonSchedule.lesson_date + lesson_time_slot` 起始时间，落在 `(now, now+15min]` 区间时发送；课程按课时去重。
- 完成通知：`order_status_scheduler` 状态推进为 `completed` 时、`booking_verification_service.confirm_verification` 核销后状态为 `completed` 时、`booking_service` 懒同步完成时。

### 3. 活动群发（`activity`）

`NotificationService.broadcast_activity(activity)`：

- 仅在 `activity.is_active` 且存在关联券（`ActivityCoupon`）时由 `activity_service.create_activity/update_activity` 调用。
- 接收人：`user_source='app'` 且状态非 `deleted` 的用户；按 `notification_preferences.activity_enabled` 过滤（无偏好记录视为开启）。
- 内容：title = `activity.title`，content = `activity.description or activity.title`，target_url = `/pages-sub/activity/detail?id={activity.id}`，`target_type="activity"`，`target_id` 为活动 ID。
- 去重：同一活动、相同 title/content 已存在群发记录时跳过，避免重复保存产生全量重复消息。
- 写入按 500 条分批 `insert`，避免逐条 flush 造成大用户量下的性能问题。

### 4. 事务边界

通知写入与业务状态变更处于同一数据库事务：支付回调、定时任务、活动保存各自 `commit` 时一起落库；通知失败按业务异常处理，不吞掉订单/活动写入结果（定时任务内单订单异常继续处理其他订单）。

## 风险与取舍

- 定时任务默认 5 分钟扫描一次，15 分钟窗口内至少有机会命中；若服务在窗口内宕机则可能漏发，属于可接受的提醒降级。
- 活动群发按用户量线性写入，当前规模可接受；后续用户量增大时可切换为异步队列。
