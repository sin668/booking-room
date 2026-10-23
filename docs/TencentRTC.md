# 腾讯云 IM (Tencent RTC) 集成文档

## 概述

本项目使用腾讯云 IM（即时通信）实现单聊功能，前端基于 TUIKit（`@tencentcloud/chat-uikit-uniapp`）和 lite-chat SDK，后端通过第三方回调落库消息镜像并转存媒体到 OSS。

**核心能力：**
- 单聊消息收发（文本、图片、语音、视频、表情、自定义消息）
- 消息已读回执
- 消息撤回
- 历史消息加载（SDK 漫游 + 数据库镜像）
- 媒体文件 OSS 转存

---

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│  小程序端 (br-app)                                           │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ TUIKit 组件层                                          │ │
│  │ - TUIChat (聊天页)                                     │ │
│  │ - TUIConversation (会话列表)                           │ │
│  │ - 消息输入/展示组件                                     │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ TUIKit 引擎层 (chat-uikit-engine-lite)                 │ │
│  │ - 消息状态管理 (TUIStore)                              │ │
│  │ - 会话切换 (TUIConversationService)                    │ │
│  │ - 自动已读 (enableAutoMessageRead)                     │ │
│  ───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ lite-chat SDK                                          │ │
│  │ - 消息收发 (sendMessage)                               │ │
│  │ - 历史拉取 (getMessageList)                            │ │
│  │ - 媒体上传 (uploadFile)                                │ │
│  ───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ 业务层 (utils/im.js, im-history.js)                    │ │
│  │ - IM 初始化 (ensureIM)                                 │ │
│  │ - 深历史拉取 (fetchImHistoryPage)                      │ │
│  │ - 消息重建 (buildImHistoryMessages)                    │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │ WebSocket (wss)                    │ HTTP
         ▼                                    ▼
┌─────────────────────────────────────────────────────────────┐
│  腾讯云 IM 服务端                                            │
│  - 消息路由                                                  │
│  - 云端漫游 (7 天免费版)                                      │
│  - 第三方回调 (C2C.CallbackAfter*)                           │
└─────────────────────────────────────────────────────────────┘
         │ HTTP POST
         ▼
┌─────────────────────────────────────────────────────────────┐
│  后端服务 (br-server)                                        │
│  ┌─────────────────────────────────────────────────────── │
│  │ IM 回调路由 (/api/v1/im/callback)                      │ │
│  │ - C2C.CallbackAfterSendMsg → 落库 + 媒体转存           │ │
│  │ - C2C.CallbackAfterMsgReport → 已读回写                │ │
│  │ - C2C.CallbackAfterMsgWithDraw → 撤回标记              │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────── │
│  │ 历史查询 API (/api/v1/chat/messages)                   │ │
│  │ - 按会话 + 游标分页                                     │ │
│  │ - 返回原始 MsgBody + 重建字段                           │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────── │
│  │ 媒体转存 (im_media_service.py)                         │ │
│  │ - 下载 IM/COS 媒体 → 上传 OSS                          │ │
│  │ - 支持 image/audio/video                               │ │
│  ───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 前端 TUIKit 改动

### 1. 聊天页生命周期管理 (`TUIKit/components/TUIChat/index.vue`)

**问题：** 小程序 `onHide`（跳页/切后台）时未释放会话，导致：
- 接收方不在聊天窗口时，新消息仍被引擎自动上报已读（"秒已读"）
- 打开系统选择器（相册/相机）触发 `onHide`，会话被清空，发送方窗口看不到新消息

**解决方案：**

```typescript
let isChoosingMedia = false  // 区分系统选择器触发的 onHide
let releasedOnHide = false   // 防止 onShow 重复绑定

onLoad((options) => {
  pageConversationID.value = options?.conversationID || ''
  initChat(options)
  // 监听媒体选择器状态
  uni.$on('choosing-media-start', () => { isChoosingMedia = true })
  uni.$on('choosing-media-end', () => { isChoosingMedia = false })
})

onHide(() => {
  if (releasedOnHide) return
  releasedOnHide = true
  if (!isChoosingMedia) {
    reset()  // 释放会话，停止自动已读
  }
})

onShow(() => {
  if (!releasedOnHide) return
  releasedOnHide = false
  if (!isChoosingMedia && pageConversationID.value) {
    initChat({ conversationID: pageConversationID.value })  // 重新绑定
  }
})

onUnload(() => {
  reset()
  uni.$off('choosing-media-start')
  uni.$off('choosing-media-end')
  logout(false)
})
```

**关键点：**
- `isChoosingMedia` 标志位区分「用户跳页」和「打开系统选择器」
- `releasedOnHide` 防止 `onLoad → onShow` 首次进入时重复绑定
- `onShow` 绑回时使用页面入参的会话 ID，不依赖 store（可能已被清空）

### 2. 媒体上传错误处理 (`TUIKit/components/TUIChat/message-input-toolbar/uploadToolkit/`)

**问题：** 
- 视频发送失败时无 Toast（同步抛错被 wx 回调吞掉）
- 相机权限被拒时无提示（只写了 success 没写 fail）
- SDK 错误信息被丢弃（`Unknown failed. error: {"message": }`）

**解决方案：**

`useUpload.ts` - 四个 choose 调用统一挂 fail 回调：
```typescript
const cachedConversationID = TUIStore.getData(StoreName.CONV, 'currentConversationID')
uni.$emit('choosing-media-start')
try {
  TUIGlobal.chooseVideo({
    sourceType: [sourceType],
    fail: function (err: any) {
      uni.$emit('choosing-media-end')
      genChooseFailHandler('视频')(err)  // Toast 显示 wx 原始 errMsg
    },
    success: function (res) {
      uni.$emit('choosing-media-end')
      const currentID = TUIStore.getData(StoreName.CONV, 'currentConversationID')
      if (!currentID && cachedConversationID) {
        // onHide 清空了会话，等待恢复后再发送
        TUIConversationService.switchConversation(cachedConversationID)
          .then(() => {
            const conversation = TUIStore.getConversationModel(cachedConversationID)
            if (conversation) sendVideoMessage(conversation, res)
          })
          .catch((err) => {
            console.error('[TUIChat] switchConversation 失败:', err)
            Toast({ message: '会话恢复失败，请稍后重试', type: TOAST_TYPE.ERROR })
          })
        return
      }
      // 正常路径
      sendVideoMessage(conversation, res)
    },
  })
} catch (err) {
  uni.$emit('choosing-media-end')
  // 同步抛错防护
}
```

`utils.ts` - sendVideoMessage 同步抛错防护：
```typescript
try {
  const result = TUIChatService.sendVideoMessage(options, sendMessageOptions)
  result?.catch(reportSendFailure('视频'))  // 异步 reject
} catch (e) {
  reportSendFailure('视频')(e)  // 同步 throw
}
```

### 3. 深历史消息加载 (`TUIKit/components/TUIChat/message-list/index.vue`)

**问题：** 腾讯云 IM 单聊云端只免费漫游 7 天，翻到漫游头部后无法查看更早消息。

**解决方案：**

```typescript
async function getHistoryMessageList() {
  // 1. 优先走 SDK 漫游
  if (!isCompleted.value) {
    await getMessageList()
    return
  }
  // 2. SDK 到头后，单聊转数据库拉取更早历史
  if (isGroup.value) return
  const earliestMsg = messageList.value[0]
  if (!earliestMsg) return
  const { messages, hasMore } = await fetchImHistoryPage(
    currentConversationID.value,
    earliestMsg.time,  // 严格更早（before 游标）
    20
  )
  if (messages.length) {
    const rebuilt = buildImHistoryMessages(messages, {
      conversationID: currentConversationID.value,
      myIMID: myIMID.value,
      needReadReceipt: needReadReceipt.value,
      userInfo: userInfo.value,
    })
    // 必须用 unshift：push/contact 会无条件上报已读
    TUIChatService.updateMessageList(rebuilt, 'unshift')
  }
  dbHasMore.value = hasMore
}
```

**「查看更多」显示条件：**
```html
<button v-if="!isCompleted || (!isGroup && dbHasMore)">查看更多</button>
```

**为什么用 `unshift` 而不是 `push`：**
- `chat-uikit-engine-lite` 的 `updateTargetMessageList()` 中，`case "push" / "contact"` 会**无条件**调用 `chat.setMessageRead()`
- `case "unshift"` 只做三件事：按 ID 去重、合并列表、重排，**完全不碰已读**
- 用 `push` 注入深历史 = 替对端把整段历史标成已读

---

## 消息拉取流程

### 正常消息加载（7 天内）

```
用户打开聊天页
  ↓
TUIChatKit.init({ conversationID })
  ↓
TUIConversationService.switchConversation(id)
  ↓
SDK 自动拉取最近消息（云端漫游）
  ↓
chat-uikit-engine-lite 监听消息事件
  ↓
TUIStore 更新 messageList
  ↓
消息列表组件渲染
```

### 深历史消息加载（超过 7 天）

```
用户点击「查看更多」
  ↓
SDK getMessageList() 返回 isCompleted = true
  ↓
前端判断：单聊 && SDK 到头
  ↓
调用 GET /api/v1/chat/messages?peer=<imAccount>&before=<earliest_time>
  ↓
后端查询 im_messages 表（msg_time < before, 按 msg_time desc, msg_seq desc 排序）
  ↓
返回原始 MsgBody + 重建字段（oss_url, is_revoked, cloud_custom_data 等）
  ↓
前端 buildImHistoryMessages() 重建为 SDK 消息结构
  ↓
TUIChatService.updateMessageList(messages, 'unshift')
  ↓
消息列表前插深历史消息
```

### 消息重建逻辑 (`br-app/src/utils/im-history.js`)

```javascript
const ELEMENT_TO_TYPE = {
  text: TUIChatEngine.TYPES.MSG_TEXT,
  image: TUIChatEngine.TYPES.MSG_IMAGE,
  sound: TUIChatEngine.TYPES.MSG_AUDIO,
  video: TUIChatEngine.TYPES.MSG_VIDEO,
  face: TUIChatEngine.TYPES.MSG_FACE,
  custom: TUIChatEngine.TYPES.MSG_CUSTOM,
}

function buildPayload(elementType, row) {
  const element = firstElement(row.elements)
  const content = element?.MsgContent || {}
  switch (elementType) {
    case 'image':
      return {
        imageInfoArray: [{
          url: row.oss_url || content.ImageInfoArray?.[0]?.URL || row.media_url,
          width: content.ImageInfoArray?.[0]?.width || 0,
          height: content.ImageInfoArray?.[0]?.height || 0,
        }]
      }
    case 'sound':
      return {
        url: row.oss_url || content.Url || row.media_url,
        second: content.Second || Number(row.content) || 0,
      }
    case 'video':
      return {
        url: row.oss_url || content.VideoUrl || row.media_url,
        snapshotUrl: content.ThumbUrl || '',
        snapshotWidth: content.ThumbWidth || 0,
        snapshotHeight: content.ThumbHeight || 0,
      }
    // ...
  }
}
```

**关键点：**
- 媒体地址优先级：`oss_url`（转存后）> `content.VideoUrl/Url`（IM 原地址）> `media_url`（兜底）
- 视频缩略图保留腾讯云原地址（已在小程序域名白名单）
- 只重建已知类型，未知类型跳过（避免落到 `v-else` 的「撤回消息」分支）

---

## 超过 7 天的历史消息

### 为什么需要数据库镜像

腾讯云 IM 单聊消息云端漫游时长：
- **体验版/专业版**：7 天（免费）
- **旗舰版**：可开通增值服务延长

免费版 7 天后消息从云端删除，`getMessageList()` 翻到漫游头部后 `isCompleted` 置真，无法继续往前翻。

### 数据库镜像方案

**服务端回调落库**（`br-server/app/services/im_callback_service.py`）：

```python
async def save_send_msg_callback(session, payload):
    """C2C.CallbackAfterSendMsg 落库，按 msg_key 幂等"""
    msg_key = payload.get("MsgKey")
    # ... 幂等检查 ...
    
    parsed = parse_message(payload.get("MsgBody"))
    record = ImMessage(
        msg_key=msg_key,
        im_from_account=from_account,
        im_to_account=to_account,
        from_user_id=from_im_user_id(from_account),
        to_user_id=from_im_user_id(to_account),
        msg_time=int(payload.get("MsgTime") or 0),
        element_type=parsed.element_type,
        content=parsed.content,
        media_url=parsed.media_url,
        cloud_custom_data=payload.get("CloudCustomData"),
        raw_payload={"MsgBody": payload.get("MsgBody") or []},
    )
    session.add(record)
    await session.flush()
    return record
```

**数据库表结构** (`br-server/app/models/im_message.py`)：

```python
class ImMessage(Base):
    __tablename__ = "im_messages"
    
    id: Mapped[int]  # 自增主键
    msg_key: Mapped[str]  # 腾讯云 IM MsgKey（唯一标识）
    im_from_account: Mapped[str]  # 发送方 IM 账号
    im_to_account: Mapped[str]  # 接收方 IM 账号
    from_user_id: Mapped[UUID | None]  # 关联本系统用户
    to_user_id: Mapped[UUID | None]
    msg_time: Mapped[int]  # 消息发送时间戳（秒）
    msg_seq: Mapped[int | None]  # 消息序号（同秒排序用）
    element_type: Mapped[str]  # text/image/sound/video/face/custom/other
    content: Mapped[str | None]  # 文本内容或媒体描述
    media_url: Mapped[str | None]  # IM/COS 原始媒体地址
    oss_url: Mapped[str | None]  # 服务端转存后的 OSS 地址
    is_read: Mapped[bool]  # 是否已读
    read_at: Mapped[datetime | None]  # 已读时间
    is_revoked: Mapped[bool]  # 是否已撤回
    revoke_time: Mapped[int | None]  # 撤回时间戳
    cloud_custom_data: Mapped[str | None]  # 引用/回复内容
    raw_payload: Mapped[dict | None]  # 原始 MsgBody（重建用）
    created_at: Mapped[datetime]  # 落库时间
```

**历史查询 API** (`br-server/app/api/routes/chat.py`)：

```python
@router.get("/messages")
async def get_chat_messages(
    peer: str,  # 对方 IM 账号（uuid.hex）
    before: int | None = None,  # 游标（严格更早）
    limit: int = 20,
):
    # 排序口径对齐 IM：先 msg_time desc，同秒按 msg_seq desc
    result = await db.execute(
        select(ImMessage)
        .where(*conditions)
        .order_by(
            ImMessage.msg_time.desc(),
            ImMessage.msg_seq.desc(),
            ImMessage.id.desc(),
        )
        .limit(limit)
    )
    rows = list(result.scalars().all())
    return {
        "messages": [
            {
                "msg_key": row.msg_key,
                "element_type": row.element_type,
                "elements": (row.raw_payload or {}).get("MsgBody") or [],
                "oss_url": row.oss_url,
                "media_url": row.media_url,
                "is_revoked": row.is_revoked,
                "is_read": row.is_read,
                "msg_time": row.msg_time,
                "msg_seq": row.msg_seq,
                # ...
            }
            for row in rows
        ],
        "has_more": len(rows) == limit,
    }
```

### 已知边界

1. **深历史消息不是 SDK 消息实例**：长按菜单里的撤回/删除/转发点了不会生效（最多报个错）
2. **回调开启前的空白**：回调开启（2026-10-22）之前、又超出当前漫游窗口的消息，两个来源都没有
3. **媒体转存失败**：没有 `oss_url` 的记录仍会用 IM 的 COS 地址，小程序没配那个域名就显示占位图

---

## 媒体转存 OSS

### 为什么需要转存

1. **小程序域名白名单限制**：IM 的 COS 域名（`*.rich.my-imcloud.com`）可能不在白名单
2. **CDN 加速**：OSS 可以配置自己的 CDN 域名
3. **长期存储**：IM 云端删除后，本地 OSS 仍保留

### 转存流程

```
腾讯云 IM 回调 C2C.CallbackAfterSendMsg
  ↓
后端解析 MsgBody，提取 media_url
  ↓
判断 element_type 是否在 _MEDIA_KINDS（image/sound/video）
  ↓
是 → 后台任务 _persist_send_msg()
  ↓
先提交消息记录到数据库（确保消息不丢）
  ↓
fetch_and_upload(kind, media_url)
  ↓
httpx 流式下载 IM/COS 媒体（限长 10MB）
  ↓
get_storage_adapter().upload(upload)  # 线程池执行，避免阻塞事件循环
  ↓
更新 im_messages.oss_url = oss_url
  ↓
提交事务
```

### 转存服务 (`br-server/app/services/im_media_service.py`)

```python
_DEFAULT_EXT = {"image": ".jpg", "audio": ".mp3", "video": ".mp4"}
_ALLOWED_EXTS = {
    "image": {".jpg", ".jpeg", ".png", ".gif", ".webp"},
    "audio": {".mp3", ".wav", ".aac", ".m4a", ".amr"},
    "video": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
}
_CONTENT_TYPES = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    # ...
}

async def fetch_and_upload(kind: str, media_url: str) -> str | None:
    """转存一条媒体，返回 OSS 公开地址；任何失败返回 None"""
    try:
        data = await _download(media_url)  # 流式下载，边读边限长
    except Exception:
        return None  # 转存失败不影响消息落库
    
    ext = _extension(kind, media_url)
    upload = UploadObject(
        content=data,
        object_key=f"chat/{kind}/{now:%Y/%m/%d}/{uuid.uuid4().hex}{ext}",
        content_type=_CONTENT_TYPES[ext],
    )
    try:
        result = await asyncio.to_thread(get_storage_adapter().upload, upload)
    except Exception:
        return None
    
    return result.url
```

### 视频消息的特殊处理

**MsgType 识别** (`br-server/app/services/im_callback_service.py`)：

```python
_ELEMENT_TYPES = {
    "TIMTextElem": "text",
    "TIMImageElem": "image",
    "TIMSoundElem": "sound",
    "TIMFileElem": "file",
    "TIMVideoElem": "video",       # 旧版 SDK
    "TIMVideoFileElem": "video",   # 4.X+ SDK（本项目实际使用）
    "TIMFaceElem": "face",
    "TIMCustomElem": "custom",
}
```

**视频字段提取**：

```python
if element_type == "video":
    return ParsedMessage(
        "video",
        f"{content.get('Second', 0)}s" if content.get("Second") else None,
        content.get("VideoUrl") or None,  # 视频地址
    )
```

**注意：** 视频缩略图（`ThumbUrl`）不转存，保留腾讯云原地址（已在小程序域名白名单）。

---

## 遇到的问题和处理

### 1. 生产环境 IM 初始化超时

**现象：** 调试模式正常，关闭调试模式后长时间显示"正在连接..."，最终超时。

**根因：** 微信小程序调试模式不校验域名白名单。SDK 的 `getconninfo` API 返回最优 WebSocket 服务器（可能是全球任意节点），生产环境严格执行白名单，不在列表中的域名连接失败。

**解决：** 添加全部 29 个 WebSocket 域名 + 4 个 request 域名到微信公众平台。

**涉及文件：** `br-app/src/utils/im.js`

### 2. 语音/视频发送失败（调试模式正常）

**现象：** 调试模式发送正常，正式版小程序发送失败，Toast 显示 `Unknown failed. error: {"message": }`。

**根因：** 
1. 语音/视频上传走服务端下发的 COS 预签名地址（`20049215-sg.rich.my-imcloud.com`），不是固定主机
2. SDK 错误类丢弃了 `wx.uploadFile` 的 `errMsg` 和 URL
3. IPv6 网络下 SDK 会整体替换 host 为 `sgpv6.rich.my-imcloud.com`，这条域名没加白名单

**解决：** 
1. 添加实际上传域名到白名单
2. `hookUploadDiagnostic()` 拦截 `TUIGlobal.uploadFile`，记录 url + errMsg
3. 失败 Toast 显示真实上传 host 和 SDK code

**涉及文件：** `br-app/src/utils/im.js`, `br-app/src/TUIKit/components/TUIChat/message-input-toolbar/uploadToolkit/utils.ts`

### 3. 消息刚发出就显示"已读"

**现象：** 发送方气泡刚发出就从"未读"翻成"已读"，接收方表示没打开过聊天窗口。

**根因：** TUIKit 引擎 `chat-uikit-engine-lite` 的 `updateMessageList()` 在 `case "push" / "contact"` 分支里**无条件**调用 `chat.setMessageRead()`。只要对端小程序停在聊天页（`currentConversationID` 绑定），新消息一 push 就整会话标记已读。

**解决：** 聊天页 `onHide` 时调用 `reset()` 释放会话，页面不可见期间引擎不会自动上报。

**涉及文件：** `br-app/src/TUIKit/components/TUIChat/index.vue`

### 4. 发送视频/图片后发送方窗口看不到新消息

**现象：** 发送视频/图片后，接收方窗口正常显示，但发送方窗口先变空白，再加载历史，出现"回到最新位置"按钮。

**根因：** 
1. 用户点击「拍摄/相册」→ 打开系统选择器 → 触发 `onHide`
2. `onHide` 调用 `reset()` → 清空 `currentConversationID` 和消息列表
3. `success` 回调执行时，会话尚未恢复
4. `TUIConversationService.switchConversation()` 返回 Promise，是异步操作

**解决：** 
1. `isChoosingMedia` 标志位区分系统选择器触发的 `onHide`
2. `success` 回调中检查 `currentConversationID`，为空时等待 `switchConversation` 完成再发送

**涉及文件：** `br-app/src/TUIKit/components/TUIChat/index.vue`, `br-app/src/TUIKit/components/TUIChat/message-input-toolbar/uploadToolkit/useUpload.ts`

### 5. 视频消息 element_type 显示为 other

**现象：** 数据库里视频消息的 `element_type` 是 `other`，`media_url` 和 `oss_url` 都是 NULL。

**根因：** 腾讯云 IM 4.X+ SDK 发出的视频消息 `MsgType` 是 `TIMVideoFileElem`，不是 `TIMVideoElem`。

**解决：** `_ELEMENT_TYPES` 添加 `TIMVideoFileElem` → `video` 映射，保留 `TIMVideoElem` 兼容旧版。

**涉及文件：** `br-server/app/services/im_callback_service.py`

### 6. 主包未使用 JS 文件告警

**现象：** 微信开发者工具提示 `主包内不应该存在主包未使用的JS文件：utils/im-history.js`。

**根因：** uni-app 编译 mp-weixin 时把 `src/utils/*.js` 整体提升到主包，但 `im-history.js` 只被 TUIKit 子包引用。

**解决：** `post-build-move-assets.js` 的 `MOVES` 表添加 `utils/im-history.js → TUIKit/utils/im-history.js`，搬迁时改写两侧 `require` 路径。

**涉及文件：** `br-app/scripts/post-build-move-assets.js`

---

## 小程序域名白名单

### socket 合法域名（29 个）

```
wss://wss.im.qcloud.com
wss://wss.tim.qq.com
wss://wss.im.tencent.cn
wss://wss.my-imcloud.com
wss://wssv6.im.qcloud.com
wss://wssger.im.qcloud.com
wss://wssger.my-imcloud.com
wss://wssgerv6.im.qcloud.com
wss://wssidn.im.qcloud.com
wss://wssidn.my-imcloud.com
wss://wssidnv6.im.qcloud.com
wss://wssind.im.qcloud.com
wss://wssind.my-imcloud.com
wss://wssindv6.im.qcloud.com
wss://wssjpn.im.qcloud.com
wss://wssjpn.my-imcloud.com
wss://wssjpnv6.im.qcloud.com
wss://wsskr.im.qcloud.com
wss://wsskr.my-imcloud.com
wss://wsskrv6.im.qcloud.com
wss://wssksa.im.qcloud.com
wss://wssksa.my-imcloud.com
wss://wssksav6.im.qcloud.com
wss://wsssgp.im.qcloud.com
wss://wsssgp.my-imcloud.com
wss://wsssgpv6.im.qcloud.com
wss://wssusa.im.qcloud.com
wss://wssusa.my-imcloud.com
wss://wssusav6.im.qcloud.com
```

### request 合法域名（4 个）

```
https://api.my-imcloud.com
https://boce-cdn.my-imcloud.com
https://events.im.qcloud.com
https://web.sdk.qcloud.com
```

### uploadFile/downloadFile 合法域名

```
https://20049215-sg.rich.my-imcloud.com  # 本项目实际使用（新加坡区域）
https://sgpv6.rich.my-imcloud.com         # IPv6 网络下 SDK 替换的 host
```

**注意：** 微信公众平台域名配置**不支持通配符**，必须逐条填写完整主机名。

---

## 回调鉴权

### 签名公式

```
Sign = sha256(Token + RequestTime)
```

- `Token`：后端配置的 `IM_CALLBACK_TOKEN`（环境变量）
- `RequestTime`：URL 参数（毫秒时间戳）
- `Sign`：URL 参数

### 验证逻辑 (`br-server/app/core/im.py`)

```python
def verify_callback_sign(sdk_appid: str | None, request_time: str | None, sign: str | None) -> bool:
    if not settings.IM_CALLBACK_TOKEN:
        return False  # 未配置 Token 时拒绝所有回调
    if not (sdk_appid and request_time and sign):
        return False
    if int(sdk_appid) != settings.IM_SDK_APP_ID:
        return False
    # 时间戳有效期 60 秒
    if abs(int(time.time() * 1000) - int(request_time)) > 60_000:
        return False
    expected = hashlib.sha256(f"{settings.IM_CALLBACK_TOKEN}{request_time}".encode()).hexdigest()
    return hmac.compare_digest(expected, sign)
```

### 回调路由 (`br-server/app/api/routes/im_callback.py`)

```python
@router.post("/callback")
async def im_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    sdk_appid: str | None = Query(alias="SdkAppid"),
    sign: str | None = Query(alias="Sign"),
    request_time: str | None = Query(alias="RequestTime"),
):
    if not verify_callback_sign(sdk_appid, request_time, sign):
        return CALLBACK_OK  # 鉴权失败仍返回 OK，但不落库
    
    body = await request.json()
    command = body.get("CallbackCommand")
    
    if command == "C2C.CallbackAfterSendMsg":
        background_tasks.add_task(_persist_send_msg, body)
    elif command == "C2C.CallbackAfterMsgReport":
        background_tasks.add_task(_persist_msg_report, body)
    elif command == "C2C.CallbackAfterMsgWithDraw":
        background_tasks.add_task(_persist_msg_withdraw, body)
    
    return CALLBACK_OK  # 2s 内响应，落库在后台任务完成
```

---

## 测试验证

### 前端测试

```bash
# 聊天页自动已读判据验证
npm run test:chat-read-gate

# 聊天页生命周期约束验证
npm run test:chat-read-on-visible

# 媒体发送诊断断言
npm run test:media-send-diagnostics

# 深历史消息合并验证
npm run test:im-history-merge

# 分包布局守卫
npm run test:mp-subpackage-layout
```

### 后端测试

```bash
cd br-server
pytest tests/test_im_callback_sync.py -v
```

测试覆盖：
- 消息解析（text/image/sound/video）
- 消息落库幂等
- 撤回标记幂等
- 已读回写
- 媒体扩展名 fallback
- 下载限流
- 回调鉴权
- 历史查询 API

---

## 相关文件索引

### 前端

| 文件 | 职责 |
|------|------|
| `br-app/src/utils/im.js` | IM 初始化、上传诊断、深历史拉取 |
| `br-app/src/utils/im-history.js` | 数据库行 → SDK 消息结构重建 |
| `br-app/src/TUIKit/components/TUIChat/index.vue` | 聊天页生命周期管理 |
| `br-app/src/TUIKit/components/TUIChat/message-list/index.vue` | 消息列表 + 深历史翻页 |
| `br-app/src/TUIKit/components/TUIChat/message-input-toolbar/uploadToolkit/useUpload.ts` | 媒体选择 + 会话恢复 |
| `br-app/src/TUIKit/components/TUIChat/message-input-toolbar/uploadToolkit/utils.ts` | 视频发送 + 错误处理 |
| `br-app/scripts/verify-im-history-merge.mjs` | 深历史合并行为验证 |
| `br-app/scripts/verify-chat-read-gate.mjs` | 自动已读判据验证 |
| `br-app/scripts/post-build-move-assets.js` | 主包 JS 搬迁到子包 |

### 后端

| 文件 | 职责 |
|------|------|
| `br-server/app/models/im_message.py` | 消息镜像表模型 |
| `br-server/app/services/im_callback_service.py` | 回调解析与落库 |
| `br-server/app/services/im_media_service.py` | 媒体转存 OSS |
| `br-server/app/api/routes/im_callback.py` | 回调路由 |
| `br-server/app/api/routes/chat.py` | 历史查询 API |
| `br-server/app/core/im.py` | IM 账号派生 + 回调鉴权 |
| `br-server/tests/test_im_callback_sync.py` | 回调测试 |

### 配置

| 文件 | 职责 |
|------|------|
| `br-server/.env` | `IM_SDK_APP_ID`, `IM_CALLBACK_TOKEN` |
| `br-app/src/utils/im.js` | 域名白名单（注释） |
| 微信公众平台 | 服务器域名配置 |

---

## 经验教训

1. **第三方 SDK 的"自动"行为要查判据变量**：引擎自动已读的判据是 `currentConversationID`（会话有没有绑），不是"页面可见"
2. **只写 success 不写 fail 的第三方 API 调用是静默失败制造机**：错误出口必须在自己的层补回来
3. **第三方 SDK 的错误出口有两种：同步 throw 和 Promise reject**：`.catch` 只能抓后者，同步抛错必须用 `try-catch`
4. **往 TUIKit 的消息 store 注入数据前，先确认 `updateTargetMessageList` 的分支副作用**：选对合并类型（unshift vs push）比写多少防御代码都管用
5. **新增数据源时别做模糊匹配**：有 `MsgKey` 就直接当 ID，不要靠「秒+方向+元素类型」猜对应关系
6. **未知类型宁可不显示**：消息列表的 `v-else` 分支是"撤回消息"，把认不出的元素类型塞进去等于给用户造假记录
7. **uni-app 的 `src/utils` 一律进主包**：新增只给分包页面用的 utils 时，同步在 `MOVES` 加一行
8. **微信公众平台域名配置不支持通配符**：必须逐条完整主机名，包括 IPv6 变体
9. **调试模式不校验域名白名单**：不能作为生产环境的验证依据，必须在关闭调试模式的真机上测试
10. **腾讯云 IM 4.X+ SDK 的视频消息 MsgType 是 `TIMVideoFileElem`**：不是 `TIMVideoElem`

---

## 参考文档

- [腾讯云 IM 消息格式描述](https://cloud.tencent.com/document/product/269/2720)
- [腾讯云 IM 消息漫游](https://cloud.tencent.com/document/product/269/3683)
- [腾讯云 IM 第三方回调](https://cloud.tencent.com/document/product/269/1632)
- [TUIKit uni-app 文档](https://cloud.tencent.com/document/product/269/72049)
- [微信小程序服务器域名配置](https://developers.weixin.qq.com/miniprogram/dev/framework/ability/network.html)
