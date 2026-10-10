# Tasks: 退出系统登录同步退出 IM

- [x] 在 `br-app/src/utils/im.js` 新增导出 `resetIM()`：调用 `TUILogin.logout()` 并重置 `imInitialized`/`initPromise`/`imProfile`
- [x] 在 `br-app/src/store/modules/user.js` 的 `clearLocalSession()` 中调用 `resetIM()`
- [x] 扩展 `br-app/scripts/verify-im-peer-profile.js`：断言 `resetIM` 存在、logout+状态重置、store 退出时调用
- [x] 构建 mp-weixin 并通过断言脚本，提交推送 main
