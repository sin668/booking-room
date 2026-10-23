# Bug 修复记录

## 微信小程序生产环境 IM 聊天初始化超时

### 报错信息

- **调试模式（开发模式）**：可正常进入 TUIKit Chat 聊天窗口
- **关闭调试模式（生产环境）**：长时间显示"正在连接..."，最终提示 `"unknow failed error..."` 或 `"IM登录超时(15000ms)"`

### 根本原因

腾讯云 IM lite-chat SDK 在登录时需要通过 WebSocket 连接到腾讯服务器（触发 `SDK_READY` 事件后 login promise 才 resolve）。SDK 内部通过 `getconninfo` API 获取最优服务器地址，可能返回以下任意域名：

- `wss.im.qcloud.com` / `wss.tim.qq.com` / `wss.im.tencent.cn` / `wss.my-imcloud.com`
- 各区域节点：`wssidn.*` / `wssind.*` / `wssger.*` / `wssjpn.*` / `wsskr.*` / `wssksa.*` / `wsssgp.*` / `wssusa.*`（含 v6 变体）

微信小程序**调试模式会放宽域名校验**，因此只配置了 `wss.im.qcloud.com` 和 `wss.tim.qq.com` 时调试可正常连接。但**生产环境严格执行域名白名单**，当 `getconninfo` 返回的服务器不在白名单中时，`wx.connectSocket()` 直接失败，SDK 重试后放弃，`SDK_READY` 永不触发，login promise 挂起直到超时。

### 解决方案

在微信公众平台 → 开发管理 → 开发设置 → 服务器域名中，添加以下全部域名：

**socket 合法域名**（29 个）：

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

**request 合法域名**（4 个）：

```
https://api.my-imcloud.com
https://boce-cdn.my-imcloud.com
https://events.im.qcloud.com
https://web.sdk.qcloud.com
```

### 经验教训

1. 微信小程序**调试模式不校验域名白名单**，不能作为生产环境的验证依据，必须在关闭调试模式的真机上测试
2. 腾讯云 IM SDK 的 WebSocket 域名不是固定的，`getconninfo` 会根据用户地理位置返回最优节点，**必须把所有区域域名都加入白名单**
3. SDK 报错 `"unknow failed error..."`（注意拼写错误 `unknow`）是腾讯 SDK 内部抛出的，说明是 SDK 层面的连接失败

### 涉及文件

- `br-app/src/utils/im.js` — IM 初始化逻辑，添加了 `withTimeout()` 超时保护和错误信息暴露
- `br-app/src/pages-sub/edu-market/detail.vue` — 聊天入口页，展示具体错误信息
- SDK 源码：`node_modules/@tencentcloud/lite-chat/basic.js` — 域名列表和连接逻辑

---

## TUIKit 聊天输入框右侧表情/更多图标中间一块实心黑方块

### 报错信息

无 JS 报错、无编译告警，纯渲染问题：

- 聊天页（`TUIKit/components/TUIChat/index`）输入行右侧两个图标（表情、更多）各显示为**一块实心深色方块**，图标图形看不见
- 同一行左侧 mic 图标**一直正常**
- 截图实测方块色 `rgb(44,52,54)`，方块尺寸约 1em 见方、正好居中盖在 23px 图标中央
- **连续更换图标资产（五版 svg + 一版官方 PNG）后，方块逐像素没有任何变化**

### 根本原因

`br-app/src/static/icons/iconfont.css` 第 7 行为自家 mask-image 图标体系定义了**裸 `.icon` 基准规则**：

```css
.icon {
  background-color: currentColor;   /* 靠 mask-image 挖出图形 */
  width: 1em; height: 1em;
  display: inline-flex; ...
}
```

该文件被 `br-app/src/App.vue` 以 `@import '@/static/icons/iconfont.css'` **全局引入**，小程序端全局样式会命中所有页面与组件里的 `.icon` 元素。

而 TUIKit **原厂模板**（`git show b270e05` 引入 TUIKit 时即存在，非本项目改动）在输入图标上写的是：

```html
<Icon class="icon icon-face" ... />
<Icon class="icon icon-more" ... />
```

这些元素拿不到 iconfont 的 `mask-image`，于是 `background-color: currentColor` 直接画成一块 1em 见方的纯色方块盖在图标中央。`currentColor` 继承自 `br-app/uni.scss` 的主题文字色 `$text-primary: #2D3436` = `rgb(45,52,54)`，与截图实测 `rgb(44,52,54)` 一致——**颜色对上主题 token 即证明方块由 CSS 绘制，与图片解码无关**。mic 正常只是因为它没带 `.icon` 类。

同一泄漏还潜在影响 TUIKit 其他 `.icon` 元素：`common/Dialog`、`common/ImagePreviewer` 的 `icon icon-close`，`plugins/.../message-call-c2c` 的 `.icon`（它只声明了 `width/height:20px`，未覆盖 `background-color`），`common/Transfer`、`TUIGroup/create-group/group-introduction`、`common/DatePicker`。

### 解决方案

把 iconfont 基准样式的选择器从裸 `.icon` 改为**显式列出本文件定义的 23 个具名图标类**（`.icon-location, .icon-search, …, .icon-order`），全局规则在结构上就不再可能命中第三方组件的 `.icon`。

回归面已穷举核对：应用内 112 处用法全部是 `class="icon icon-<23 类之一>"`，**零处裸 `class="icon"`**；唯一的动态绑定 `pages/index/index.vue:75` 的 `entry.iconClass`（`icon-wallet/ticket/book/order`）与 `login.vue` 的 `icon-eye`/`icon-eye-off` 均在名单内，渲染不变。

验证：`dist/build/mp-weixin/app.wxss` 中已无裸 `.icon{...}` 规则，只剩分组选择器。commit `f398f74`。

### 走过的弯路（务必避免重复）

前五轮全部误判为"小程序 svg 渲染器不支持某个特性"，依次猜测：不支持 `stroke` → 不支持 `fill-rule="evenodd"` → 不支持 `A` 弧线命令 → 不支持同 path 多子路径挖孔 → 填充型 path 被按包围盒整块涂黑。对应 commit `85afc0b` → `cf3f2b6` → `8a15d93` → `eb3fe52` → `511040a`，全部无效。

- **反证一直摆在眼前**：正常显示的 mic 资产 `br-app/src/TUIKit/assets/icon/audio.svg` 里 `stroke` + `A` 弧线 + `fill-rule="evenodd"` + `transform` + 多子路径填充**全都在用**，且它的圆环 path 与手写的完全一致。
- **否证手段（下次照抄）**：对不同版本截图跑同一套 PIL 连通域暗像素统计。`eb3fe52`（填充版）与 `511040a`（纯描边版）**逐像素一致**（方块 776 vs 756 暗像素、fill 0.60 vs 0.58），只有被改动的描边圆环 bbox 从 34px 变 36px；换成官方 `face-uni.png`/`more-uni.png` 后仍是 763/743、0.57/0.56。**我的改动在数值上没有体现 = 目标层选错了**。
- 那次 svg→png（`9c452a4`）并不是修复，只是顺手采用了 TUIKit 对 uni 端的 png 约定（同族 `camera-uni.png`/`image-uni.png`）。

### 经验教训

1. 引入第三方组件库时，全局样式表**绝不能定义裸通用类名**（`.icon`、`.btn`、`.close`…）的可见属性（背景、尺寸）；要么加自家前缀，要么把基准样式挂在自己的具名修饰类上。
2. 排查第三方组件"多出实心色块"：**先 grep 全局 CSS 是否命中该元素类名**，再考虑资产；把异常区颜色对一遍主题 token，命中即确认是 CSS 画的。
3. 假设被截图否证一次就停手，不要在同一层继续猜第二种可能——第二轮无效时就该换层（资产 → 样式/DOM）。
4. 注意维护陷阱：以后新增第 24 个图标类，必须同时补进 `iconfont.css` 的基准名单，否则该图标会渲染成"完全不可见"（无尺寸无背景）。

### 涉及文件

- `br-app/src/static/icons/iconfont.css` — 修复点（基准选择器去裸 `.icon`）
- `br-app/src/App.vue` — 全局 `@import` 造成泄漏的路径
- `br-app/src/TUIKit/components/TUIChat/message-input/index.vue` — 受害元素（原厂 `class="icon icon-face"` / `icon-more`）
- `br-app/uni.scss` — `$text-primary: #2D3436`，方块颜色来源

---

## TUIKit 聊天文字输入框输入首字符就撑成两行

### 报错信息

无 JS 报错、无编译告警，纯渲染问题：

- 微信小程序端（mp-weixin）聊天窗口文字输入框，**未输入时是一行高度**；输入任意一个字符、文字还没换行，白色圆角输入框立刻变成两行高
- 现象只在小程序端出现，H5 端正常
- 该输入框由 commit `0015e6e` 从单行 `<input>` 改为多行 `<textarea auto-height>`，改动前不存在此问题

### 根本原因

`auto-height` 的原生 `<textarea>` **高度完全由组件自己算**，而当时把盒子的外观样式全压在了 textarea 身上：`padding: 8px 12px` + `border: 1px` + `min-height` + `background` + `border-radius`。

微信官方 textarea 文档里有两条决定性的说明：

1. `设置 auto-height 时，style.height 不生效` —— 高度由组件接管，外部只留下 min-height/padding 这类它会叠加计算的量
2. `disable-default-padding` **只对 iOS 有效** —— Android 侧组件自带默认内边距，无法用该属性去掉

于是 CSS 的上下 padding 与组件内部测量出的行高相互叠加（Android 还额外带自身默认内边距），第一次输入就把高度撑到约两行。换句话说：**问题不在 auto-height，也不在任何"行数"属性，而在于给一个自管高度的原生表单组件加了垂直盒子内边距**。

### 解决方案

把盒子外观交给外层容器，textarea 只保留纯内容区（commit `61e6c53`）：

```html
<div class="message-input-area-box">
  <textarea class="message-input-area" auto-height ... />
</div>
```

```scss
.message-input-area-box {
  box-sizing: border-box;
  min-width: 0;
  background: #fff;
  border: 1px solid #e5e8ee;
  border-radius: 20px;
  padding: 8px 12px;
  min-height: 38px;
}

.message-input-area {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  background: transparent;
  border: none;
  padding: 0;          // 关键：textarea 上不留垂直内边距
  font-size: 15px;
  line-height: 22px;
}
```

这样 textarea 的高度等于内容行高（一行 22px），盒子高度 = 22 + 16 + 2 = 40px，**空内容与单字符结果相同，不再跳变**；文字换行时 textarea 自然增高，盒子随之撑开。视觉尺寸与原设计一致，未引入任何 JS 高度计算。

验证：`npm run build:mp-weixin` 通过（主包 1.15MB），产物 `message-input-editor.wxml` 中 textarea 的 `padding` 已为 0、外观类落在新增的 `message-input-area-box` 上。**注意：本节按官方文档的生效范围推导出根因并落地修复，构建侧证据齐全，但"输入首字符不再跳成两行"仍需你在微信开发者工具/真机上做一次目视确认。**

### 走过的弯路（务必避免重复）

连错五轮，全部是在 textarea 自身的高度属性上打转，没有一条去查官方文档的生效范围：

| commit | 猜测 | 结果 |
| --- | --- | --- |
| `a039c0d` | 空 textarea 塌陷，加 `height: 38px` | 无效（auto-height 下 style.height 根本不生效，文档明写） |
| `de7376d` | 关掉 auto-height、用 JS 算高度 | 代码量大，用户要求撤回 → `a4bbd1e` revert |
| `b376d31` | `box-sizing` 内容区 20px < `line-height` 22px 放不下，改 `min-height: 40px` | 无效 |
| `1baa35d` | 小程序 textarea 有 `rows` 属性、默认 2 行，加 `:rows="1"` | **属性根本不存在**，无效 |
| `eec0bd7` | 列方向 flex 父容器把 textarea 拉伸，移除 `flex: 1` | 无效 |

- `min-height: 40px` 那一版还被本地一次未记录的编辑悄悄改回 `38px`，等于从未被真正验证过——排查期间要确认工作区文件与预期一致。
- 两次凭记忆断言原生属性默认值（`rows=2`）都是错的。**小程序组件的属性名与默认值必须以官方文档为准，不要按 Web/HTML textarea 或别的框架类推。**

### 经验教训

1. 原生表单组件（textarea / input / picker）一旦带上"自管高度/自管尺寸"的开关（`auto-height` 等），**外观盒子就要另起一层容器**，不要往组件上压 padding、border、min-height。
2. 排查这类"只在小程序端、只在某个交互之后出现"的样式问题，第一步是读官方组件文档的**属性生效范围与平台差异**（本例的 `disable-default-padding 仅 iOS`、`auto-height 下 style.height 失效`就是答案本身），而不是逐个属性试。
3. 同一个假设层连续两次无效即停手换层：五轮里有四轮仍在调 textarea 的高度数值。参见上一条图标问题的同类教训。

### 涉及文件

- `br-app/src/TUIKit/components/TUIChat/message-input/message-input-editor.vue` — 修复点（新增 `message-input-area-box` 外层容器，textarea 清空垂直内边距与盒子样式）
- `br-app/src/TUIKit/components/TUIChat/message-input/index.vue` — `:not(not)` 全局 flex 与 `.message-input-editor` flex 容器，排查时确认过不是拉伸来源


---

## 微信小程序生产环境语音消息发送失败（调试模式正常）

### 报错信息

- **调试模式（打开"不校验合法域名"）**：按住说话正常录音、正常发送，气泡与 Toast 都正常。
- **关闭调试模式（生产环境）**：按住说话正常录音，松手后气泡显示"发送失败"，Toast 显示 `Unknown failed. error: {"message": }`（注意 SDK 拼写 `failed`，用户看到的可能是 `fail` 的简写）。

### 根本原因

腾讯云 IM 小程序语音上传走的是**服务端下发的 COS 预签名地址**，不是固定主机。域名按 SDKAppID 分配，本项目 SDKAppID = **20049215**（来自 `br-server/.env` 的 `IM_SDK_APP_ID`），实际上传主机为 `20049215-sg.rich.my-imcloud.com`（新加坡区域节点）。

微信公众平台"服务器域名"配置**不支持通配符**，必须逐条填写完整主机名。`*.rich.my-imcloud.com` 这类写法在后台根本填不进去，也不会生效。

SDK 内部 `wx.uploadFile` 失败分支（`lite-chat/standard.js` 的 `_handleResponse`）把 `wx` 的 `errMsg` 整个丢弃，只留 `{code: +res.statusCode, message: JSON.stringify(res.data)}`。fail 回调里两者都是 `undefined`，于是 `code=NaN`（判假）、`message=undefined`（落回空串），最终 SDK 错误类 `Ws` 拼成 `Unknown failed. error: {"message": }`——**线上完全看不出是哪个域名被拦**，只能看到空 message。

### 解决方案

**1. 域名白名单**

在微信公众平台 → 开发管理 → 开发设置 → 服务器域名中，把以下域名加入对应类别（本项目实际使用的是新加坡节点）：

**uploadFile 合法域名**：

```
https://20049215-sg.rich.my-imcloud.com
```

**downloadFile 合法域名**（语音播放同样需要）：

```
https://20049215-sg.rich.my-imcloud.com
```

其他区域节点（按需添加，取决于腾讯云 IM 控制台分配）：

```
https://20049215-cn.rich.my-imcloud.com
https://20049215w4c.my-imcloud.com
```

**2. 代码层诊断兜底**

在 `src/utils/im.js` 的 `ensureIM` 登录前给 `TUIGlobal.uploadFile`（即全局 `wx.uploadFile`，SDK 每次调用时才取这个属性）包一层，记录本次上传的 `url` 与 `errMsg`；`message-input-audio.vue` 的失败提示优先显示它们。这样下次遇到同类问题，Toast 直接显示被拦的域名和 wx 原始 errMsg，不再只能看到空 message。

同时修正了 `sendAudioMessage` 的 `.then(onSendAudioFailure)` 误把成功当失败的 bug——改为只 `.catch`，成功时不再弹 Toast。

### 经验教训

1. 腾讯云 IM 小程序四类域名白名单（socket / request / uploadFile / downloadFile）中，**uploadFile / downloadFile 的域名是按 SDKAppID 分配的子域名**，不是固定主机；必须从实际上传失败日志或 Toast 里拿到真实主机名，不能凭官方文档的"示例"猜。
2. 微信小程序**调试模式不校验合法域名**，不能作为生产环境的验证依据；必须在关闭调试模式的真机上测试。
3. 微信公众平台**服务器域名配置不支持通配符**，必须逐条完整主机名。
4. SDK 的错误类会丢字段（本例中 `errMsg` 被整个丢弃），需要自己拦截 `wx` 原生 API 才能拿到真实失败原因。
5. 后台改完域名后，真机要**下拉删除该小程序再重新进入**，域名列表有客户端缓存，否则看着像"配了还是失败"。

### 涉及文件

- `br-app/src/utils/im.js` — `hookUploadDiagnostic` 拦截 `TUIGlobal.uploadFile`，记录 url + errMsg
- `br-app/src/TUIKit/components/TUIChat/message-input/message-input-audio.vue` — 失败 Toast 回显 url + errMsg；移除 `.then(onSendAudioFailure)` 避免成功也弹提示
- SDK 源码：`node_modules/@tencentcloud/lite-chat/standard.js` — 错误类 `Ws` 与 `_handleResponse` 的 fail 分支

## 发一条消息出现两条回调 + 消息刚发出就显示"已读"

### 报错信息

后端 uvicorn 访问日志里，发一条消息同一秒内出现四条请求：

```
GET  /api/v1/chat/messages?peer=05a0adcc33d44f58ae03caa0b537e033&limit=200   200 OK
GET  /api/v1/chat/messages?peer=c904bd6f84a147aeb3272f92616dc156&limit=200   200 OK
POST /api/v1/im/callback?CallbackCommand=C2C.CallbackAfterSendMsg&...&Sign=bde7c8fa...&RequestTime=1792662316   200 OK
POST /api/v1/im/callback?CallbackCommand=C2C.CallbackAfterMsgReport&...&Sign=bde7c8fa...&RequestTime=1792662316  200 OK
```

同时小程序端：消息刚发出去就马上从"未读"变成"已读"。

### 根本原因

**1. 两条 POST 回调不是重复，是两个不同的 CallbackCommand**

`C2C.CallbackAfterSendMsg`（发送落地）和 `C2C.CallbackAfterMsgReport`（对端已读上报）是两件事。回调鉴权 `Sign = sha256(Token + RequestTime)` 只精确到秒，两条回调落在同一秒里，所以 `Sign` 和 `RequestTime` 完全一样，看起来像同一条请求发了两次。

**2. 两条 GET 也不是同一客户端重复请求**

两条的 `peer` 参数分别是 `05a0adcc…`（brian77）和 `c904bd6f…`（Noah63007），是**两个不同登录用户的客户端各自拉自己视角的会话历史**。日志里的 `172.18.188.98` 是容器网关地址，不能用来判断调用方。

**3. 客户端确实存在过度轮询（真 bug）**

`src/utils/im.js` 的 `loadChatMediaMap` 用"列表里最新媒体时间 > 数据库快照最新时间"作为"要不要重拉"的判据，本意是给回调落库的秒级延迟留重试。但**回调开启之前发出的历史图片/语音永远不会进数据库**，该条件恒为真，只剩 2 秒节流挡着 → 聊天页停留期间每 2 秒打一次 `limit=200` 的会话历史接口。

**4. "秒已读"是真实已读上报，不是回调写坏了状态**

- TUIKit 引擎 `chat-uikit-engine-lite` 的 `updateMessageList` 在 `case "push" / "contact"` 分支里**无条件**调用 `chat.setMessageRead({conversationID})`（只有 `case "received"` 才判断 `enableAutoMessageRead`）。只要对端小程序停在聊天页，新消息一push 就整会话标记已读。
- SDK 侧 `openim.get_peer_read_time` 拿到对端已读时间后，把 `time <= peerReadTime && flow === 'out'` 的消息全部置 `isPeerRead = true` 并抛 `MESSAGE_READ_BY_PEER`，角标随即变"已读"。
- 生产库 `im_messages` 的 `read_at` 与发送时间相差 2~4 秒，和日志里同一秒的 `C2C.CallbackAfterMsgReport` 完全对得上。
- 角标渲染 100% 走 SDK 状态：`message-elements/read-status/index.vue` 与 npm 原版 `@tencentcloud/chat-uikit-uniapp` **逐字节相同**，本系统加的 OSS 覆盖只改 `payload` 里的图片/语音地址，不碰任何已读字段。

### 解决方案

`src/utils/im.js`：

1. 给重试加上限 `MEDIA_MAP_MAX_TRIES = 5`，并且每出现一条更新的媒体才重置计数（`mediaMapTarget`），保证"新发的图片有 5 次机会等回调落库，补不齐的历史媒体不再无限轮询"。
2. 判据顺序改为：数据库已覆盖 → 直接返回；重试次数用尽 → 直接返回；最后才是 2 秒节流。
3. 会话 ID 从消息自身取（`targets[0].message.conversationID`），不再由调用方传 `currentConversationID.value`——切会话时 `messageList` 可能先于 `currentConversationID` 更新，用旧 ID 会拉错对端历史并多打一次接口。

回归检查：`npm run test:chat-media-map`（`scripts/verify-chat-media-map.js`）。

### 经验教训

1. 判断"重复请求"要先按**参数**区分调用方，不要只看同一网关 IP；两条 GET 的 `peer` 不同就是两个客户端。
2. 重试判据必须同时有次数上限：只有时间节流的"等一个永远等不到的数据"，等于无限轮询。
3. `Sign`/`RequestTime` 只精确到秒，同一秒内的多条回调鉴权值相同，不能用来判断是否重复投递；要按 `CallbackCommand` 区分。
4. 已读状态由**对端客户端**上报决定，服务端回调只是把它抄进数据库；排查"秒已读"要先确认对端是否停在聊天页（引擎在 push 时无条件 `setMessageRead`），而不是查回调代码。后来定位到真正的主因是会话绑定没随页面隐藏释放，见下一节。
5. 怀疑 TUIKit 组件被我们改坏时，先和 `node_modules/@tencentcloud/chat-uikit-uniapp` 里的原版 `diff` 一次，比读代码猜快得多。

### 涉及文件

- `br-app/src/utils/im.js` — `loadChatMediaMap` 有界重试；`applyChatMediaUrls` 从消息自身取会话 ID
- `br-app/src/TUIKit/components/TUIChat/message-list/index.vue` — 调用点去掉 `currentConversationID`
- `br-app/scripts/verify-chat-media-map.js` — 上述约束的回归检查
- SDK 源码：`node_modules/@tencentcloud/chat-uikit-engine-lite/index.js` — `updateMessageList` 的 `push`/`contact` 分支无条件 `setMessageRead`
- SDK 源码：`node_modules/@tencentcloud/lite-chat/basic.es.js` — `get_peer_read_time` 回写 `isPeerRead`、`_initC2CReadReceiptInfo`

## 对方没打开聊天窗口，消息却 1~4 秒就变"已读"

### 现象

- 发送方气泡刚发出就从"未读"翻成"已读"，接收方表示没打开过聊天窗口。
- 生产库 `im_messages` 里 `read_at - msg_time` 大量是 1~4 秒：

```
id  sent(+08)            read_at               delta  from->to
11  2026-10-23 08:28:12  2026-10-23 00:28:14      2s  05a0adcc->c904bd6f
 9  2026-10-23 08:20:01  2026-10-23 00:20:03      2s  c904bd6f->05a0adcc
 1  2026-10-22 17:40:08  2026-10-22 09:42:27    139s  05a0adcc->c904bd6f
```

  同一对账号，1~4 秒和 139 秒都出现过，说明不是网络抖动，而是接收端有没有"绑定这个会话"的差别。

### 根本原因

腾讯云 IM 的已读只由**接收端客户端**调用 `chat.setMessageRead()` 产生，服务端回调只是抄写。TUIKit 引擎会自动调用它，而它的判据只有 `currentConversationID`，**完全不关心聊天页是否可见**：

- `chat-uikit-engine-lite/index.js` 的 APP store 默认 `enableAutoMessageRead: true`；
- `updateTargetMessageList()` 的 `case "received"`（`onMessageReceived` 走的分支）里 `o && chat.setMessageRead({conversationID: currentConversationID})`，只要消息属于当前绑定会话就上报；`case "push" / "contact"` 更是无条件上报；
- `switchConversation(id)` 一绑定就对会话上报已读，且 `currentConversationID` 只由 `switchConversation` / `deleteConversation` 写入；
- 引擎收到消息后先按 `message.conversationID === currentConversationID` 过滤，过滤结果为空就直接返回，不上报。

聊天页原来只在 `onUnload` 里 `reset()` 释放会话。但 uni-app 小程序端还有 `onHide`：用户从聊天页 `navigateTo` 跳到别的页面，或把小程序切到后台时，页面仍在栈里、不会 `onUnload`，会话因此一直绑着。于是接收人明明不在聊天窗口，新消息一到达就被引擎自动上报已读，发送方 1~4 秒内看到"已读"。

### 解决方案

把「会话绑定」和「聊天页可见」绑在一起（`br-app/src/TUIKit/components/TUIChat/index.vue`）：

- `onLoad` 记录本次打开的 `conversationID`（不能依赖 store，切会话时可能还是旧值）；
- `onHide` → `reset()` 释放会话，页面不可见期间引擎不会自动上报，未读红点也才正确；
- `onShow` → 仅在确实被 `onHide` 释放过时，用记录的 ID 重新 `initChat({ conversationID })` 绑回，此时上报已读才等于"用户真的看了"；首次进入 `onLoad` 已绑定，靠 `releasedOnHide` 守卫避免重复绑定；
- `onUnload` 原有 `reset()` 保留。

`TUIChatKit.init()` 有 `isInitialized` 短路，重复调用安全。

### 验证

- `scripts/verify-chat-read-gate.mjs`：用**真实引擎包**注入假 `chat`，喂同一条 `C2Cpeer1` 的消息，断言「绑定 C2Cpeer1 → 恰好一次 `setMessageRead`」「`currentConversationID` 释放 → 零次」「绑到别的会话 → 零次」。这条直接证明释放会话能止血，而不是只读压缩代码猜。
- `scripts/verify-chat-read-on-visible.js`：锁住源码约束（引入 `onShow/onHide`、`onHide` 里 `reset()`、`onShow` 用 `pageConversationID` 绑回、`onUnload` 仍释放）。
- `npm run build:mp-weixin` 后检查产物：`dist/build/mp-weixin/TUIKit/components/TUIChat/index.js` 里 `onHide(()=>{r||(r=!0,_())})`、`_ = () => switchConversation("")` 均在。

### 经验教训

1. 第三方 SDK 的"自动"行为要查它的**判据变量**，不要按常识推断。引擎自动已读的判据是 `currentConversationID`（会话有没有绑），不是"页面可见"，所以只写 `onUnload` 不够，小程序还有 `onHide`（跳页 / 切后台）这条路径。
2. `onLoad → onShow` 首次进入都会触发，用 `releasedOnHide` 这类状态守卫区分「首次」和「返回」，别在 `onShow` 无条件重绑。
3. 会话释放会连带 `TUIStore.reset(CHAT, ['messageList', ...])`，返回聊天页要重新拉一次历史；先确认重新绑定用的是页面入参里的会话 ID，否则会拉错对端。
4. 判断是不是"自动已读"造成的，看数据库 `read_at - msg_time` 的分布最省事：1~4 秒是引擎自动上报，几十上百秒才是真人打开窗口，同一对账号两种值并存就说明绑约未释放。
5. IM 已读按**账号**统计：同一账号在开发者工具或另一台手机上停在聊天页，秒已读同样会发生，这类不属于本 Bug，别把它当修复失败。
6. 光读压缩产物不足以证明修复有效，能注入假对象跑真实包就做，`process.exit(0)` 收尾（引擎有常驻定时器）。

### 涉及文件

- `br-app/src/TUIKit/components/TUIChat/index.vue` — `onLoad` 记录会话 ID、`onHide` 释放、`onShow` 绑回
- `br-app/scripts/verify-chat-read-gate.mjs` — 引擎自动已读判据的行为验证
- `br-app/scripts/verify-chat-read-on-visible.js` — 聊天页生命周期约束的源码断言
- `br-app/package.json` — `test:chat-read-gate`、`test:chat-read-on-visible`
- SDK 源码：`node_modules/@tencentcloud/chat-uikit-engine-lite/index.js` — `enableAutoMessageRead` 默认 true、`updateTargetMessageList` 的 `received` 分支、`switchConversation` 上报已读

## 聊天窗口只能往前翻 7 天，更早的消息一片空白

### 现象

- 打开与他人的单聊，点「查看更多」把 SDK 漫游历史翻到底之后按钮就消失，再往前的消息一条都看不到。
- 数据库 `im_messages` 里其实有更早的记录（服务端回调一直在落库），但聊天页从没读过它们。

### 根本原因

1. **腾讯云 IM 单聊消息云端只免费漫游 7 天**（官方文档《消息漫游》：体验版与专业版均为 7 天，延长时长要单独开通增值服务；富媒体文件的存储时长与漫游一致）。`getMessageList()` 翻到漫游头部后 `isCompleted` 置真，组件的「查看更多」是 `v-if="!isCompleted"`，于是彻底封口。
2. 数据库镜像是 2026-10-22 才开启回调开始写的，**比 IM 漫游窗口更晚**，所以不能整体换成读数据库：否则回调开启之前那 7 天内的消息反而消失了。两边必须是「SDK 负责自己的窗口，数据库负责窗口之前」。
3. 原来读数据库只为一件事——把图片/语音地址换成转存后的 OSS 地址（`applyChatMediaUrls`）。它按「秒数 + 收发方向 + 元素类型」这种模糊键去猜哪条 SDK 消息对应哪条库记录，同秒同类多条会错配，还要为重试控制加一堆模块级状态。数据库既然已经有 `MsgKey`，就不该再靠猜。

### 解决方案

**服务端补齐重建所需的事实**（`br-server`）：

- `im_messages` 增加 `cloud_custom_data` / `is_revoked` / `revoke_time`，随消息落库 `CloudCustomData`（引用回复的内容就塞在这里），迁移见 `alembic/versions/2026_10_23_1100-j5k1l7m3n9p4_...py`。
- 新增 `C2C.CallbackAfterMsgWithDraw` 分发与 `apply_msg_withdraw()`：按 `MsgKey` 只标状态、不删记录，重复投递靠 `is_revoked is false` 天然幂等。
- `GET /api/v1/chat/messages` 排序改成 `msg_time desc, msg_seq desc, id desc`（对齐 IM 单聊「先 MsgTime、同秒按 MsgSeq」的口径），并把 `elements`(原始 MsgBody)、`cloud_custom_data`、`is_revoked`、`msg_seq`、`im_from_account`、`im_to_account`、`media_url`/`oss_url`、`is_read` 全部回给客户端。

**客户端按 SDK 消息结构重建**（`br-app/src/utils/im-history.js`）：只重建 `text/image/sound/face/custom`，其余类型一律跳过——消息列表把认不出的类型落到 `v-else` 的 `MessageRevoked` 分支，会显示成「撤回了一条消息」。payload 结构按渲染组件的契约来：图片 `payload.imageInfoArray[0].{url,width,height}`、语音 `payload.{url,second}`、自定义 `payload.extension`，媒体地址优先用转存好的 `oss_url`。`ID` 用 `msg_key`，`status` 固定 `success`（回调只落 `SendMsgResult == 0` 的消息），`isPeerRead` 由 `is_read` 推导。

**翻页分工**（`message-list/index.vue`）：`getHistoryMessageList()` 先看 SDK 是否到头，没到头继续走 `getMessageList()`；`isCompleted` 为真且是单聊时才用当前最早一条消息的 `time` 作 `before` 游标向数据库取更早一页，`TUIChatService.updateMessageList(messages, 'unshift')` 注入。「查看更多」显示条件改成 `!isCompleted || (!isGroup && dbHasMore)`，切会话时重置 `dbHasMore`（引擎 `switchConversation` 会清空 CHAT store 的消息列表）。

### 为什么是 unshift

`chat-uikit-engine-lite` 的 `updateTargetMessageList()` 里只有 `case "received"` 会 `chat.setMessageRead()`，`case "push" / "contact"` 更是**无条件**上报已读；`case "unshift"` 只做三件事：按 `ID` 过滤掉已存在的、把新消息并进列表、`sortMessageList()` 重排，**完全不碰已读**。把几十条几年前的历史用 `push` 注进去，等于替对端把整段历史标成已读——这正是上一节「秒已读」的同一个坑，别在补齐历史时再踩一次。

### 验证

- `scripts/verify-im-history-merge.mjs`：用**真实引擎包**喂假 `chat`，把数据库行重建出的消息与一条 SDK 消息一起 `unshift`，断言「按 ID 去重、深历史前插且时间升序、`setMessageRead` 零次」，同时锁住重建字段的渲染契约（`getMessageContent().url` 拿到的是 OSS 地址）。
- `scripts/verify-im-history.js`：源码断言旧的媒体地址替换逻辑确实清干净、`fetchImHistoryPage` 只对 `C2C` 会话发请求、注入只走 `unshift`。
- `br-server` `pytest tests/test_im_callback_sync.py`（撤回标记与幂等、`CloudCustomData` 落库、历史接口返回重建字段、`before` 游标严格更早）。

### 已知边界（都是有意接受，不是待修）

- 深历史消息不是 SDK 消息实例，长按菜单里的撤回/删除/转发点了不会生效，最多报个错；读它、看它、找它都正常。
- 回调开启（2026-10-22）之前、又超出当前漫游窗口的消息，两个来源都没有，看不见也补不回来。
- 媒体转存失败的记录没有 `oss_url`，深历史里仍会用 IM 的 COS 地址，小程序没配那个域名就显示占位图。

### 经验教训

1. 第三方 IM 的"历史"受服务商配额限制，**免费档位的能力边界要先查官方文档再设计数据源**。7 天漫游决定了数据库镜像是必需项，不是优化项。
2. 新增数据源时别做模糊匹配。`「秒+方向+元素类型」`猜对应关系这种设计，只有在两边没有共同主键时才被迫接受；本例早就有 `MsgKey`，直接把它当 `ID` 就干净了。
3. 往 TUIKit 的消息 store 注入数据前，先去压缩产物里确认 `updateTargetMessageList` 的分支副作用（尤其会不会上报已读），选对合并类型比写多少防御代码都管用。
4. 未知类型宁可不显示。消息列表的 `v-else` 分支是"撤回消息"，把认不出的元素类型塞进去等于给用户造假记录。
5. 游标要写成严格比较（`before = 最早一条的 msg_time`，SQL 用 `<`），等号会让边界那条在上一页下一页各出现一次。

### 涉及文件

- `br-server/app/models/im_message.py`、`br-server/alembic/versions/2026_10_23_1100-j5k1l7m3n9p4_add_im_message_history_rebuild_fields.py` — 三个新列
- `br-server/app/services/im_callback_service.py` — `CloudCustomData` 落库、`apply_msg_withdraw()`
- `br-server/app/api/routes/im_callback.py` — 分发 `C2C.CallbackAfterMsgWithDraw`
- `br-server/app/api/routes/chat.py` — 排序口径与重建字段
- `br-app/src/utils/im-history.js` — 数据库行 → SDK 消息结构
- `br-app/src/utils/im.js` — `fetchImHistoryPage()`，删掉媒体地址映射
- `br-app/src/TUIKit/components/TUIChat/message-list/index.vue` — SDK 到头后转数据库翻页，`unshift` 注入
- `br-app/scripts/verify-im-history.js`、`br-app/scripts/verify-im-history-merge.mjs` — 替代 `verify-chat-media-map.js`

## 主包内不应存在主包未使用的 JS 文件：utils/im-history.js

### 现象

- 深历史功能上线后，微信开发者工具构建产物提示：`主包内不应该存在主包未使用的JS文件：utils/im-history.js`。
- 文件确实在 `dist/build/mp-weixin/utils/` 下，但主包没有任何页面引用它——只有 `TUIKit/components/TUIChat/message-list` 这个子包页面在用。

### 根本原因

uni-app 编译 mp-weixin 时把 `src/utils/*.js` 整体提升到主包的 `utils/`，不按「谁引用」下沉到分包。项目里 `src/utils` 大部分模块（`auth.js`、`request.js`、`im.js`）主包真的在用，所以这个提升平时是对的；`im-history.js` 是第一个只被 `TUIKit` 子包引用的 utils，于是撞上了微信的「主包未使用 JS」检查。

同类问题项目里早有解法：`scripts/post-build-move-assets.js` 在 build 之后把只被 TUIKit 用到的 `assets/` 图标和 `common/assets.js` 搬进 `TUIKit/`，并改写两侧相对 `require`。缺的只是把这套机制延伸到 utils JS。

### 解决方案

1. `post-build-move-assets.js` 增加 `MOVES` 表和 `moveMainPackageJs()`：按表把主包 JS 搬进子包，搬迁时改写该文件自身对外的 `require`（基准从旧目录换成新目录），再全量扫描子包目录，把指向旧路径的 `require` 改成指向新路径。
2. 新增产物守卫 `scripts/verify-mp-subpackage-layout.js`，接进 `build:mp-weixin` 末尾，也在 `test:mp-subpackage-layout` 单跑。两条断言：每条相对 `require` 都能解析到真实文件；主包 JS 若引用者全部落在同一个子包，就报错并提示「加进 MOVES」。以后再把只被子包用的模块写进 `src/utils`，构建阶段就会自己报出来，不用等开发者工具提醒。
3. 用显式 `MOVES` 表而不是自动搬迁：被两个子包共享的文件搬进任意一个都会让另一个找不到，自动化只能挑一个错的。表里一行一条，人工判断归属。

### 走过的弯路

- 第一版改写「消费者 require」时，基准目录错用了目标文件的新目录，`message-list/index.js` 里的 `../../../utils/im-history.js` 被写成了 `./im-history.js`，构建时被自己的新守卫拦下（`require("./im-history.js") 解析不到文件`）。基准必须是**引用方所在目录**，不是被引用文件所在目录。

### 验证

- `npm run build:mp-weixin` 输出 `Moved utils/im-history.js → TUIKit/utils/im-history.js (rewrote 1 require)`、`Main package size: 1.15MB`、`mp subpackage layout checks passed (182 js, subpackages: pages-sub, TUIKit)`。
- 产物核对：主包 `utils/` 已无该文件；`TUIKit/utils/im-history.js` 自身对 vendor 的引用改写为 `../../common/vendor.js`；`TUIKit/components/TUIChat/message-list/index.js` 引用为 `../../../utils/im-history.js`。

### 经验教训

1. uni-app 的 `src/utils` 一律进主包，**新增只给分包页面用的 utils 时，同步在 `MOVES` 加一行**，否则主包体积和「未使用 JS」告警都会找上门。
2. 搬文件必须两侧一起改写：被搬文件自己的 `require` 是「旧目录 → 新目录」，引用它的人是「以引用方目录为基准」，两个基准不一样，很容易只改一半。
3. 这类「构建产物布局」问题适合用产物级断言守，源码级断言守不住——编译器改的是路径，不是代码。

### 涉及文件

- `br-app/scripts/post-build-move-assets.js` — `MOVES` 表、`moveMainPackageJs()`、`resolveRelative()` / `relativize()` / `rewriteRequires()`
- `br-app/scripts/verify-mp-subpackage-layout.js` — 新增产物守卫
- `br-app/package.json` — `build:mp-weixin` 链尾接入守卫，新增 `test:mp-subpackage-layout`
