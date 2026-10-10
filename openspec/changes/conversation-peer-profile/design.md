## 实现说明

会话行的渲染已经正确（`getAvatar()` 有值走 `<image>`，否则首字母兜底），需要补的是「IM 侧画像写入」这一环。

### 决策 1：写入方 = 客户端自己，走 SDK 原生 `updateMyProfile`

每个用户在 IM 登录成功后把自己的昵称/头像写进 IM 用户画像。这样对方（无论发送者还是接收者）拉到的会话 `userProfile` 就同时有 `nick` 与 `avatar`，且 TUIKit 聊天页气泡头像同步受益。

理由：`chat-uikit-engine-lite` 已导出 `TUIUserService.updateMyProfile(UpdateMyProfileParams{nick, avatar})`，属于已安装依赖的原生能力；相比之下由 br-server 调 IM REST 账号导入接口需要新增对外集成、密钥调用与「用户改头像后再次同步」的额外触发点，成本高且本地无法验证。

### 决策 2：触发点放在 `utils/im.js`，由 store 喂数据，避免循环依赖

`store/modules/user.js` 已经 `import { ensureIM } from '@/utils/im'`。若让 `utils/im.js` 反过来 import store 会形成环。因此在 `utils/im.js` 增加一个纯 setter：

- `setIMProfile(profile)`：缓存资料；若 IM 已就绪则立即推送，否则由 `ensureIM()` 登录成功后推送。
- `pushIMProfile()`（模块内私有）：过滤掉空的 `nick`/`avatar`，两者都为空直接返回；调用失败只 `console.warn`，不影响 `ensureIM()` 返回就绪。

store 在 `userInfo` 落地的两处调用 `setIMProfile`：`fetchUserInfo()`（登录/注册/autoLogin 都会经过）与 `updateProfile()`（用户改昵称、头像）。两个方向的时序都覆盖：IM 先就绪则立即推送，IM 后就绪则由 `ensureIM()` 补推。

### 决策 3：payload 只带非空字段

`updateMyProfile({ nick: '', avatar: '' })` 可能清空已有画像，因此只写入有值的字段。

### 决策 4：不改页面

`br-app/src/pages/notifications/index.vue` 的 `toConversationRow()` 已使用 `getShowName()`/`getAvatar()`，画像写入后无需改动；未读数量来自同一份会话列表，`TUIStore.watch(StoreName.CONV, { conversationList })` 在收到新消息时会更新红点，`onShow` 再补一次全量拉取覆盖小程序退后台断连的场景。

## 自检

`br-app/scripts/verify-im-peer-profile.js`（assert 风格，与仓库既有 `scripts/verify-*.js` 一致）断言：`im.js` 导出 `setIMProfile` 且 `ensureIM` 成功后调用推送；`updateMyProfile` 只使用 `nick`/`avatar` 两个 SDK 字段并过滤空值；store 在 `fetchUserInfo` 与 `updateProfile` 后同步；`utils/im.js` 不 import store（防环）；会话行仍读取 `getAvatar()` 并保留首字母兜底。
