## MODIFIED Requirements

### Requirement: 单聊消息服务端回调落库

系统 SHALL 提供腾讯云 IM 第三方回调接收接口 `POST /api/v1/im/callback`，处理 `C2C.CallbackAfterSendMsg` 命令，将单聊消息持久化到 `im_messages` 表，并 MUST 同时保存回调体中的 `CloudCustomData`（引用/回复卡片内容载体，缺失时按空处理）。接口 MUST 校验请求中的 `SdkAppid` 与本应用配置一致，并 MUST 按官方公式校验 `Sign`（`sha256(Token + RequestTime)`）且拒绝时间戳误差超过 1 分钟的请求。`SdkAppid` 是会下发给客户端的公开值，不足以证明来源，因此未配置 `IM_CALLBACK_TOKEN` 时接口 MUST 拒绝处理回调（不写入任何数据）。接口 MUST 在 2 秒内返回，写库与媒体处理 SHALL 在响应之后的后台任务中执行。响应体 MUST 为 `{"ActionStatus":"OK","ErrorInfo":"","ErrorCode":0}`。

#### Scenario: 文本消息落库

- **WHEN** 收到合法的 `C2C.CallbackAfterSendMsg` 回调且 `MsgBody` 含 `TIMTextElem`
- **THEN** 按 `MsgKey` 写入一条 `element_type=text` 的记录，内容包含收发双方与文本
- **AND** 返回 `ErrorCode=0`

#### Scenario: 引用消息自定义数据落库

- **WHEN** 回调体携带 `CloudCustomData`（例如引用/回复消息时写入的 `messageReply`）
- **THEN** 记录保存该字符串原文，历史查询接口原样返回，供客户端重建引用卡片

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

### Requirement: 会话历史消息查询接口

系统 SHALL 提供 `GET /api/v1/chat/messages` 接口，使用登录态鉴权，返回当前用户与指定 `peer`（IM UserID）之间的历史消息，支持 `limit` 与 `before` 分页。接口 MUST 只返回当前用户作为收或发一方的消息，MUST NOT 返回他人会话。`peer` MUST 先归一为库内存储形态（`uuid.hex`）再比较，大写或带连字符的合法 UserID MUST 命中同一会话。返回内容 MUST 足以让客户端把记录重建为 SDK 消息结构：每条消息 MUST 含 `msg_key`、`msg_seq`、`element_type`、`content`、`media_url`、`oss_url`、`is_read`、`is_revoked`、`msg_time`、`direction` 与原始 `MsgBody` 元素、`cloud_custom_data`。排序 MUST 为 `msg_time` 倒序、同秒按 `msg_seq` 倒序，与 IM 单聊排序规则一致，保证分页游标不重不漏。

#### Scenario: 参与者查询历史

- **WHEN** 已登录用户请求自己与对端之间的历史消息
- **THEN** 返回该会话消息列表，含 `msg_key`、`element_type`、`content`、`oss_url`、`is_read` 与时间
- **AND** 每条记录附带重建消息所需的 `MsgBody` 元素、`cloud_custom_data`、`is_revoked` 与 `msg_seq`

#### Scenario: 越权查询被拒

- **WHEN** 请求的 `peer` 与当前用户之间不存在会话数据，或 `peer` 不是合法的 IM UserID
- **THEN** 返回空列表或参数错误，且 MUST NOT 泄露第三方消息

#### Scenario: 未登录访问

- **WHEN** 未携带有效登录态访问历史接口
- **THEN** 返回 401

#### Scenario: peer 大小写与连字符归一

- **WHEN** 传入大写或带连字符形式的对端 UserID
- **THEN** 仍返回同一会话的历史消息，不因字符串形态不同而漏查

## ADDED Requirements

### Requirement: 单聊消息撤回状态落库

系统 SHALL 处理 `C2C.CallbackAfterMsgWithDraw` 回调，按回调体 `MsgKey` 定位消息记录并标记为已撤回（记录撤回时间），MUST NOT 删除原消息记录。缺少 `MsgKey` 时 SHALL 直接返回成功且不改动任何数据；重复投递 MUST 幂等。该回调未在 IM 控制台勾选时，系统行为 MUST 与未引入本要求时一致。

#### Scenario: 撤回回调标记消息

- **WHEN** 收到合法的 `C2C.CallbackAfterMsgWithDraw` 且 `MsgKey` 命中已有记录
- **THEN** 该记录标记为已撤回并记录撤回时间，原内容仍保留
- **AND** 返回 `ErrorCode=0`

#### Scenario: 撤回的重复投递幂等

- **WHEN** 同一 `MsgKey` 的撤回回调被重复投递
- **THEN** 结果保持一致，不产生新记录，也不改变已标记的状态

#### Scenario: 撤回回调缺少 MsgKey

- **WHEN** 回调体没有 `MsgKey`
- **THEN** 返回 `ErrorCode=0` 且不改动任何数据

### Requirement: 会话窗口补齐超出漫游窗口的历史消息

腾讯云 IM 单聊消息在云端仅漫游有限天数，br-app 会话窗口 SHALL 在 IM 侧历史拉取完毕后继续从本系统历史接口翻页，把更早的消息按 SDK 消息结构重建并注入 TUIKit 引擎的消息列表。重建 MUST 以引擎消息列表的渲染与状态契约为准：`ID` 取 `msg_key`，携带正确的 `conversationID`、`flow`、`from`、`to`、`time`、`type`、`payload`（媒体地址优先使用记录的 `oss_url`，缺失时回退 `media_url`）、`status`、`isRevoked`、`needReadReceipt`、`isPeerRead` 与 `readReceiptInfo`、`cloud_custom_data`，使超过漫游窗口的历史同样能展示文本/图片/语音、撤回提示、已读状态与引用卡片。注入 MUST 走引擎的 `unshift` 合并路径，MUST NOT 因此触发已读上报。翻页游标 MUST 严格早于列表中已加载的最早一条消息，MUST NOT 与 IM 侧窗口重叠出重复气泡；无法识别的元素类型 SHALL 跳过而不渲染成撤回提示。历史接口失败或没有更多数据时，会话窗口 MUST 保持正常，MUST NOT 阻塞聊天。

#### Scenario: IM 历史拉完后继续向数据库翻页

- **WHEN** 引擎报告 IM 侧历史已无更多（`isCompleted`），用户点击「查看更多」
- **THEN** 从历史接口取更早的一页，按消息结构重建后前插进消息列表并按时间排序

#### Scenario: 深历史消息状态还原

- **WHEN** 数据库记录标记为已撤回、已被对端已读，或携带引用自定义数据
- **THEN** 重建的消息分别显示撤回提示、已读状态与引用卡片，媒体使用数据库转存的 OSS 地址

#### Scenario: 补历史不产生已读上报

- **WHEN** 通过数据库补齐更早的历史消息
- **THEN** MUST NOT 触发对当前会话的已读上报，对端不会因此看到「已读」

#### Scenario: 与 IM 窗口不重复

- **WHEN** 数据库记录的 `msg_time` 不早于列表中已加载的最早一条消息
- **THEN** 该记录不重复插入，消息列表中同一条消息只出现一个气泡

#### Scenario: 未知元素类型跳过

- **WHEN** 数据库记录的元素类型不在可重建集合内
- **THEN** 跳过该记录，MUST NOT 把它渲染成「撤回了一条消息」等错误形态

#### Scenario: 历史接口失败

- **WHEN** 翻页请求失败或超时
- **THEN** 会话窗口仍正常显示已加载的消息，保留「查看更多」入口可重试

## REMOVED Requirements

### Requirement: 会话窗口优先使用数据库消息数据

**Reason**: 该要求只为绕开 IM 的 COS 域名不在小程序白名单，用「时间 + 收发方向 + 元素类型」模糊匹配把 SDK 消息的图片/语音地址换成 OSS 地址，需要节流、重试上限与跨会话缓存重置等一整套状态；现在消息本身已按数据库记录重建，媒体地址来自记录自己的 `oss_url`，IM 域名也已加入小程序白名单，这套模糊替换不再有必要。

**Migration**: 由「会话窗口补齐超出漫游窗口的历史消息」承担媒体地址来源（`oss_url` 优先、`media_url` 兜底）；IM 窗口内的近 7 天消息直接使用 SDK 返回的地址渲染。`applyChatMediaUrls` / `loadChatMediaMap` 与其回归脚本一并删除。
