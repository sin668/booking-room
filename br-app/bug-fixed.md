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

## TUIKit 小程序端输入栏表情/更多图标不显示

### 报错信息

微信小程序中聊天输入栏右侧的表情按钮和更多按钮区域为空白，不显示任何图标。H5 端正常。

### 根本原因

原版 TUIKit 使用 `<i class="icon">` + CSS `background-image: url(...)` 渲染图标，且图标资源为 SVG 格式。微信小程序不支持：

1. 内联 SVG（无法作为 background-image 引用）
2. `<i>` 空元素在小程序端无法正确渲染背景图
3. 小程序的 CSS 引擎对 background-image 外部引用的处理与 H5 不同

### 解决方案

改用 TUIKit 提供的 `CommonIcon` 组件（内部根据平台条件渲染 `<img>` 或 `<image>`），图标资源使用 PNG 格式：

```html
<CommonIcon
  class="icon icon-face"
  :file="faceIcon"
  :size="'23px'"
  :hotAreaSize="'3px'"
  @onClick="changeToolbarDisplayType('emojiPicker')"
/>
```

```js
import faceIcon from '../../../assets/icon/face-uni.png';
import moreIcon from '../../../assets/icon/more-uni.png';
```

### 涉及文件

- `br-app/src/TUIKit/components/TUIChat/message-input/index.vue` — 输入栏组件，使用 CommonIcon + PNG 图标
- `br-app/src/TUIKit/components/common/Icon.vue` — CommonIcon 组件，`isApp || isWeChat` 时用 `<image>`，否则用 `<img>`
- `br-app/src/TUIKit/assets/icon/face-uni.png`、`more-uni.png` — PNG 图标资源

## TUIKit 小程序端图标被 flex 容器拉伸堆积

### 报错信息

输入栏的表情、更多图标显示为变形的大方块，图标之间间距异常，堆积在一起。

### 根本原因

CommonIcon 组件外层 `.message-input-icon` 容器和内部 `.icon` 元素在 flex 行布局（`audio-main-content-line`）中未限制收缩，被相邻的 textarea（`flex: 1`）挤压，导致图标容器宽度被压缩到最小、内部布局变形。

### 解决方案

为图标容器和内部元素显式设置 `flex: 0 0 <size>` 禁止伸缩：

```scss
.message-input {
  &-icon {
    flex: 0 0 23px;
    width: 23px;
    height: 30px;
    margin-left: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .icon {
    flex: 0 0 auto;
  }
}
```

### 涉及文件

- `br-app/src/TUIKit/components/TUIChat/message-input/index.vue` — `.message-input-icon` 和 `.icon` 样式
- `br-app/src/TUIKit/components/TUIChat/message-input/message-input-audio.vue` — `.audio-message-icon` 同理设置 `flex: 0 0 23px`

## TUIKit 小程序端输入框首字符即放大（textarea auto-height）

### 报错信息

微信小程序聊天输入框，输入第一个字符时输入框就从矮状态跳变到 38px 高度，视觉上像是"放大"了。预期行为：输入框应保持单行高度，仅在文字换行到第二行时才自动增高。

### 根本原因

uni-app 的 `<textarea auto-height>` 在空内容时渲染为平台默认最小高度（约 24-30px），而非 CSS `min-height` 设定值。当用户输入第一个字符后，auto-height 机制介入，将高度设为 `min-height: 38px`（padding 8+8 + line-height 22 + border 1+1），产生 8-14px 的跳变。

### 解决方案

添加显式 `height: 38px` 与 `min-height: 38px` 配合。`height` 固定初始状态高度，`auto-height` 在内容超过一行时突破该高度继续增长：

```scss
.message-input-area {
  // ...
  padding: 8px 12px;
  height: 38px;       // 锁定单行高度，空/有内容视觉一致
  min-height: 38px;   // auto-height 增长的下限
  font-size: 15px;
  line-height: 22px;
}
```

### 涉及文件

- `br-app/src/TUIKit/components/TUIChat/message-input/message-input-editor.vue` — textarea 样式
