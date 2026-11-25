## 1. 后端公共发送方法与默认目标（br-server）

- [x] 1.1 `NotificationService.send_notification`：类型校验、偏好过滤、按类型补默认 `target_url`；`create_notification` 委托复用
- [x] 1.2 新增 `app/utils/geo.py` Haversine 距离工具
- [x] 1.3 新增 `tests/test_notification_send.py` 覆盖偏好关闭不发送与默认目标回填

## 2. 到店提醒接口（br-server）

- [x] 2.1 `app/schemas/notification.py` 增加 `ArrivalReminderRequest` / `ArrivalReminderResponse`
- [x] 2.2 `send_arrival_reminder`：房间校验、500 米门槛、24 小时去重、发送 `到店签到提醒`
- [x] 2.3 `POST /api/v1/notifications/arrival-reminder` 路由（当前用户鉴权）
- [x] 2.4 接口测试覆盖 nearby / too_far / disabled / already_sent / room_without_coordinates / 未登录

## 3. 前端公共发送与详情页触发（br-app）

- [x] 3.1 `src/api/notifications.js` 增加 `sendArrivalReminder`
- [x] 3.2 新增 `src/utils/notification.js` 公共发送方法（未登录跳过、失败静默）
- [x] 3.3 `pages/booking/detail.vue` 定位成功且 ≤500 米时触发一次到店提醒

## 4. 验证与交付

- [x] 4.1 后端 pytest 相关用例通过
- [x] 4.2 br-app 距离单测与 mp-weixin / h5 构建通过
- [x] 4.3 消息列表点击跳转核对（target_url 优先、类型兜底）
- [ ] 4.4 提交并推送 origin main
