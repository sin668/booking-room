# Design — im-message-callback-sync

## 方案

1. **回调入口** `app/api/routes/im_callback.py`：`POST /api/v1/im/callback`，无登录态。
   - 校验 query `SdkAppid == settings.IM_SDK_APP_ID`；配置了 `IM_CALLBACK_TOKEN` 时按官方建议校验 `Sign == sha256(Token + RequestTime)`，且 `RequestTime`（毫秒）与服务器时间误差 < 60s。
   - 按 `CallbackCommand` 分发：`C2C.CallbackAfterSendMsg` 落库、`C2C.CallbackAfterMsgReport` 回写已读，其余命令直接放行。
   - 同步只做解析 + 入队，立即返回 `{"ActionStatus":"OK","ErrorInfo":"","ErrorCode":0}`；写库与媒体转存放在 `BackgroundTasks`（腾讯云回调 2s 超时）。
   - 后台任务自建 `async_session()`，不复用请求级 `get_db`（请求结束时其 session 已关闭）。
2. **表 `im_messages`**（`app/models/im_message.py`）：`id`、`msg_key`（unique，腾讯云 MsgKey）、`im_from_account`/`im_to_account`（IM UserID）、`from_user_id`/`to_user_id`（UUID，可空，FK `users.id` CASCADE）、`element_type`、`content`（Text）、`media_url`（IM/COS 原始地址）、`oss_url`、`msg_time`（秒）、`msg_seq`、`is_read`、`read_at`、`raw_payload`（JSON）、`created_at`。
   - IM UserID ↔ `users.id` 换算复用 `app/core/im.py` 的 `to_im_user_id`，新增反向 `from_im_user_id`（非法 hex 返回 None，落库只保留 IM 账号）。
   - 新模型必须在 `alembic/env.py` 注册，否则迁移生成不出表。
3. **消息解析落库** `app/services/im_callback_service.py`：取 `MsgBody` 第一个元素定 `element_type`；text 存 `Text`；image 存 `ImageInfoArray` 中 `Type==1`（原图，缺失时取首项）的 `URL`；sound 存 `Url`（注意小写 r）与 `Second`；其余存 JSON 摘要。按 `msg_key` upsert 去重。
4. **媒体转存** `app/services/im_media_service.py`：httpx 下载 IM 地址 → 复用 `app/services/upload_service.py` 的 `UploadObject` + `get_storage_adapter().upload()`，object key 形如 `chat/{image|audio}/YYYY/MM/DD/{hex}{ext}`，`oss_url` 取适配器返回的公开 URL。oss2 是同步 SDK，走 `asyncio.to_thread`。转存失败只记 warning 并保留 IM 原地址，不影响消息落库。
5. **已读回写**：`im_from_account == Peer_Account AND im_to_account == Report_Account AND msg_time <= LastReadTime AND is_read = false` → `is_read = true, read_at = now()`；天然幂等。
6. **历史查询接口** `GET /api/v1/chat/messages?peer=<imUserID>&limit=&before=<msg_time>`：`get_current_user_id` 鉴权，只返回 (self, peer) 双向消息，按 `msg_time` 倒序取一页后正序返回。
7. **br-app**：`src/api/chat.js` 增加历史接口封装；`TUIKit/components/TUIChat/message-list/index.vue` 的 `onMessageListUpdated` 用历史接口返回的 `msg_key -> oss_url` 覆盖图片/语音元素的 URL。

## 取舍

- **落库通道只用腾讯云服务端回调**（用户已确认），不做客户端上报，避免两套写入与可信度分歧。
- **原生消息类型照发，服务端另存 OSS 副本**（用户已确认）：不引入自定义消息，客户端渲染管线不变；顺带把媒体域名换成 OSS，缓解小程序 COS 域名白名单问题。
- **"打开会话优先读库"落为数据覆盖，不重建 TUIKit 消息列表**：`messageList.value` 每次都被引擎事件整体替换，伪造消息对象在小程序端极易出问题（见 `br-app/bug-fixed.md` 的 TUIKit 坑合集）。渲染源仍是 SDK，数据库提供 OSS 地址与已读数据。

## 运维（不在本次代码内）

腾讯云 IM 控制台需配置回调 URL 与 Token，并启用「发单聊消息之后回调」「单聊消息已读上报后回调」；`.env` 补 `IM_CALLBACK_TOKEN`。

## 实现约束（来自 br-app/bug-fixed.md）

不改全局 `.icon` 样式；不给 auto-height textarea 加 padding/height；不引入动态 `import()`；小程序端不用 `Set`；`sendAudioMessage` 不靠 `.then()` 链处理失败；新增富媒体域名要同步小程序 `uploadFile/downloadFile` 白名单。
