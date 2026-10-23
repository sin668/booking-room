## 设计说明

### 数据源分工：SDK 窗口 + 数据库深历史，而不是整体换成数据库

IM 云端只漫游 7 天，而 `im_messages` 只有开启回调之后（2026-10-22 起）的数据。若把聊天页历史整体改成只读数据库，近 7 天内、回调开启之前的消息会凭空消失——用户要的是「更多历史」，不是「换一批历史」。因此按时间分工：

- SDK 继续负责它能覆盖的窗口（`getMessageList` 分页，撤回/已读/发送状态/引用由 SDK 原生提供）。
- 数据库负责窗口之外的更早消息：`isCompleted` 为真（SDK 已无更多）时，「查看更多」转为按 `before = 当前最早一条消息的 msg_time` 向 `GET /api/v1/chat/messages` 翻页。
- 游标取严格更早（`msg_time < before`），所以数据库页与 SDK 窗口天然不重叠，不依赖任何模糊匹配键；引擎 `unshift` 分支再按 `ID` 去重一次，重复投递的同一 `msg_key` 也不会出现两个气泡。

### 注入点：`TUIChatService.updateMessageList(msgs, 'unshift')`

引擎 CHAT store 的 `updateMessageList` 会把传入的普通对象包成 `MessageModel`（`new Ue(msg)`），组件因此拿到和 SDK 消息一样的接口（`getMessageContent()`、`isRevoked` 渲染分支、长按菜单）。`unshift` 分支的行为是「按 ID 过滤已存在的 → 前插 → `sortMessageList`」，并且**不会**调用 `chat.setMessageRead`，所以补历史不会把对端消息上报成已读（这是上一轮已读问题的红线）。

### 重建字段以渲染契约为准，不臆造

按 message-list 及其子组件实际读取的字段构造：

| 字段 | 取值 | 依据 |
| --- | --- | --- |
| `ID` | `msg_key` | 引擎按 ID 去重；`vueForRenderKey`、`scroll-into-view` 都用 ID |
| `conversationID` | `C2C` + 对端账号 | `updateTargetMessageList` 只保留等于 `currentConversationID` 的消息 |
| `type` | 由 `MsgBody[0].MsgType` 决定 | 与 SDK 常量一致，避免 `element_type` 二次映射 |
| `payload` | `MsgBody[0].MsgContent`，媒体地址优先 `oss_url` | 引擎 handler 读 `payload.text` / `imageInfoArray[0].{url,width,height}` / `{url,second}` |
| `flow`/`from`/`to` | 按记录相对当前用户的方向 | 气泡左右与「对方撤回了一条消息」文案 |
| `time` | `msg_time`（秒） | 时间戳分隔与排序 |
| `status` | 固定 `success` | 回调只落 `SendMsgResult==0` 的消息，即已送达；`fail`/`unSend` 会渲染重发图标 |
| `isRevoked` | `is_revoked` | 模板 `v-else` 分支渲染 MessageRevoked |
| `needReadReceipt` | `isEnabledMessageReadReceiptGlobal()` | 与发送侧同一开关，读 read-status 的分支口径 |
| `isPeerRead` + `readReceiptInfo` | 由 `is_read` 推导，`readReceiptInfo` 必须是对象 | read-status 直接解构 `message.readReceiptInfo`，缺省会抛错 |
| `cloudCustomData` | 记录原值字符串 | message-quote 组件 `JSON.parse(cloudCustomData).messageReply` |
| `nick`/`avatar` | 取 CHAT store `userInfo[account]` | 与引擎 `updateLocalMessage` 同一来源，取不到时气泡自行回退 |

只重建 `text/image/sound/custom/face` 五类；数据库里的 `other`（未知元素）跳过——模板的 `v-else` 会把无法识别的消息渲染成「撤回了一条消息」，宁可少显示一条也不显示错。

### 服务端只补三点，不改既有幂等与鉴权

1. `save_send_msg_callback` 多存 `CloudCustomData`（引用/回复卡片内容在里面，不落库就重建不出引用）。
2. 新增 `apply_msg_withdraw`：处理 `C2C.CallbackAfterMsgWithDraw`（字段 `From_Account`/`To_Account`/`MsgKey`/`EventTime`），按 `msg_key` 置 `is_revoked`/`revoke_time`，重复投递幂等；未勾选该回调时行为与现在一致。
3. 历史接口排序改为 `msg_time desc, msg_seq desc, id desc`（与官方「单聊先按时间、同秒按 MsgSeq」一致），并返回重建字段。旧数据没有 `cloud_custom_data`/`is_revoked` 时按空值/未撤回处理，不做回填。

### 已知边界（明确接受，不做额外兜底）

- 深历史消息点撤回/删除/转发会调用 SDK，SDK 不认识该消息 → 失败静默（已过撤回时限的自有消息本来也不可撤回）。本次不加操作门禁。
- 数据库没有的消息类型（回调开启前、以及非本系统账号发来的消息）超出 7 天窗口后仍不可见，这是镜像型历史库的固有限制。
- 富媒体文件在 IM 侧的存储时长与漫游一致，超过窗口后只剩服务端转存的 `oss_url`；没有转存成功的记录只能显示占位，不报错。
