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

腾讯云 IM 控制台需配置回调 URL 与 Token，并启用「发单聊消息之后回调」「单聊消息已读上报后回调」；`.env` 必须配置 `IM_CALLBACK_TOKEN`（与控制台一致），否则回调接口一律拒绝处理、不落库。

## 验证阶段修复

集成审查发现 1 个 CRITICAL + 3 个 IMPORTANT，均已修复：

1. **回调鉴权改为默认拒绝**：`SdkAppid` 由 `/api/v1/chat/user-sig` 下发给客户端，是公开值，只校验它等于回调接口无鉴权——任何人都能伪造回调写库，并借 `fetch_and_upload` 让服务端去抓任意 URL（SSRF，且下载结果会经历史接口回显）。因此未配置 `IM_CALLBACK_TOKEN` 时直接拒绝处理（仍返回 OK 不影响 IM）。签名可信来源确立后，媒体地址由腾讯云服务端生成、不是用户可控输入，SSRF 入口随之关闭。
2. **消息先提交再转存**：原实现把转存夹在同一次 commit 前，而 `httpx.InvalidURL` 不是 `httpx.HTTPError` 子类（实测 MRO 只到 `Exception`），畸形地址会让整条消息回滚丢失。改为消息 commit 后另起一次更新写 `oss_url`，并把下载异常捕获放宽到 `Exception`。注意 commit 会过期 ORM 实例，转存所需的 `id/kind/media_url` 必须在 commit 前取成标量（项目已知的 async MissingGreenlet 坑）。
3. **流式限长**：原实现先 `response.content` 全量进内存再比 10MB，上限无效。改为 `client.stream` + `aiter_bytes` 边读边累加，超限抛 `MediaTooLarge` 走降级路径。
4. **媒体映射按需刷新**：原实现把 `msg_key -> oss_url` 映射按会话缓存在模块变量里且永不失效，重新进入同一会话不再请求，新增消息也拿不到 OSS 地址。改为「列表中出现比上次快照更新的消息 / 上次请求失败」时重新拉取，并加 2 秒最短间隔避免每次消息事件都打接口；并发切会话时只回写仍匹配的会话，返回本次构建的局部映射。

同时修掉的正确性问题：回调体顶层是数组时 `.get` 抛 500（加 `isinstance` 判断，保持返回 OK）、历史接口 `peer` 未归一（大写/带连字符会漏查）、匹配键缺元素类型（同秒同向的图片与语音会互相错配）、模型 `is_read` 与迁移的 `server_default` 不一致。

**已接受的非关键偏差**（保留原因）：

- 前端仍只覆盖 `imageInfoArray[0]`（引擎渲染取该下标），不覆盖缩略图等其他档位：其余档位保留 IM 地址，避免把缩略图换成原图体积；覆盖只改 `payload` 上的地址、不重建消息对象，是「数据覆盖而非重建」既定取舍的必然结果。
- 并发同 `MsgKey` 的重复回调靠 `msg_key` 唯一索引兜底，`save_send_msg_callback` 不做 `IntegrityError` 吞异常：重复投递只会多一条 exception 日志，且测试会话被复用（fixture 只 flush 不 commit），在共享会话里 `rollback` 会连带丢弃夹具数据。
- 后台任务测试仍复用 `db_session` 替身（`_SessionScope`），未覆盖真实独立会话的连接行为。

## 实现约束（来自 br-app/bug-fixed.md）

不改全局 `.icon` 样式；不给 auto-height textarea 加 padding/height；不引入动态 `import()`；小程序端不用 `Set`；`sendAudioMessage` 不靠 `.then()` 链处理失败；新增富媒体域名要同步小程序 `uploadFile/downloadFile` 白名单。
