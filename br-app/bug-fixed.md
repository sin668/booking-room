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
