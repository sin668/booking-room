## 实现说明

主体改动集中在 `br-app/src/pages/profile/index.vue`，完全沿用页面既有写法，不引入新组件与新样式体系；另附一个只读静态校验脚本 `br-app/scripts/verify-profile-menu-summary.js`（在 `br-app/package.json` 注册为 `test:profile-menu`）。

**取数**：在既有的 `loadProfileStats()` 的 `Promise.allSettled([...])` 里追加两个请求，与余额/卡券/学习时长同批并发，并复用页面已有的 `profileRequestId` 竞态保护：

- `getReviewList({ mine: true, page_size: 1 })` → 取响应 `total` 存到 `reviewCount`；`page_size: 1` 只取 1 条明细，仅用于拿总数。
- `getNotificationUnreadSummary()` → 取 `total_unread` 存到 `unreadMessageCount`（与首页 `loadNotificationUnreadSummary` 同一接口、同一字段口径）。

两者 `rejected` 时各自回落为 0，不影响其他统计项。

**展示**：新增两个 computed，仿照已有 `followSummary`（数量为 0 返回空串）：

- `reviewSummary` → 数量为 0 时返回空串，否则 `${reviewCount}条评论`
- `unreadMessageSummary` → 数量为 0 时返回空串，否则 `${unreadMessageCount}条未读`

**模板**：

- 「我的评价」行在 `menu-item-text` 后插入 `<text class="menu-item-meta">{{ reviewSummary }}</text>`。
- 紧随其后新增「我的消息」行：`@tap="navigateTo('/pages/notifications/index')"`，图标用全局已注册的 `.icon.icon-bell`（`App.vue` 已 `@import` iconfont.css），置于 `<view class="menu-icon blue">` 色块内，右侧 `menu-item-meta` + `menu-arrow`，结构与相邻行一致。
- 「钱包充值」行插入静态 `<text class="menu-item-meta">充值钱包</text>`。

新增的唯一样式是一条 `.message-icon { font-size: 34rpx; color: $primary; }`，用于给 mask-image 图标定色与定尺寸，与既有 `.menu-arrow` 的做法一致（34rpx 与相邻 `.review-star-icon` 同尺寸）。

**验证**：`npm run build:mp-weixin` 编译通过；`node scripts/verify-profile-menu-summary.js` 校验三处文案、跳转目标、数量为 0 时留空、以及 `Promise.allSettled` 解构槽位与请求数一致（该脚本对以上四类破坏均会失败）。因小程序页面需登录态与真实数据，UI 交互以构建产物 + 静态校验 + 代码走查为准，不谎称已在真机验证。
