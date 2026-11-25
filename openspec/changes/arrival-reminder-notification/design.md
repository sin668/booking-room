# 到店签到提醒：技术设计

## 决策记录

- 流程：本次新增一个受控后端接口，已由用户在 tweak 升级判定中明确选择「继续 tweak」，无数据库 schema 变更。
- 触发范围：仅到店签到提醒，不接入预约/活动等其他业务节点。

## 后端

### 1. 公共发送方法

`NotificationService.send_notification(data: NotificationCreate, *, respect_preferences: bool = True)`

- 校验 `type` 属于 `booking/activity/report/arrival`（复用 `_validate_type`）。
- `respect_preferences=True` 时读取用户偏好；对应类型关闭则不创建消息，返回 `None`。
- 未传 `target_url` 时按类型补默认目标：
  - `booking` → `/pages-sub/orders/index`
  - `activity` → `/pages/index/index`
  - `report` → `/pages-sub/study-record/index`
  - `arrival` → `/pages-sub/qrcode/index`
- 原有 `create_notification` 改为委托 `send_notification(..., respect_preferences=False)`，保持既有调用语义不变。

### 2. 到店提醒接口

`POST /api/v1/notifications/arrival-reminder`

请求体（`ArrivalReminderRequest`）：

```json
{ "room_id": 1, "latitude": 30.5, "longitude": 114.3 }
```

响应（`ArrivalReminderResponse`，统一 200）：

```json
{ "sent": true, "reason": null, "distance": 320.5, "notification": { ... } }
```

判定顺序（服务层 `send_arrival_reminder`）：

1. 房间不存在 → 404。
2. 房间缺少有效经纬度 → `sent=false, reason=room_without_coordinates`。
3. Haversine 距离 > 500 米 → `sent=false, reason=too_far`（附 `distance`）。
4. 该用户对 `arrival` 关闭偏好 → `sent=false, reason=disabled`。
5. 24 小时内已存在同 `target_type=room`、`target_id=<room_id>` 的 `arrival` 消息 → `sent=false, reason=already_sent`。
6. 通过 `send_notification` 创建消息：
   - `title`：`到店签到提醒`
   - `content`：`你已到达「<房间名>」附近，可前往我的学习码完成签到。`
   - `target_url`：`/pages-sub/qrcode/index`
   - `target_type`：`room`，`target_id`：`<room_id>`

距离计算放在 `app/utils/geo.py`（标准库 math 实现，与前端 `haversineDistance` 口径一致，GCJ-02 坐标）。

### 3. 鉴权

接口使用 `get_current_user_id`，只允许为当前登录用户创建消息，不接受客户端传 `user_id`。

## 前端

### 1. 公共发送消息工具

新增 `src/utils/notification.js`：

```js
export function sendNotification(type, payload)
```

- 未登录直接返回 `null`，不触发请求。
- 按类型映射到 API 方法（当前仅 `arrival` → `sendArrivalReminder`）。
- 请求失败静默处理（console.warn），不阻塞页面与不弹 toast。

### 2. 详情页触发

`src/pages/booking/detail.vue` 的 `loadRealDistance`：

- 定位成功后计算 `meters`，保持原距离文案逻辑。
- `meters !== null && meters <= 500` 时调用 `sendNotification('arrival', { room_id, latitude, longitude })`。
- 页面级 `arrivalNotified` 标记保证同一次进入只触发一次；跨次进入由后端 24 小时去重兜底。
- 未授权定位、坐标缺失、游客场景均不触发。

### 3. 消息列表跳转

- 复用既有 `openNotification` → `markNotificationRead` → `navigateToTarget` 流程。
- `target_url` 优先；缺失时按类型默认目标跳转（`arrival` → `/pages-sub/qrcode/index`）。
- 会话条目维持独立点击逻辑，不受影响。

## 验证

- 后端：新增 `tests/test_notification_send.py` 覆盖公共方法偏好过滤/默认目标，以及接口的距离、去重、缺坐标、鉴权分支。
- 前端：`npm run test:distance`、`npm run build:mp-weixin`、`npm run build:h5`。
- 项目检查命令：`.comet/check-policy.json` 中的 pytest + 双端构建。
