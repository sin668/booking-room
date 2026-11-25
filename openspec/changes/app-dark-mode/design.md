## 方案

CSS 自定义属性 + 页面根节点主题类 + SCSS 变量间接引用。

1. `uni.scss` 中语义色由字面量改为 `var(--token)`，页面已有的 `$text-primary`、`$surface` 等写法保持不变。
2. `App.vue` 全局样式定义 `page { --token: 浅色值 }` 与 `.theme-dark { --token: 深色值 }`。
3. 每个页面根节点 `<view class="page">` 追加 `:class="themeClass"`，变量在页面子树内被覆盖。
4. `theme` store 同步读取 `theme_mode`，切换时写 storage 并调用 `uni.setNavigationBarColor`、`uni.setTabBarStyle`、`uni.setBackgroundColor`。
5. 全局 `themeMixin` 提供 `themeClass`，在 `main.js` 注册。

## Token

新增/保留的关键 token：`--bg-color`、`--bg-warm`、`--bg-hero`、`--surface`、`--surface-soft`、`--surface-muted`、`--text-primary`、`--text-secondary`、`--text-muted`、`--border-color`、`--border-soft`、`--primary`、`--primary-light`、`--primary-soft`、`--success`、`--danger`。

深色基线：`--bg-color: #0F1115`、`--surface: #1A1D24`、`--text-primary: #ECEFF4`、`--text-secondary: #A8B0BD`、`--text-muted: #6B7484`、`--border-color: #2A2F3A`。

## 关键约束

- `rgba($primary, a)` 不能与 CSS 变量共存，需先改字面量（settings、edu-market/publish、edu-market/detail 共 12 处）。
- `$white` 双语义：前景白保持字面量，背景/切割边框改为 `$surface`/`$bg-color`。
- `src/TUIKit/**` 不在范围内，聊天页保持浅色。
- TabBar 图标为 PNG，不生成深色图，仅切换背景与文字色。
- 首屏不闪白：store state 同步读取 storage，`onLaunch` 应用原生配色。

## 回滚

回退提交；用户数据仅涉及本地 `theme_mode` 键，无服务端状态。
