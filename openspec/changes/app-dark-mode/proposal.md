## Why

设置页「通用」分组已有「深色模式」开关，但当前只修改页面内的本地布尔值，没有任何视觉与状态副作用，属于占位功能。用户需要在弱光环境下使用 App，并且该开关必须真正驱动全 App 视觉主题。

## What Changes

- 新增全局主题 token 层：`uni.scss` 的语义色改为 CSS 变量引用，`App.vue` 定义浅色/深色两套 token。
- 新增 `theme` store，持久化 `theme_mode`（`light`/`dark`），并提供主题类名与原生 UI 同步。
- 新增全局 `themeMixin`，向所有页面提供 `themeClass`。
- 设置页「通用 - 深色模式」开关改为读写 store，切换即时生效。
- 除 `src/TUIKit/**` 外的 35 个业务页面根节点绑定主题类，并清理页面内硬编码浅色色值。
- 原生导航栏、状态栏、TabBar 配色随主题切换。

不涉及后端、接口、数据库与业务逻辑变更。

## Capabilities

### New Capabilities

- `app-dark-mode-ui`: 定义全 App 深色模式的开关、持久化、主题 token 生效范围与原生 UI 同步规则。

### Modified Capabilities

- `profile-settings-ui`: 设置页「通用」分组的深色模式开关从占位改为真实生效并反映当前主题状态。

## Impact

- 代码：`br-app/src/uni.scss`、`App.vue`、`main.js`，新增 `store/modules/theme.js`、`utils/theme.js`，`pages-sub/settings/index.vue`，`pages/**` 与 `pages-sub/**` 共 35 个页面。
- 不涉及：`br-server`、`br-admin`、`src/TUIKit/**`、`pages.json` 静态配置。
- 回滚方案：回退本次提交即可；`theme_mode` 只是本地 storage 键，清理 `uni.removeStorageSync('theme_mode')` 即恢复默认浅色，无服务端副作用。
