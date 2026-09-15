# Design: guest-access-open-pages

## 实现说明

核心原则（ponytail：最小改动，复用现有机制）：

1. **`request.js` 单点改动**：`refreshAccessToken()` 失败分支移除 `uni.reLaunch('/pages/login/login')`（request.js:89），保留清 token + 抛错。这是全项目唯一的全局强制跳登录点。401 处理本身（含并发排队，BUG-2 已修复的 `buildRequest(tokenValue)` 模式）不动。

2. **公开页面跳过登录态附加请求**：公开页面中依赖登录态的附加请求（关注状态等）在调用前判断 `getToken()`，未登录直接跳过。公开页面主体数据本就是公开接口。

3. **需登录页面主动守卫**：新增轻量工具函数 `ensureLogin()`（放 `utils/auth.js`，复用 `request.js` 已导出的 `getToken`）：未登录时 toast 提示 + `uni.navigateTo('/pages/login/login')` 并返回 false。需登录页面在 `onShow`/`onLoad` 或关键操作入口调用，替代原先「放行请求 → 401 → reLaunch 登录页」的隐式链路。
   - 需登录页面清单（进入即守卫）：orders、recharge、membership、wallet/transactions、coupon、favorites、study-record、notifications、qrcode、verify-booking、settings、review/submit、review/list(mine)、booking/confirm、booking/seat-select、training/course-booking。
   - 「我的」页保持现状（已有未登录占位 UI，不跳转）。
   - 操作级守卫（已有）：activity/detail 领券、membership 开通等保持不变。

4. **登录回跳**：登录页现有 `goAfterLogin()`（navigateBack / reLaunch 首页）已满足"登录成功返回来源页"——守卫统一用 `navigateTo` 进入登录页，登录后 `navigateBack` 自然返回。无需新增 redirect 参数机制。

5. **App.vue**：删除未使用的 `WHITE_LIST` 死代码。

## 不做的事

- 不引入全局路由拦截器（`uni.addInterceptor`）——当前分散守卫模式改动更小、更可控，且 tabBar 页面 onShow 守卫已覆盖入口。
- 不改后端任何接口/权限逻辑（RBAC 仍由后端强制）。
- 不新增依赖。

## 风险与规避（对照 bug-fixed.md）

- BUG-4 模式：守卫失败不得误清登录态——守卫只读 token，不写。
- BUG-14：新页面如用到 `onMounted` 必须从 `vue` 导入。
- BUG-20：模板不出现裸 `<`/`>` 字符。
