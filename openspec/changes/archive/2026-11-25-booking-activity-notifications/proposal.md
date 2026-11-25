## Why

公共发送消息方法（`NotificationService.send_notification`）已在到店签到提醒中落地，但预约支付、开课提醒、订单完成和活动上架等关键业务节点仍未接入，用户无法及时获知订单进展与新活动。

## What Changes

- 预约自习室或课程支付成功时（余额支付、微信支付回调、支付对账）发送 title 为「预约成功通知」的 `booking` 消息。
- 订单状态定时任务检测自习室座位或课程课时开始时间，距开始不足 15 分钟时发送 title 为「预约开始提醒」的 `booking` 消息。
- 订单状态变更为「已完成」时（定时任务推进、核销完成）发送 title 为「离店核销完成」的 `booking` 消息。
- br-admin 新建/编辑活动保存后，若活动已上架且关联卡券，向全部 App 用户群发 `activity` 消息：title 为活动 title，content 为活动 description，target_url 为活动详情链接。
- 所有预约类消息遵循用户 `booking` 偏好，活动群发遵循 `activity` 偏好；同一订单/同一活动事件去重，避免重复提醒。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `message-notification-api`: 新增预约支付成功、开始前提醒、完成核销三类订单通知的发送规则与去重约束，以及活动群发消息的内容与投递范围。
- `activity-admin-api`: 新增活动保存（新建/编辑）时触发群发通知的行为要求。

## Impact

- 影响模块：br-server `services`（notification/booking/booking_payment/course_booking/booking_verification/order_status_scheduler/activity）与相关测试；br-app、br-admin 前端无需改动。
- API：不新增或变更外部 API；消息通过现有 `GET /api/v1/notifications` 读取。
- 数据库：复用 `notifications` 表，无 schema 迁移。
- 回滚方案：移除各业务节点对通知服务的调用即可停止发送；已写入的通知记录可按 `target_type='booking'|'activity'` 清理，不影响订单与活动数据。
