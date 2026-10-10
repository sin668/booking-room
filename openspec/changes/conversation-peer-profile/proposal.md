## Why

消息通知页「会话」TAB 已经能列出会话，但左右两侧都看不到对方的头像：发送者打开时看不到接收者的头像，接收者打开时既看不到发送者的头像，昵称也只能显示 IM 账号名。

根因不在页面渲染，而在数据源：`chat-uikit-engine-lite` 的会话模型 `getAvatar()` 读取 `userProfile.avatar`，`getShowName()` 读取 `remark || userProfile.nick || userID`。本系统只在 `/api/v1/chat/user-sig` 签发 UserSig，从未把用户的昵称与头像写入腾讯云 IM 的用户画像，因此双方拿到的 `userProfile` 只有 `userID`（即平台 `username`），头像为空。

## What Changes

- IM 登录成功后，把当前用户在本系统设置的昵称与头像写入腾讯云 IM 用户画像（复用已安装 SDK 的 `TUIUserService.updateMyProfile({ nick, avatar })`）。
- 用户在本系统修改昵称或头像后，重新推送到 IM，保证对方下次拉取会话列表即见新资料。
- 「会话」TAB 的未读红点数字（含 `99+` 上限）继续由 `TUIStore` 会话列表订阅与页面 `onShow` 重新拉取保证及时刷新；本次只验证，不新增代码。
- 不新增后端接口、不改数据库、不改页面模板。

## Capabilities

### Modified Capabilities

- `message-notification-ui`: 会话 TAB 的对方头像与昵称来源改为本系统用户资料（经 IM 用户画像承载）。

## Impact

- 影响代码：`br-app/src/utils/im.js`、`br-app/src/store/modules/user.js`，新增 `br-app/scripts/verify-im-peer-profile.js` 与 `package.json` 脚本注册。
- 依赖：仅使用已安装的 `@tencentcloud/chat-uikit-engine-lite`，无新增依赖。
- 外部：写入腾讯云 IM 用户画像（每次 IM 初始化一次调用；资料更新时再一次）。
- 回滚：还原这两个源文件即可，IM 侧画像为幂等覆盖写，无需数据迁移。
