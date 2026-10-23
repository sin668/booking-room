## Why

腾讯云 IM 单聊消息在云端只漫游 7 天（体验版/专业版免费漫游时长均为 7 天，延长属增值服务），TUIKit 聊天窗口的历史分页完全依赖 SDK 的 `getMessageList`，所以用户往上翻最多只能看到 7 天内的消息，更早的会话在窗口里直接消失。本系统已经通过 `C2C.CallbackAfterSendMsg` 把单聊消息全量镜像进 `im_messages`（含唯一的 `msg_key`），数据是齐的，只是聊天页没有用它。

同时，上一期为绕开「IM 的 COS 域名不在小程序白名单」而加的 `applyChatMediaUrls`/`loadChatMediaMap`，只是为了给 SDK 消息换一张 OSS 图片/语音地址：它按「秒 + 收发方向 + 元素类型」模糊匹配、带节流重试缓存，逻辑复杂且和消息真实主键无关。既然现在要按消息记录重建 SDK 消息，媒体地址自然来自记录自己的 `oss_url`，这套模糊替换应当删除。

## What Changes

- **br-server**：`im_messages` 增加 `cloud_custom_data`、`is_revoked`、`revoke_time`；落库时保存回调体里的 `CloudCustomData`；新增处理 `C2C.CallbackAfterMsgWithDraw` 撤回回调，按 `MsgKey` 标记撤回；`GET /api/v1/chat/messages` 返回重建消息所需的完整字段（`MsgBody` 元素、`cloud_custom_data`、`is_revoked`、`msg_seq`、收发账号、`is_read`、`media_url`/`oss_url`）。
- **br-app**：新增按 SDK 消息结构重建历史消息的模块，把数据库记录还原成 TUIKit 可渲染的消息对象（`ID` 用 `msg_key`，携带 `payload`、`status`、`isRevoked`、`needReadReceipt`、`readReceiptInfo`/`isPeerRead`、`cloudCustomData`）；聊天页在 SDK 漫游窗口耗尽后继续向数据库翻页补齐更早的历史，通过引擎 `updateMessageList(..., 'unshift')` 注入（按 ID 去重、前插并排序，且不触发已读上报）。
- **删除**：`loadChatMediaMap` / `applyChatMediaUrls` 及其 `message-list` 调用点、回归脚本 `verify-chat-media-map.js` 与对应 npm 脚本。
- **不做**：不给超出撤回时限的深历史消息增加操作门禁（撤回/删除/转发点击仍走 SDK，失败静默），不改会话列表与未读红点逻辑，不引入新的回调命令以外的写入来源。

## Capabilities

### New Capabilities

（无新增 capability，本次只改 `im-message-sync`）

### Modified Capabilities

- `im-message-sync`: 历史查询接口需返回消息重建字段；新增撤回回调落库与「按 SDK 结构重建深历史」要求；移除「用数据库地址覆盖媒体渲染地址」要求。

## Impact

- 数据库：`im_messages` 三列新增（alembic 迁移，可空/有默认值，不回填历史数据）。
- 服务端：`app/models/im_message.py`、`app/services/im_callback_service.py`、`app/api/routes/im_callback.py`、`app/api/routes/chat.py`、`tests/test_im_callback_sync.py`。
- 客户端：`br-app/src/utils/im.js`、`br-app/src/utils/im-history.js`（新增）、`br-app/src/TUIKit/components/TUIChat/message-list/index.vue`、`br-app/package.json`、`br-app/scripts/`。
- 部署：远端需 `alembic upgrade head` 并发布后端；IM 控制台需额外勾选「单聊消息撤回后回调」，否则撤回状态不会同步。
- 依赖：不新增第三方依赖。
