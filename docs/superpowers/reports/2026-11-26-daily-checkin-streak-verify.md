# 验证报告：daily-checkin-streak（连续签到与补签）

- 日期：2026-11-26
- 流程：Comet tweak / verify_mode: full
- 分支：main（isolation: current）
- 验证命令：`comet check run daily-checkin-streak verify --local -- sh -c '...pytest tests/test_checkin.py && npm run test:dark-mode && build:mp-weixin && build:h5'`
- 证据日志：`openspec/changes/daily-checkin-streak/.comet/checks/692d42fb-8a86-4240-849e-64b44248ac01.log`

## 结论

通过。无 CRITICAL / IMPORTANT 遗留问题。

## 检查项

| # | 检查项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | tasks.md 全部完成 | PASS | 20/20 已勾选 |
| 2 | 实现符合 design.md 决策 | PASS | 两张独立表、汇总接口返回统计+月历+missed_dates、奖励集中在服务端、补签不发放积分、两页共用 API 模块 |
| 3 | Design Doc 一致性 | 跳过 | tweak 预设无 Design Doc（用户已明确授权跳过），由 design.md 承担设计说明 |
| 4 | 能力规格场景覆盖 | PASS | 见下方场景核对 |
| 5 | proposal.md 目标满足 | PASS | 签到、连续天数、积分、补签卡、补签中心、深色模式均已实现 |
| 6 | delta spec 与 design 无矛盾 | PASS | 奖励口径、补签窗口、初始化 2 张卡一致 |
| 7 | docs/superpowers/specs 设计文档 | 跳过 | 本 change 无对应 Design Doc |

## 场景核对

### checkin-streak-api

- 汇总接口：`GET /api/v1/checkin/summary` 必填 `month`，非法值（`2026-13`/`2026-00`/`2026-1`）返回 422；返回 `today`、`today_signed`、`streak`、`total_days`、`points`、`makeup_cards`、`calendar_mark`、`missed_dates`；以 `Asia/Shanghai` 判定今日。
- 连续天数：今日已签从今日向前，今日未签从昨日向前（`_calculate_streak`）。
- 漏签：晚于/等于首次签到、早于今日、无记录；今日不计漏签；`makeup_eligible` 仅近 30 天。
- 签到：首次 +5、第 7 天 +25、第 30 天 +1 卡；重复签到 400；未登录 401。
- 补签：去重、必须早于今日、不超过 30 天、不早于首次签到、未签到、卡数足够；成功后扣卡、不发放积分；任何校验失败不落库。
- 初始化：首次访问创建统计行，0 积分、2 张补签卡。

### checkin-streak-ui

- 路由：`pages.json` 分包注册 `checkin/index`（签到日历）与 `checkin/makeup`（补签中心）。
- 个人中心入口：可跳转签到日历页。
- 签到日历页：渐变头图（连续/累计/积分/补签卡）、全宽签到按钮、周一起始日历、已签 ✓ / 缺签 ✕ / 未来预计连续天数 / 今日「签」、图例、月份切换、30 天奖励进度、补签入口、规则卡片、成功弹窗、失败轻提示。
- 补签中心页：剩余卡与规则说明、日历选日、待补签列表、选择上限、底部确认栏、空状态、成功提示与刷新。
- 深色模式：两页根节点绑定 `themeClass`，颜色全部走语义变量；`npm run test:dark-mode` 通过（17 token / 37 页面）。
- 登录与异常：`ensureLogin()` 未登录时不请求接口；汇总失败时展示零值、提示且按钮不可用。

## 验证中发现并已修复的问题

1. **IMPORTANT — 非法月份导致 500**：`month=2026-13` 通过正则后构造 `date()` 抛 `ValueError`。已把查询参数正则收紧为 `^\d{4}-(0[1-9]|1[0-2])$`，并新增 `test_summary_rejects_invalid_month` 回归测试。
2. **WARNING — 失败态按钮文案误导**：加载失败后按钮仍显示「加载中...」，已改为「暂不可用」，仍保持不可点击。

## 非阻断偏差

- SUGGESTION：个人中心签到入口的 meta 文案为「连续签到领积分」而非实时签到状态摘要。原因是个人中心位于主包，引入 `api/checkin.js` 会破坏现有主包/分包搬运与校验约束；签到状态在签到页完整体现。后续如需实时摘要，建议由个人中心聚合接口一并返回。

## 其他证据

- 后端测试：`pytest tests/test_checkin.py` → 20 passed。
- 迁移链：`alembic heads` → `p1q6r2s8t4u0 (head)`（单 head）。
- 前端构建：`npm run build:mp-weixin` 通过，主包 1.18MB，分包布局校验通过；`npm run build:h5` 通过。
- 路由：OpenAPI 包含 `/api/v1/checkin/summary`、`/api/v1/checkin`、`/api/v1/checkin/makeup`。
- 代码审查：`review_mode: off`，按 tweak 预设跳过自动代码审查；本次为新增功能且改动集中，已由上述构建、测试与场景核对覆盖。
