## Why

当前 br-app 首页通知铃铛仅做展示，“我的设置”里的通知设置也只是本地开关，用户无法查看实际消息通知。需要补齐移动端消息通知前端功能，并同步提供 br-server REST 后端接口，让用户能从通知入口查看与设置中 4 类通知一致的真实消息内容。

## What Changes

- 新增 br-app 消息通知列表页面，展示 4 类通知：预约提醒、活动通知、学习报告、到店提醒。
- 首页通知铃铛从占位改为进入消息通知页面，并根据未读消息显示红点。
- 消息通知页面支持按类型筛选、未读/已读状态展示、空状态、加载/刷新和错误重试。
- 新增 br-server 消息通知 REST API，支持当前用户消息列表、未读摘要、单条已读、批量已读、通知偏好读取和保存。
- 消息通知页面尊重“我的设置”中 4 类通知开关，被关闭的类型仍可查看历史消息，但不计入首页主动未读红点，并显示已关闭提示。
- “我的设置”通知设置继续提供 4 类开关，并通过后端偏好接口与消息通知页面、首页红点保持一致。
- 不包含破坏性变更；现有首页、设置页入口保留。

## Capabilities

### New Capabilities

- `message-notification-ui`: br-app 用户消息通知中心前端能力，覆盖 4 类通知列表、筛选、未读状态、详情入口和空/错/加载状态。
- `message-notification-api`: br-server 用户消息通知 REST 能力，覆盖消息数据模型、列表分页、未读摘要、已读状态、通知偏好和用户隔离。

### Modified Capabilities

- `homepage-ui`: 首页通知铃铛从纯展示改为进入消息通知页面并显示未读提示。
- `profile-settings-ui`: 我的设置通知设置明确包含 4 类消息通知开关，并通过后端偏好接口作为消息通知页面和首页红点的类型偏好来源。

## Impact

- br-app:
  - `src/pages/index/index.vue` 首页通知铃铛入口和未读状态。
  - `src/pages/settings/index.vue` 通知设置 4 类开关的状态定义、后端保存和页面联动。
  - 新增消息通知页面、API 封装和路由配置。
- br-server:
  - 新增通知数据模型、通知偏好数据模型、schema、service、router 和数据库迁移。
  - 新增 `/api/v1/notifications`、`/api/v1/notifications/unread-summary`、`/api/v1/notifications/{id}/read`、`/api/v1/notifications/read-all`、`/api/v1/notifications/preferences` REST 接口。
  - 新增后端测试覆盖分页筛选、未读摘要、已读状态、偏好保存和跨用户隔离。
  - 更新 `docs/api.md` 记录通知 API。
- OpenSpec:
  - 新增 `message-notification-api` 规格。
  - 新增 `message-notification-ui` 规格。
  - 修改 `homepage-ui`、`profile-settings-ui` 规格。
- 回滚方案:
  - 移除新增消息通知页面与路由。
  - 首页通知铃铛恢复为占位行为。
  - 设置页通知开关保留现状，不再联动消息通知页面。
  - 移除新增 br-server 通知路由、service、schema 和数据库迁移。
