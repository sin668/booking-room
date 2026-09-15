## 1. 「我的」页取数

- [x] 1.1 在 `br-app/src/pages/profile/index.vue` 引入 `getReviewList`、`getNotificationUnreadSummary`，在 `data` 中新增 `reviewCount`、`unreadMessageCount`
- [x] 1.2 把两个请求并入 `loadProfileStats()` 既有的 `Promise.allSettled`，失败各自回落为 0，并沿用 `profileRequestId` 竞态保护

## 2. 「我的」页展示

- [x] 2.1 新增 `reviewSummary`、`unreadSummary` computed，数量为 0 时返回空串
- [x] 2.2 「我的评价」行右侧加 `menu-item-meta` 显示 `X条评论`
- [x] 2.3 在「我的评价」下方新增「我的消息」行（`icon-bell` 图标 + 文案 + 未读统计 + 箭头），跳转到 `/pages/notifications/index`，并补上图标定色定量的 `.message-icon` 样式
- [x] 2.4 「钱包充值」行右侧加静态 `充值钱包` 引导文案

## 3. 验证

- [x] 3.1 运行 `npm run build:mp-weixin` 确认编译通过，运行 `npm run test:profile-menu` 校验三处文案、跳转目标与 0 值留空，并走查与相邻菜单行的结构一致性
