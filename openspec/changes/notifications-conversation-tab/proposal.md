# Proposal: 消息通知页新增「会话」TAB 并精简通知类型标签

## Why

br-app 消息通知页目前只能查看系统通知，用户与教培供需发布者的 IM 单聊没有任何入口，只能回到详情页重新点「咨询」；同时顶部筛选标签「预约提醒/活动通知/学习报告/到店提醒」字数过长，加上新的「会话」后一行放不下。

## What Changes

- 顶部筛选导航在「全部」之后新增「会话」TAB，展示当前用户与腾讯 IM 的会话列表（京东消息风格）：左侧头像 + 昵称 + 最新一条消息（超长单行截断加省略号），右侧时间 + 未读条数红点徽标。
- 点击会话条目进入已有的 `/TUIKit/components/TUIChat/index` 聊天页，复用现网 `conversationID` 路由参数机制，不新建聊天页。
- 通知类型标签精简：`预约提醒`→`预约`、`活动通知`→`活动`、`学习报告`→`报告`、`到店提醒`→`到店`。
- 无破坏性变更：设置页通知偏好仍使用 `settingLabel` 全称，后端通知类型枚举 `booking/activity/report/arrival` 不变。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `message-notification-ui`：筛选入口由 5 项变为 6 项并新增会话列表要求；四类通知的展示文案口径变更。

## Impact

- 模块范围：仅 br-app 前端（小程序 + H5），不涉及 br-server、br-admin。
- 受影响文件：
  - `br-app/src/utils/notificationTypes.js`（标签文案）
  - `br-app/src/pages/notifications/index.vue`（新增会话 TAB、会话列表 UI 与跳转）
- 依赖：仅使用仓库已安装的 `@tencentcloud/chat-uikit-engine-lite`（`TUIStore`/`TUIConversationService`）与既有 `br-app/src/utils/im.js` 的 `ensureIM()`，不新增任何依赖。
- 数据：会话数据完全来自腾讯 IM SDK 本地会话列表，无新增后端接口。

## 回滚方案

改动集中在 2 个前端文件且无数据迁移、无接口变更，回滚即 `git revert` 本次 tweak 提交（`notificationTypes.js` 标签恢复全称、`notifications/index.vue` 移除会话 TAB 分支）后重新构建 `npm run build:mp-weixin`，不影响历史消息数据。
