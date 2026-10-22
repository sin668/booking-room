## Why

会话消息目前只存在腾讯云 IM 侧（漫游有有效期、媒体 URL 由 IM 的 COS 域名下发且不在我们掌控中），br-app 打开会话完全依赖 SDK 拉取，既无法在服务端留存会话记录，也让图片/语音资源依赖 `*.rich.my-imcloud.com`（该域名曾多次因小程序白名单问题导致发送/播放失败）。

## What Changes

- 接入腾讯云 IM **第三方回调**，由服务端在单聊消息发送后把消息落到我们的数据库（新增 `im_messages` 表）。
- 会话打开时**优先从我们的数据库加载历史消息**，注入 TUIKit 消息列表；SDK 实时消息照常追加。
- 会话中的**图片与语音消息在落库时转存到阿里云 OSS**（复用已有存储适配器），库里同时保存 IM 原始 URL 与 OSS URL，展示优先使用 OSS URL。原生消息类型不改，避免动 TUIKit 的收发链路。
- **已读状态回写**：接收方在 TUIKit 内的已读上报会触发 `C2C.CallbackAfterMsgReport`，服务端据此把对端发来的消息标记为已读。
- 新增会话历史查询 API（仅供会话双方读取自己的消息）。
- 运维动作（不在代码内）：在 IM 控制台配置回调 URL、开启两个回调开关。

## Capabilities

### New Capabilities
- `im-message-sync`: 腾讯云 IM 单聊回调接收、鉴权、消息落库、媒体转存 OSS、已读回写与会话历史查询。

### Modified Capabilities
<!-- 无：HTTP 上传入口的 scope 白名单与"仅支持图片文件"约束不变，媒体转存走服务端内部复用存储适配器，不改变 file-upload 的需求。 -->

## Impact

- br-server：新增 `app/models/im_message.py`、`app/services/im_callback_service.py`、`app/services/im_media_service.py`、`app/api/routes/im_callback.py`、`app/api/routes/chat.py` 历史查询接口；`app/core/im.py` 增加回调鉴权校验；alembic 新增一次迁移；`app/main.py` 注册路由；`app/core/config.py` 新增 `IM_CALLBACK_TOKEN`。
- br-app：`src/TUIKit/components/TUIChat/` 会话打开时拉取并注入数据库历史消息；图片/语音元素展示优先使用 OSS URL；新增 `src/api/chat.js` 历史查询封装。
- 依赖与配置：腾讯云 IM 控制台「第三方回调」需配置公网可达的 br-server 地址并开启 `发单聊消息之后回调`、`单聊消息已读上报后回调`。
- 风险：回调有 2 秒超时，媒体下载与上传必须在响应之后的后台任务里做；转存失败时保留 IM 原始 URL 兜底。
