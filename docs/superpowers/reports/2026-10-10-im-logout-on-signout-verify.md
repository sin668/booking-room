# 验证报告: im-logout-on-signout

**日期**: 2026-10-10
**验证模式**: full（存在 delta spec）
**结论**: PASS

## 背景

用户诉求：A 登录系统同时登录 TUIChat，退出系统登录同时退出 TUIChat 登录；切换到 B 登录时 IM 也以 B 重新登录，「会话」TAB 正确显示对方（A）头像/昵称与带数字的未读红点，点击进入与 A 的会话窗口。

根因：`ensureIM()` 用模块级 `imInitialized` 短路，退出系统登录时从不登出 IM，导致换账号后 IM 停留在上一用户会话。

## 检查清单

| # | 检查项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | tasks.md 全部完成 [x] | PASS | 4/4 checked |
| 2 | 改动文件与 tasks 一致 | PASS | im.js（resetIM）、user.js（clearLocalSession 调用）、verify 脚本 |
| 3 | 编译通过 | PASS | `npm run build:mp-weixin` exit=0，build 证据已登记 |
| 4 | 相关测试通过 | PASS | `node scripts/verify-im-peer-profile.js` exit=0 |
| 5 | 无安全问题 | PASS | 登出清理本地会话与 IM 状态，无新增密钥/注入面 |
| 6 | 集成代码审查 | PASS | 见下 |
| 7 | 核心/边界场景 | PASS | 见 delta spec 场景覆盖 |

## 集成代码审查

- `im.js resetIM()`：`if (!imInitialized) return` 幂等；`await TUILogin.logout()` 失败进 catch 打 warn；`finally` 无条件重置 `imInitialized/initPromise/imProfile` — 即使登出网络异常也保证下次 `ensureIM()` 重新登录。
- `user.js clearLocalSession()`：`resetIM().catch(()=>{})` fire-and-forget，不阻塞退出 UX；`clearLocalSession` 是 `logout()` 与设置页登出的唯一汇聚点，覆盖全部退出路径。
- 无循环依赖：store 引 im.js，im.js 不反向引 store（既有断言仍成立）。

## Delta Spec 场景覆盖（message-notification-ui / ADDED: IM sign-in follows system sign-in and sign-out）

- **Sign out of system also signs out of IM**：`clearLocalSession → resetIM → TUILogin.logout`，脚本断言 logout 调用 + 状态重置 ✓
- **Next user gets their own IM session**：`imInitialized=false` 后 `ensureIM()` 不再短路，重新 `TUILogin.login` 以新账号登录 ✓
- **Receiver sees sender profile + unread badge after switch**：渲染口径与未读释放由 conversation-peer-profile / conversation-unread-badge 保证，本次仅补登出环节 ✓

## WARNING

- 换账号后「会话」列表/未读需在真机验证 IM SDK 在 `TUILogin.logout` + 重新 login 后 store 是否彻底清空旧账号缓存；源码断言与构建已覆盖逻辑正确性，端到端多账号切换建议真机回归。

## SUGGESTION

- `TUIChatEngine.login` 无对应 logout，依赖 `TUILogin.logout` 触发的 SDK_NOT_READY 复位引擎；若后续发现引擎残留，可补充引擎级 reset。

## 最终结论

**PASS** — 7 项全通过，无 CRITICAL/IMPORTANT。可归档。
