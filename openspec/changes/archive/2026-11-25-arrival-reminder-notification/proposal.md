## Why

消息中心已支持四类系统消息的展示与点击跳转，但后端 `notifications` 表至今没有统一的发送入口，也没有任何业务节点真正写入消息，导致「到店提醒」等能力只有壳、没有消息。本次补齐公共发送方法，并让用户在到达学习室附近（≤500 米）浏览详情时自动收到一条可点击跳转的「到店签到提醒」。

## What Changes

- br-server 通知服务新增公共发送方法 `send_notification`：统一校验类型、按用户通知偏好过滤、按类型补默认 `target_url`，供后续业务节点复用。
- br-server 新增受控接口 `POST /api/v1/notifications/arrival-reminder`：基于房间坐标与用户上报坐标计算距离，≤500 米才发送 `arrival` 类型消息，同房间 24 小时内去重。
- br-app 新增公共发送消息工具与 API 封装，`pages/booking/detail.vue`（自习室 / 培训室 / 综合室共用详情页）定位成功后调用。
- br-app 消息中心点击非会话消息跳转目标链接的行为保持不变并补齐到店消息的目标地址（我的学习码页面）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `message-notification-api`: 新增公共发送方法语义与 `arrival-reminder` 接口（距离门槛、偏好过滤、24 小时去重、归属与鉴权）。
- `message-notification-ui`: 房间详情页在 500 米内自动触发到店签到提醒；非会话消息点击跳转目标链接。

## Impact

- 影响模块：
  - br-server：`app/services/notification_service.py`、`app/api/routes/notification.py`、`app/schemas/notification.py`、新增地理距离工具、`tests/`。
  - br-app：`src/api/notifications.js`、新增 `src/utils/notification.js`、`src/pages/booking/detail.vue`。
- 无数据库 schema 变更：复用 `notifications` 表现有 `target_url` / `target_type` / `target_id` 字段。
- 无新增依赖：距离计算使用服务端已有 Python 标准库实现，前端复用 `src/utils/distance.js`。

## 回滚方案

- 回滚后端：删除 `arrival-reminder` 路由与公共发送方法，消息表数据保留（仅多出 `arrival` 类型记录，不影响其他能力）。
- 回滚前端：移除详情页触发调用与公共发送工具；消息列表仍按既有 `target_url` 与类型默认目标跳转。
