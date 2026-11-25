# 任务清单

## 1. 通知服务能力

- [x] 1.1 在 `NotificationService` 中新增预约生命周期方法：支付成功、开始提醒、离店完成，统一走公共发送方法并尊重 `booking` 偏好
- [x] 1.2 为三个预约方法增加 `(user_id, type, target_type, target_id, title)` 去重查询
- [x] 1.3 新增 `broadcast_activity` 群发方法：App 用户范围、`activity` 偏好过滤、活动详情 target_url、分批写入与内容去重
- [x] 1.4 增加通知服务单元测试，覆盖消息内容、偏好过滤、去重与群发范围

## 2. 预约支付成功接入

- [x] 2.1 `booking_service.create_booking` 与 `pay_pending_booking` 余额支付成功后发送「预约成功通知」
- [x] 2.2 `course_booking_service.create_course_booking` 余额支付成功后发送「预约成功通知」
- [x] 2.3 `booking_payment_service` 微信回调与支付对账确认支付成功后发送「预约成功通知」
- [x] 2.4 增加支付成功通知的集成测试，覆盖余额与微信两条路径

## 3. 订单状态定时任务接入

- [x] 3.1 在 `order_status_scheduler` 中检测座位/课时开始时间，小于 15 分钟时发送「预约开始提醒」，课程按课时去重
- [x] 3.2 在定时任务推进状态为「已完成」时发送「离店核销完成」，核销完成与懒同步路径同样接入
- [x] 3.3 扩展定时任务与核销测试，覆盖提醒窗口、课程课时、完成通知与去重

## 4. 活动群发接入

- [x] 4.1 `activity_service.create_activity/update_activity` 在已上架且有关联卡券时调用群发方法，失败不阻断活动保存
- [x] 4.2 增加活动群发测试，覆盖已上架/未上架/无卡券/偏好关闭/重复保存场景

## 5. 验证与交付

- [x] 5.1 运行 br-server 相关 pytest 与格式检查
- [x] 5.2 检查改动范围与文档一致，确认无新增外部 API 或数据库迁移
- [x] 5.3 提交并推送 GitHub main
