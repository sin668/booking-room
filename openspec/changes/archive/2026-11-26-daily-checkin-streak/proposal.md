# Proposal: 连续签到与补签

## Why

br-app 目前没有任何签到能力：用户每天打开小程序没有可积累的日常动作，个人中心也缺少提高日活的入口。已完成的 `prototype/checkin.html`、`checkin-success.html`、`checkin-makeup.html` 三屏高保真原型定义了完整交互（签到、连续天数、漏签、补签卡），但只有静态页面，没有真实数据与接口支撑。

## What Changes

- br-server 新增签到数据模型：`checkin_records`（按用户 + 日期唯一签到记录，区分每日签到与补签）与 `user_checkin_stats`（积分、补签卡余额）。
- br-server 新增三个接口：
  - `GET /api/v1/checkin/summary?month=YYYY-MM`：返回今日是否已签、连续天数、累计签到天数、积分、补签卡、指定月份日历标记与近 30 天可补签日期。
  - `POST /api/v1/checkin`：今日签到，每日 +5 积分，连续第 7/14/21… 天额外 +20 积分，连续第 30/60… 天额外赠 1 张补签卡；重复签到返回 400。
  - `POST /api/v1/checkin/makeup`：使用补签卡补签近 30 天内漏签日期，按日期数量扣卡。
- br-app 新增「签到日历」页与「补签中心」页，按原型实现渐变签到头图、签到按钮、周一起始日历（已签 ✓、漏签 ✗、未来日期显示预计连续天数）、连续奖励进度、签到规则、补签选日与底部确认栏；个人中心「学习服务」新增签到入口。
- 新页面复用全局 `themeMixin` 的 `themeClass` 与 `uni.scss` 语义色变量，兼容已有深色模式，不新增独立的深色样式分支。
- 无破坏性变更：不改动既有接口与数据表，`checkin-streak` 相关能力全部为新增。

## Capabilities

### New Capabilities

- `checkin-streak-api`: 签到汇总、每日签到、补签的服务端行为与数据口径（连续天数、漏签判定、积分与补签卡奖励、鉴权）。
- `checkin-streak-ui`: br-app 签到日历页与补签中心页的路由、展示、交互与深色模式要求。

### Modified Capabilities

（无。既有 `unified-user-model` 的字段不变，积分与补签卡保存在独立表中。）

## Impact

- 模块范围：
  - br-server：新增模型、迁移、schema、service、route，并注册到 `app/main.py`；新增单测。
  - br-app：新增 `src/api/checkin.js`、`src/pages-sub/checkin/` 两个页面、`pages.json` 路由、个人中心入口、图标补充。
  - br-admin：不受影响。
  - 数据库：PostgreSQL 新增两张表，不改既有表结构。
- 兼容性：接口与页面均为新增；未登录用户沿用 `get_current_user_id` 返回 401，前端沿用 `ensureLogin()` 登录引导。
- 文档：在 `docs/api.md` 补充签到接口说明。
- 依赖：不新增任何第三方依赖。

## 回滚方案

- 应用层：`git revert` 本次提交即可移除全部新增路由、页面与入口，既有功能不受影响。
- 数据库层：执行 Alembic `downgrade`（迁移 `downgrade()` 删除 `checkin_records` 与 `user_checkin_stats` 两张表及其索引），无既有表数据变更，回滚不丢失业务数据。
- 数据层：签到数据为新增独立数据，回滚后不再被读取，无需数据修复脚本。
