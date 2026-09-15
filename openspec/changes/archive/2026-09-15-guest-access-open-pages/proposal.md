# Proposal: guest-access-open-pages

## Why

br-app 目前没有全局路由守卫，登录拦截依赖「请求层 401 兜底（`request.js` 刷新失败即 `reLaunch` 登录页）+ 少数页面各自判断」的分散模式。未登录用户浏览公开内容（首页、课程详情、门店详情、评价列表等）时，页面一旦附带触发任何需登录接口（如关注状态），即被强制踢到登录页，无法以游客身份体验产品核心浏览路径，影响新用户转化。

## What Changes

- `br-app/src/utils/request.js`：401 且刷新失败时**不再全局 `reLaunch` 登录页**，只清理本地 token 并将「登录已过期」错误向上抛出，由调用方决定后续行为（保持当前页面、toast 提示或跳登录）。
- 公开浏览页面在未登录时跳过需登录的附加请求（关注状态、个性化推荐等），保证游客可完整浏览。
- 明确需登录的页面（订单、钱包、卡券包、学习记录、充值、会员开通、学习码、核销、设置等）在进入或操作时主动检查登录态并跳转登录页，替代原先依赖 401 兜底的隐式拦截。
- 登录页支持回跳：登录成功后返回来源页面（复用现有 `navigateBack` 逻辑，reLaunch 进入时回首页）。

## Capabilities

- **New Capabilities**: `guest-access`（游客可访问性与登录门槛策略）
- **Modified Capabilities**: `user-auth`（401 处理语义变更：刷新失败不再由请求层强制跳转登录页，登录门槛上移到页面/操作层）

## Impact

- **代码**：`br-app/src/utils/request.js`、`br-app/src/App.vue`（清理死代码 WHITE_LIST）、若干页面 `onShow`/`onLoad` 增加登录守卫、公开页面跳过登录态附加请求。不涉及 br-server / br-admin。
- **API**：无后端接口变更；后端权限控制不变（RBAC 仍由后端强制）。
- **依赖**：无新增依赖。
- **回滚方案**：变更集中在 `request.js` 单点 + 各页面守卫，回滚时恢复 `request.js` 中的 `uni.reLaunch('/pages/login/login')` 一行并移除各页面守卫即可恢复原行为；git revert 单次提交即可。
