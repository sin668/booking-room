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
