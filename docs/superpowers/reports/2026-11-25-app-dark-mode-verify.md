# app-dark-mode 验证报告

- 变更：`openspec/changes/app-dark-mode`
- 工作流：tweak（verify_mode: full）
- 日期：2026-11-25
- 基线：`675855a`；实现提交：`d035d88`
- 检查命令：`comet check run app-dark-mode verify --local -- sh -c "cd br-app && npm run test:dark-mode && npm run build:mp-weixin && npm run build:h5"`（exit=0）

## 一、完整验证检查项

| # | 检查项 | 结果 | 证据 |
| --- | --- | --- | --- |
| 1 | tasks.md 全部任务完成 | PASS | 12/12，`comet state tasks` 显示 completed=12 |
| 2 | 实现符合 design.md 高层设计 | PASS | `uni.scss` 变量间接引用、`App.vue` 双套 token、35 页根节点 `themeClass`、`themeMixin` 注册 |
| 3 | 无独立 Design Doc（tweak 不产出 `docs/superpowers/specs/`） | 跳过 | 本 change 无该产物 |
| 4 | 能力规格场景全部通过 | PASS | 见下方场景核对 |
| 5 | proposal.md 目标满足 | PASS | 开关驱动、全业务页面覆盖、TUIKit 排除、原生配色同步 |
| 6 | delta spec 与 design 无矛盾 | PASS | 首轮验证发现原生导航栏仅在切换时生效，已回 build 修复并在 design.md 第 5 条记录 `onMounted` 重新应用 |
| 7 | 关联设计文档可定位 | 跳过 | tweak 无独立设计文档 |

## 二、规格场景核对

| 场景 | 实现证据 |
| --- | --- |
| 打开深色开关立即生效 | `settings/index.vue` 的 `darkMode` setter → `themeStore.setMode`；`themeClass` 为响应式 computed，`.theme-dark` 覆盖 token |
| 关闭恢复浅色 | 同上，`setMode('light')` 返回浅色 token |
| 重启后恢复深色 | `store/modules/theme.js` 同步读取 `theme_mode`；`App.vue` `onLaunch` 调用 `init()` |
| 业务页面跟随主题 | `verify-dark-mode.js` 校验 35 个页面根节点均绑定 `themeClass`，且 17 个 token 全部走 `var()` |
| 聊天页排除 | `src/TUIKit/**` 未改动，页面扫描显式跳过该目录 |
| 原生栏同步 | `setNavigationBarColor`/`setTabBarStyle`/`setBackgroundColor` 于切换时调用；`themeMixin.onMounted` 在每个新页面重新应用（该 API 仅作用于当前页面） |
| 设置开关反映当前模式 | `darkMode` computed getter 读取 `themeStore.isDark` |

## 三、构建与测试

- `npm run test:dark-mode`：通过（17 token / 35 页面）
- `npm run build:mp-weixin`：通过（含 AppID 写入、TUIKit 资源搬运、分包布局校验 188 js）
- `npm run build:h5`：通过

### 存量失败说明（非本变更引入）

`npm run test:scripts` 中 8 项脚本在基线 `675855a` 上同样失败，已用 `git archive HEAD` 导出基线代码复跑确认：

| 脚本 | 基线失败原因 |
| --- | --- |
| test:profile-links | 断言 `/pages/wallet/...`，基线页面已是 `/pages-sub/...` |
| test:refactor | 断言文案 `已预约`，代码为 `confirmed` |
| test:activity-coupon | 断言首页活动链接 `/pages/activity/detail?id=` |
| test:course-schedule | 断言日期文案 `2026-08-18日`，代码为 `2026-08-18` |
| test:profile-menu | 断言「我的消息」跳转绑定 |
| test:conversation-tab、test:im-peer-profile | 引用已迁移的 `src/pages/notifications/index.vue` |
| test:im-history-merge | 纯 Node 环境无法解析 `@/TUIKit` 别名 |

本变更仅修改样式与 class 绑定，不涉及上述逻辑，故不纳入修复范围。

## 四、风险与安全

- 无新增依赖、无网络请求、无密钥或敏感信息写入。
- 主题偏好仅存本地 `theme_mode` 键，无服务端状态变更。
- 代码审查：`review_mode: off`，按配置跳过自动代码审查；由本报告的场景核对与构建/脚本检查覆盖正确性验证。

## 结论

全部检查项通过，无 CRITICAL/IMPORTANT 问题，可进入归档。
