## Why

消息通知页「会话」TAB 依赖腾讯云 IM 登录态展示对方头像/昵称与未读红点。当前退出系统登录（`userStore.logout` / `clearLocalSession`）只清理本地 token，从不退出 IM。由于 `ensureIM()` 用模块级 `imInitialized` 短路，A 退出后 IM 仍停在 A 的账号，B 再登录系统时 `ensureIM()` 直接返回、不会以 B 重新登录 IM，导致 B 的「会话」TAB 显示的仍是 A 的会话与对方资料，未读红点也归属错误账号。

## What Changes

- 退出系统登录时同步退出腾讯云 IM 登录（`TUILogin.logout`），并重置 IM 模块状态（`imInitialized`、`initPromise`、`imProfile`）。
- 重置后，下一个用户登录系统并进入会话 TAB 时 `ensureIM()` 会以新用户身份重新登录 IM，会话 TAB 显示正确的对方头像/昵称与未读红点。

## Impact

- Affected capability: `message-notification-ui`
- Affected code: `br-app/src/utils/im.js`（新增 `resetIM`）、`br-app/src/store/modules/user.js`（退出时调用）、`br-app/scripts/verify-im-peer-profile.js`（断言）
