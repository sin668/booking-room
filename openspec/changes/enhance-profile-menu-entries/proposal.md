## Why

「我的」页菜单项右侧已有「查看全部」「N项关注」「N张可用」等引导文案，但「我的评价」和「钱包充值」两行右侧空白，且缺少进入消息中心的入口，用户无法在「我的」页感知自己的评价数量和未读消息。

## What Changes

- 「我的评价」行右侧新增 `X条评论` 统计文案（X 为当前用户发表的评价总数，含待审核/已驳回），无评价时留空。
- 在「我的评价」下方新增「我的消息」行，右侧显示 `X条未读`（X 为未读消息数，为 0 时留空），点击跳转到已有的消息通知页 `/pages/notifications/index`。
- 「钱包充值」行右侧新增静态引导文案 `充值钱包`，与相邻行的「交易明细」「到店核销」保持同一写法。

不新增后端接口、不改动数据库：评价总数复用 `GET /api/v1/reviews?mine=1&page_size=1` 的 `total`，未读数复用 `GET /api/v1/notifications/unread-summary` 的 `total_unread`（首页铃铛已在用同一接口）。

## Capabilities

**Modified Capabilities**

- `student-review-ui` — 「My reviews entry on profile page」要求在保留跳转与登录守卫语义的前提下，右侧新增评价数量文案。
- `message-notification-ui` — 新增「我的」页消息入口及其未读数展示要求。

「钱包充值」右侧的静态文案不涉及任何可验收的行为变化，仅作为 UI 引导纳入本次实现范围，不写入 spec。

## Impact

- 影响模块：仅 `br-app`（uni-app 小程序前端），单文件 `br-app/src/pages/profile/index.vue`。
- 数据来源：`br-app/src/api/review.js`（已有 `getReviewList`）、`br-app/src/api/notifications.js`（已有 `getNotificationUnreadSummary`）。
- `br-server`、`br-admin`、数据库与 alembic 迁移：无改动。
- 新增请求：每次进入「我的」页 `onShow` 多两个只读 GET，与既有 `Promise.allSettled` 并发发起，互不阻塞。

## Rollback

改动集中在一个页面的模板/computed/取数方法，回滚方式为 `git revert` 本次 tweak 提交；无迁移、无接口签名变更、无数据写入，回滚后无需任何清理动作。
