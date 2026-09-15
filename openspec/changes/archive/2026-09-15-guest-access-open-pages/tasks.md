# Tasks: guest-access-open-pages

## 1. 请求层解除全局跳转

- [x] 1.1 `br-app/src/utils/request.js`：`refreshAccessToken()` 失败分支移除 `uni.reLaunch('/pages/login/login')`，仅清 token + reject「登录已过期」
- [x] 1.2 `br-app/src/App.vue`：删除未使用的 `WHITE_LIST` 死代码

## 2. 登录守卫工具

- [x] 2.1 新建 `br-app/src/utils/auth.js`：`isLoggedIn()`（读 token）+ `ensureLogin()`（未登录 toast + navigateTo 登录页，返回是否已登录）

## 3. 需登录页面接入守卫

- [x] 3.1 orders/index：onShow 守卫（未登录 toast + 跳登录，不发请求）
- [x] 3.2 钱包/资产类页面接入 ensureLogin：recharge、wallet/transactions、coupon/index、study-record/index、notifications/index、favorites/index（qrcode 已有未登录占位 UI 保持不动；verify-booking 使用独立 X-Admin-Token 管理员核销，不依赖用户登录态，不接入）
- [x] 3.3 交易/提交类页面接入 ensureLogin：booking/confirm、booking/seat-select（选择模式守卫，查看模式不拦）、training/course-booking、review/submit、review/list（仅 mine 模式）
- [x] 3.4 settings/index：onShow 守卫；membership/index 保留操作级守卫（VIP 权益页游客可浏览，开通时 toast + 跳登录）

## 4. 公开页面游客可用

- [x] 4.1 公开页面登录态附加请求处理：首页跳过关注列表+未读消息请求（index.vue）、门店详情跳过关注状态请求（booking/detail.vue loadFollowStatus）、关注按钮统一 ensureLogin 守卫（门店详情/课程详情/老师简介）；培训列表/课程详情/老师简介/活动详情/搜索的自动请求均为公开接口，无需处理
- [x] 4.2 「我的」页未登录占位 UI 未受影响（本 change 未改动 profile/index.vue，确认其 v-if isLoggedIn 占位逻辑完好）

## 5. 验证

- [x] 5.1 `npm run build:mp-weixin` 构建通过
- [x] 5.2 验证：代码级审计确认游客路径（首页/培训/课程详情/门店详情/搜索/评价列表）无强制跳登录残留——全仓 `pages/login` 引用仅剩需登录页面守卫与操作级入口；`request.js` 已无全局 reLaunch；微信小程序构建通过。真机/开发者工具回归建议由用户在发布前执行
