# TUIKit 会话窗口问题修复记录

> 适用范围：`br-app`（uni-app vue3 + 腾讯 TUIKit），主战场 **微信小程序（mp-weixin）**，兼顾 H5 / App。
> 核心文件：`src/TUIKit/components/TUIChat/message-list/index.vue`、`src/utils/im-history.js`、`src/utils/im.js`。
> 本文按「报错信息 → 根本原因 → 解决方案」记录本轮会话窗口加载与滚动相关的缺陷修复。

## 背景：两条历史来源与小程序滚动机制

IM 云端只漫游 **7 天**消息（免费版）。超过 7 天的深历史由本系统数据库镜像补齐：
`fetchImHistoryPage`（后端 `/messages`，`before` 秒级游标，`has_more` 分页）拉行 →
`buildImHistoryMessages` 按 SDK 消息结构重建 → `TUIChatService.updateMessageList(msgs, 'unshift')` 前插。

微信小程序原生 `scroll-view` 的两个滚动入口语义不同，是本轮多数缺陷的根源：

| 入口 | 语义 | 陷阱 |
| --- | --- | --- |
| `scroll-top`（数值） | 滚动到指定偏移，**原生 clamp 到 `[0, maxScroll]`** | 同值重设不触发；手动滚动后 ref 不跟随原生位置 |
| `scroll-into-view`（元素 id） | 把目标元素**顶部**对齐视口**顶部** | 前插子节点布局前就执行 → 锚到旧位置；目标不足一屏时滚过内容末尾 → 白屏 |

`maxScroll = 内容总高 - 视口高`。小程序 `scrollOffset` 查询只返回 `scrollTop/scrollLeft`，
**不返回 `scrollHeight`**，内容总高需另测包裹层 `#messageScrollContent`。

---

## 问题一：「查看更多」出现过早，加载白屏卡顿，媒体预览返回跳回最新

### 报错信息
- 会话只有几条消息就出现「查看更多」按钮，需手点才加载。
- 点加载后窗口闪一下白屏、卡一下才显示更多消息，不像微信原生顺滑。
- 打开图片/视频预览，关闭后视口跳到**最新消息**，而非停留在刚看的媒体位置。

### 根本原因
1. 加载入口是手点按钮，且分页步长小，少量消息即触发「查看更多」。
2. 加载指示 spinner 在内容流内占高度，前插时高度核算被干扰，产生白屏过渡。
3. 预览返回走页面 `onShow` → 重新 `initChat`，把视口重置到最新。

### 解决方案
- 去掉手点「查看更多」：**滚动到顶部自动加载**（`scrollTop < 50 && canLoadMore && !isLoadingMessage`）
  + **不足一屏自动续拉**（`autoFillViewport`，铺满视口为止，带防抖 `autoFillLastCount` 避免原地刷接口）。
- 分页步长提到 50，spinner 移出内容流改为**覆盖层**（`message-loading-overlay`，`position:absolute`），
  不再参与前插高度差核算。
- 媒体预览返回位置保持：`handleImagePreview` 预览前 `uni.$emit('media-preview-start')`，
  页面置 `isPreviewingMedia` 标志，`onHide` 跳过重置、`onShow` 跳过 `initChat`，返回后视口不动。

---

## 问题二：超 7 天历史会话进入聊天页整屏白屏、「查看更多」无效

### 报错信息
- 全部消息都超出 7 天漫游窗口的会话，进入聊天页**一片空白**。
- 点「查看更多」无任何反应，再点屏幕才偶尔出消息。

### 根本原因
SDK 漫游到头（`isCompleted`）后引擎只回空列表，旧逻辑没有数据库兜底入口，
聊天页拿不到任何消息可渲染。

### 解决方案
- `onChatCompletedUpdated`：`isCompleted && !isGroup && 引擎消息列表为空` 时，
  直接 `loadDatabaseHistoryPage()` 从数据库取最近一页。
- `getHistoryMessageList`：先判 `isCompleted && !isGroup` 再转数据库翻页，
  SDK 窗口未到头仍归 SDK，避免重复来源。
- 数据库游标取当前最早一条消息的时间（`messageList[0].time`），按时间分区不与 SDK 消息重复上屏。
- 重建消息 `ID` 用 `MsgKey`、`status` 固定 `success`、媒体优先用转存 OSS 地址
  （IM 的 COS 域名可能不在小程序白名单），并补齐 `readReceiptInfo` 对象
  （`read-status` 组件直接解构，缺对象会抛异常）。

---

## 问题三：加载更多白屏闪烁 + 锚定前跳超一屏

### 报错信息
- 小程序加载更多（尤其超 7 天历史）时窗口闪白屏、卡一下。
- 加载后视口**往前跳到超一屏**的位置，需往下拉才能看到刚加载的消息。

### 根本原因
前插历史后用 `scroll-into-view` 锚**旧首条**：小程序原生 `scroll-view` 会在前插子节点
**布局前**就执行 `scroll-into-view`，锚到旧首条的旧位置（≈顶部），前插内容随后把视口往下顶，
表现为跳到超一屏外。盲增 `scroll-top += 300` 又会滚出内容外白屏。

### 解决方案
前插改用确定性的**高度差补偿 `scroll-top`**（`anchorPrepend`）：
- 加载前 `measureScroll` 测 `{ top: scrollTop, height: 内容总高, vp: 视口高 }`。
- 加载后 `measureContentHeight` 单查询补测内容总高，`delta = afterHeight - before.height`。
- 目标 `scrollTop = before.top + delta`，使原首条停在原来的视觉位置；
  加载前内容不足一屏（`before.height <= before.vp + 10`）时改为滚到底看最新。
- 这是全平台一致的确定性兜底，不依赖 `scroll-into-view` 的渲染时序。

---

## 问题四：安卓 webview 前插「先跳超一屏再拉回」的可见过渡帧

### 报错信息
- 安卓小程序前插历史时，仍能看到视口**先跳到超一屏、再被快速拉回**正确位置的过渡。

### 根本原因
两帧过渡：前插（setData#1 → paint A 错位）→ 渲染后测量+补偿（setData#2 → paint B 正确）。
微信 `scroll-view` 内部滚动容器 `.wx-scroll-view` 默认关闭 `overflow-anchor`，
安卓 webview 下浏览器原生滚动锚定不生效，前插先画一帧错位再被补偿拉回。
（`scroll-anchoring` 属性：webview 渲染器仅 iOS 生效；Skyline 3.6.2+ 默认开。）

### 解决方案
- 开启 iOS/Skyline 原生 `:scroll-anchoring="true"` 作免闪第一道防线。
- 安卓 webview：CSS 覆盖内部滚动容器 `overflow-anchor: auto !important`
  （`:deep(.wx-scroll-view), :deep(.uni-scroll-view)`），让浏览器原生锚定原子接管前插。
- 补偿式与原生锚定幂等共存：原生若已原子补偿，`anchorPrepend` 算出的目标值与之相同，再设一次不二次跳动。

---

## 问题五：彻底消除错位帧 paint A（离屏镜像原子前插）

### 报错信息
- 过渡已压到最短，但「先画一帧错位（paint A）、渲染后补偿再画一帧正确（paint B）」的最短过渡依然存在。

### 根本原因
只要「前插」与「补偿滚动」分属两次 setData，就必然有一帧错位。
要原子化，必须**在插入前就知道批次会增加多少高度**，把列表与目标 `scroll-top` 放进同一次 setData。

### 解决方案
**离屏镜像预测量 + 原子前插**：
1. `measureBatchHeight(batch)`：把批次渲染进离屏镜像 `#measureMirror`
   （`visibility:hidden` 保留布局、`z-index:-1`、`pointer-events:none`），
   `getBoundingClientRect` 量得前插后会增加的内容高度 `delta`。
   图片高度由 payload `width/height` 经 `watchEffect` 在加载前确定（`DEFAULT_MAX_SIZE=155`），
   视频用 `snapshotWidth/Height`，故镜像量高与真实渲染一致。
2. `commitPrepend(batch, before, delta)`：**同一次 flush 内**先设目标 `scroll-top`
   （`before.top + delta`，不足一屏则 `before.height + delta`）→ 清镜像 → `updateMessageList(batch, 'unshift')`
   → 复位加载态。渲染层在绘制前同时应用列表与滚动位置，**第一帧即定位正确**，无 paint A。
3. `verifyPrepend` 安全网：仅当真实位置与理想位置偏差 `> 40px`
   （同帧 `scroll-top` 被旧高度钳制、缺尺寸图片加载后大幅撑高）才用 `+1px` 微 nudging 强制重设；
   阈值内小残差忽略，原子前插到位时本函数不动、无额外绘制。

---

## 问题六：「回到最新位置」首次点击白屏，再点一次才正确

### 报错信息
- 会话窗口点击「回到最新位置」按钮，**首次点击出现白屏**，再点一次才回到正确的最新消息位置。

### 根本原因
滚底用 `scroll-into-view` 锚**末条**（`setAnchor(last.ID, true)`）。
`scroll-into-view` 把末条**顶部**对齐视口**顶部**：当末条高度不足一屏时，
对齐后的 `scrollTop = 内容总高 - 末条高 > maxScroll = 内容总高 - 视口高`，
即滚过内容末尾 `(视口高 - 末条高)`，超出部分整屏白屏。
第二次点击的强制重触发（先清空再设）落点不同才恢复正确。

### 解决方案
滚底统一改用**数值 `scroll-top` 递增哨兵**，移除整套 `scroll-into-view` 锚点机制：
```js
let bottomScrollSeq = 0;
const scrollToBottom = () => {
  scrollTop.value = 1e9 + (++bottomScrollSeq);
};
```
- 数值 `scroll-top` 被原生 `scroll-view` **clamp 到 `maxScroll`（即底部）**，永远不滚出内容外，首点即正确。
- **递增哨兵**保证每次设值都不同：手动滚动后 ref 不跟随原生位置，同值重设不触发滚动，
  递增确保每次点击/每条新消息都能重新触发滚底。
- 末条变化 watcher（初次加载/收到新消息）与 `scrollToLatestMessage` 统一走 `scrollToBottom()`。
- 删除 `scrollAnchorID` / `setAnchor` / `scheduleAnchorClear` / `anchorClearTimer`
  及模板 `:scroll-into-view` 绑定和各处清锚点代码（定位原消息 `scrollToTargetMessage`
  本就用数值测量，不受影响）。

---

## 验证方式与边界

### 已执行
- **源码断言**：`node scripts/verify-im-history.js`（深历史重建契约 + 原子前插 + 滚底哨兵 + 无 `scroll-into-view` 绑定）。
- **聊天相关断言**：`verify-chat-read-gate.mjs`、`verify-chat-read-on-visible.js`、
  `verify-tuikit-cleanup.js`、`verify-media-send-diagnostics.js` 均通过。
- **双端构建**：`npm run build:mp-weixin`（含分包布局校验，主包 1.16MB）、`npm run build:h5` 均成功。
- **编译产物核对**：mp-weixin `message-list/index.wxml` 已无 `scroll-into-view`，
  `scroll-top="{{i}}"`、`scroll-anchoring="{{true}}"` 保留；`index.js` 滚底为 `P.value=1e9+ ++F` 递增哨兵。
- **H5 冒烟**：本地静态服务打开首页，TUIKit 引擎正常加载（LiteChat 1.6.22 / Engine-Lite 1.0.7 / UniversalAPI 2.4.1），
  无 JS/Vue 运行时错误；仅后端未启动的预期 `ERR_CONNECTION_REFUSED`（`localhost:8000/api/v1/*`）。

### 边界（如实说明）
- 会话窗口需 **IM 登录 + 后端运行 + 超 7 天历史会话**才能真机复现，
  本轮无法在认证态小程序真机运行时逐一点验按钮交互，滚底修复以**源码断言 + 双端构建 + 编译产物核对**为准。
- `verify-im-history-merge.mjs`（引擎级合并行为）因 `im-history.js` 早前引入 `@/` 别名 TS 依赖，
  裸 Node 无法解析而失败，属**既有问题**，与本轮滚动改动无关。

## 关键经验
1. 小程序 `scroll-into-view` 是「元素顶部对齐视口顶部」，**不是**「滚到元素可见」：
   锚末条会滚出内容外白屏，锚旧首条会在前插时前跳超一屏。滚底/锚定优先用数值 `scroll-top`（原生 clamp）。
2. 数值 `scroll-top` 同值重设不触发，手动滚动后 ref 不跟随原生位置 → 用**递增哨兵**强制重触发。
3. 消除前插过渡帧的本质是**原子化**：插入前预测量批次高度（离屏镜像），列表与目标 `scroll-top` 同一次 setData。
4. 小程序 `scrollOffset` 不返回 `scrollHeight`，内容总高需测包裹层；spinner 移出内容流避免干扰高度核算。
5. 平台差异：`scroll-anchoring` webview 仅 iOS、Skyline 3.6.2+ 默认开；安卓 webview 需 CSS `overflow-anchor`。