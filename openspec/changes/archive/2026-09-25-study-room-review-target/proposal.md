# 提案：我的评价页自习室卡片展示评价对象行

## Why

「我的评价」页（br-app `pages/review/list`）的卡片底部评价对象行目前只覆盖课程评价（`课程名 · 老师名`）；自习室评价的 `room_name`/`seat_number` 字段后端已返回但前端未使用，导致自习室卡片该行整体缺失，用户无法区分评价对应的自习室与座位。

## What Changes

- `targetText` 按 `booking_type` 分支：自习室评价渲染 `自习室名称 · N号座位`，课程评价维持 `课程名 · 老师名` 不变。
- 评价对象行图标随类型切换：课程 `icon-book`、自习室 `icon-location`（对齐发表评价页先例）。
- 无后端改动：`GET /api/v1/reviews` 的 `ReviewItem` 已含 `room_name`、`seat_number`、`booking_type`。
- 回滚方案：纯前端展示层改动，回退 `br-app/src/pages/review/list.vue` 的单次 tweak 提交即可，无数据与接口影响。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `student-review-ui`：新增「我的评价卡片评价对象行」需求，覆盖课程与自习室两种 `booking_type` 的末行展示与数据缺失隐藏行为。

## Impact

- 影响模块：仅 `br-app`（uni-app 小程序端）`src/pages/review/list.vue`。
- 不影响：br-server 接口、数据库、br-admin、评价提交/审核链路。
