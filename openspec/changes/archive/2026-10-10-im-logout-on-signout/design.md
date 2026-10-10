# Design: 退出系统登录同步退出 IM

## 决策 1：新增 `resetIM()` 而非只在页面 onUnload 登出

`ensureIM()` 用模块级 `imInitialized` 短路；只要它没被重置，换用户登录时就不会重新 `TUILogin.login`。因此在 `br-app/src/utils/im.js` 新增导出 `resetIM()`：`await TUILogin.logout()`，`finally` 里把 `imInitialized=false`、`initPromise=null`、`imProfile=null`，使下一次 `ensureIM()` 以新用户重新登录并重新推送画像。

## 决策 2：在 store 清理本地会话时调用 resetIM

`clearLocalSession()` 是所有登出路径的唯一汇聚点（`logout()` 与设置页直接调用都会经过它）。在其中调用 `resetIM()`，保证退出系统登录一定退出 IM。`clearLocalSession` 保持同步返回，`resetIM()` 以 fire-and-forget 方式触发并 `catch` 兜底，不阻塞退出 UX。

## 决策 3：不改动会话 TAB 渲染与未读释放逻辑

对方头像/昵称、未读红点与离开聊天页释放当前会话已由 conversation-peer-profile / conversation-unread-badge 覆盖，本次只补「退出即登出 IM」这一环，不改渲染。

## 决策 4：用断言脚本验证，不引入测试框架

沿用 `br-app/scripts/verify-im-peer-profile.js` 的源码断言方式，新增对 `resetIM` 存在、`clearLocalSession` 调用 `resetIM`、以及 `resetIM` 内 `TUILogin.logout` + 状态重置的断言。
