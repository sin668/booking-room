# Tasks — im-message-callback-sync

## 1. br-server 基础

- [x] 1.1 `app/core/im.py`：新增 `from_im_user_id(im_user_id) -> uuid.UUID | None`；新增回调签名校验工具（`Sign = sha256(Token + RequestTime)` + 时间戳误差 < 60s）
- [x] 1.2 `app/core/config.py`：新增 `IM_CALLBACK_TOKEN`（默认为空，空时跳过 Sign 校验）
- [x] 1.3 `app/models/im_message.py`：`im_messages` 模型；`app/models/__init__.py` 与 `alembic/env.py` 注册
- [x] 1.4 alembic 迁移创建 `im_messages` 表（含 `msg_key` 唯一索引与收发账号索引）

## 2. br-server 服务与接口

- [x] 2.1 `app/services/im_callback_service.py`：解析 `C2C.CallbackAfterSendMsg` 的 `MsgBody`（text/image/sound/custom），按 `msg_key` upsert 落库
- [x] 2.2 `app/services/im_media_service.py`：下载 IM 媒体 + 复用 `get_storage_adapter()` 上传 OSS，回写 `oss_url`，失败降级保留 IM 地址
- [x] 2.3 `app/services/im_callback_service.py`：解析 `C2C.CallbackAfterMsgReport`，按 `Peer_Account/Report_Account/LastReadTime` 幂等回写已读
- [x] 2.4 `app/api/routes/im_callback.py`：回调路由（SdkAppid/Sign 校验、命令分发、立即返回 OK、后台任务写库与转存）；`app/main.py` 注册
- [x] 2.5 `app/api/routes/chat.py`：`GET /api/v1/chat/messages` 历史查询接口（登录态鉴权、仅返回本人参与的会话、limit/before 分页）

## 3. br-app 会话窗口

- [x] 3.1 `src/api/chat.js`：封装历史消息接口
- [x] 3.2 `src/TUIKit/components/TUIChat/message-list/index.vue`：进入会话拉取历史，用 `msg_key -> oss_url` 覆盖图片/语音渲染地址，请求失败不阻塞聊天

## 4. 测试与验证

- [x] 4.1 br-server 单测：回调解析（text/image/sound）、`msg_key` 幂等、已读回写与重复上报、Sign 校验、历史接口越权与未登录
- [x] 4.2 运行 `/opt/miniconda3/envs/booking-room/bin/python -m pytest` 相关用例确认通过
- [x] 4.3 `cd br-app && npm run build:mp-weixin` 构建通过

## 5. 验证阶段修复（集成审查发现）

- [x] 5.1 CRITICAL：回调鉴权改默认拒绝——`IM_CALLBACK_TOKEN` 未配置时不落库（`SdkAppid` 是公开值），补伪造签名/缺 Token 回归用例
- [x] 5.2 IMPORTANT：消息先 commit 再做媒体转存，下载异常捕获放宽到 `Exception`，转存抛异常不再回滚消息（加回归用例）
- [x] 5.3 IMPORTANT：媒体下载改流式读取 + 边读边限长（超限 `MediaTooLarge` 走降级），加限长回归用例
- [x] 5.4 IMPORTANT：前端媒体映射改按需刷新（新消息/失败重拉 + 2s 最短间隔 + 会话切换不回写），匹配键补元素类型
- [x] 5.5 回调体非对象不再 500、历史接口 `peer` 归一（大写/连字符）、`is_read` 与迁移 `server_default` 对齐
