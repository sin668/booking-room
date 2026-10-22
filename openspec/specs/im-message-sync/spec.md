# im-message-sync Specification

## Purpose
把腾讯云 IM 单聊消息在服务端可信落库，并为 br-app 会话窗口提供以数据库数据（OSS 媒体地址、已读状态、历史消息）为准的展示能力。
## Requirements
### Requirement: 单聊消息服务端回调落库

系统 SHALL 提供腾讯云 IM 第三方回调接收接口 `POST /api/v1/im/callback`，处理 `C2C.CallbackAfterSendMsg` 命令，将单聊消息持久化到 `im_messages` 表。接口 MUST 校验请求中的 `SdkAppid` 与本应用配置一致，并 MUST 按官方公式校验 `Sign`（`sha256(Token + RequestTime)`）且拒绝时间戳误差超过 1 分钟的请求。`SdkAppid` 是会下发给客户端的公开值，不足以证明来源，因此未配置 `IM_CALLBACK_TOKEN` 时接口 MUST 拒绝处理回调（不写入任何数据）。接口 MUST 在 2 秒内返回，写库与媒体处理 SHALL 在响应之后的后台任务中执行。响应体 MUST 为 `{"ActionStatus":"OK","ErrorInfo":"","ErrorCode":0}`。

#### Scenario: 文本消息落库

- **WHEN** 收到合法的 `C2C.CallbackAfterSendMsg` 回调且 `MsgBody` 含 `TIMTextElem`
- **THEN** 按 `MsgKey` 写入一条 `element_type=text` 的记录，内容包含收发双方与文本
- **AND** 返回 `ErrorCode=0`

#### Scenario: 重复回调幂等

- **WHEN** 同一 `MsgKey` 的回调被重复投递
- **THEN** 数据库中该 `MsgKey` 仍只有一条记录

#### Scenario: SDKAppid 不匹配拒绝

- **WHEN** 回调 URL 参数中的 `SdkAppid` 与本应用配置不一致
- **THEN** 请求被拒绝且 MUST NOT 写入任何消息记录

#### Scenario: 未配置回调 Token 时拒绝落库

- **WHEN** 服务端未配置 `IM_CALLBACK_TOKEN`
- **THEN** 回调仍返回 `ErrorCode=0`，但 MUST NOT 写入任何消息记录

#### Scenario: 签名不合法拒绝

- **WHEN** 回调携带的 `Sign` 与 `sha256(Token + RequestTime)` 不一致，或 `RequestTime` 与服务端时间偏差超过 1 分钟
- **THEN** 请求被拒绝且 MUST NOT 写入任何消息记录

#### Scenario: 未知回调命令放行

- **WHEN** 收到本次未处理的 `CallbackCommand`
- **THEN** 直接返回 `ErrorCode=0`，不影响 IM 正常收发

#### Scenario: 回调体不是对象

- **WHEN** 回调请求体的 JSON 顶层不是对象（例如数组）
- **THEN** 返回 `ErrorCode=0` 且不写入数据，MUST NOT 抛出 500 让 IM 判定回调失败

### Requirement: 会话媒体转存对象存储

系统 SHALL 对落库的 `TIMImageElem` 与 `TIMSoundElem` 消息，从 IM 返回的地址下载文件并通过现有存储适配器上传到阿里 OSS，将结果写入 `oss_url`。媒体转存 MUST 复用 `app/services/upload_service.py` 的存储适配器，MUST NOT 扩大对外图片上传接口的 scope 白名单或类型限制。下载 MUST 流式读取并按大小上限（10MB）中断。消息记录 MUST 先于转存提交，转存失败或抛异常 MUST NOT 影响消息落库结果。

#### Scenario: 图片转存成功

- **WHEN** 图片消息的 IM 地址可下载且 OSS 可用
- **THEN** `oss_url` 写为 OSS 公开访问地址，`media_url` 保留 IM 原始地址

#### Scenario: 语音转存成功

- **WHEN** 语音消息回调体含 `Url` 与 `Second`
- **THEN** 下载后上传 OSS，`oss_url` 写入语音文件的 OSS 地址

#### Scenario: 转存失败降级

- **WHEN** 媒体下载或 OSS 上传失败
- **THEN** 消息记录仍然保留，`oss_url` 为空，`media_url` 保留 IM 原始地址
- **AND** 记录 warning 日志

#### Scenario: 转存过程抛出异常

- **WHEN** 转存环节抛出未被识别的异常（例如媒体地址畸形导致 `InvalidURL`）
- **THEN** 该条消息记录 MUST 已经落库，只丢失 `oss_url`

### Requirement: 已读状态服务端回调回写

系统 SHALL 处理 `C2C.CallbackAfterMsgReport` 命令，按 `Report_Account`（已读者）与 `Peer_Account`（发送者）以及 `LastReadTime`，将该方向上 `msg_time <= LastReadTime` 的消息标记为已读并记录 `read_at`。重复上报 MUST 保持幂等。

#### Scenario: 对端已读上报

- **WHEN** 收到 A 已读 B 消息的 `C2C.CallbackAfterMsgReport` 回调
- **THEN** `im_from_account=B AND im_to_account=A` 且未读的记录的 `is_read` 置为 true

#### Scenario: 重复已读上报

- **WHEN** 同一对用户的已读上报被重复投递
- **THEN** 已读记录结果不变，不产生新记录

### Requirement: 会话历史消息查询接口

系统 SHALL 提供 `GET /api/v1/chat/messages` 接口，使用登录态鉴权，返回当前用户与指定 `peer`（IM UserID）之间的历史消息，支持 `limit` 与 `before` 分页。接口 MUST 只返回当前用户作为收或发一方的消息，MUST NOT 返回他人会话。`peer` MUST 先归一为库内存储形态（`uuid.hex`）再比较，大写或带连字符的合法 UserID MUST 命中同一会话。

#### Scenario: 参与者查询历史

- **WHEN** 已登录用户请求自己与对端之间的历史消息
- **THEN** 返回该会话消息列表，含 `msg_key`、`element_type`、`content`、`oss_url`、`is_read` 与时间

#### Scenario: 越权查询被拒

- **WHEN** 请求的 `peer` 与当前用户之间不存在会话数据，或 `peer` 不是合法的 IM UserID
- **THEN** 返回空列表或参数错误，且 MUST NOT 泄露第三方消息

#### Scenario: 未登录访问

- **WHEN** 未携带有效登录态访问历史接口
- **THEN** 返回 401

#### Scenario: peer 大小写与连字符归一

- **WHEN** 传入大写或带连字符形式的对端 UserID
- **THEN** 仍返回同一会话的历史消息，不因字符串形态不同而漏查

### Requirement: 会话窗口优先使用数据库消息数据

br-app 会话窗口 SHALL 在进入会话后请求本系统历史消息接口，用其中的 `oss_url` 覆盖图片与语音消息的渲染地址；未命中数据库记录时 SHALL 回退到 IM 原始地址。消息列表的渲染数据源仍由 TUIKit 引擎驱动，MUST NOT 伪造引擎消息对象。覆盖映射 MUST 按需刷新：列表中出现比已拉取快照更新的消息，或上一次请求失败时， SHALL 重新拉取（最短间隔 2 秒），不得把某个会话的映射永久缓存。

#### Scenario: 命中 OSS 地址

- **WHEN** 历史接口返回的 `msg_key` 与引擎消息列表中某条图片/语音消息对应，且该记录有 `oss_url`
- **THEN** 该消息使用 OSS 地址渲染

#### Scenario: 数据库无记录

- **WHEN** 引擎消息在历史接口结果中没有对应记录，或记录没有 `oss_url`
- **THEN** 保持 IM 原始地址渲染，不报错

#### Scenario: 历史接口失败

- **WHEN** 历史接口请求失败或超时
- **THEN** 会话窗口仍正常显示 IM 消息，不阻塞聊天

#### Scenario: 会话内出现更新的消息

- **WHEN** 重新进入同一会话，或列表中出现时间晚于上次快照的图片/语音消息
- **THEN** 重新拉取历史接口并刷新映射（受最短间隔约束），使新消息同样能取到 OSS 地址

#### Scenario: 同一秒同方向的不同媒体类型

- **WHEN** 同一秒内同一收发方向同时存在图片与语音消息
- **THEN** 按「时间 + 收发方向 + 元素类型」匹配，两者 MUST NOT 互相错配

