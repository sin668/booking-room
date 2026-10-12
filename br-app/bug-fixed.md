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
