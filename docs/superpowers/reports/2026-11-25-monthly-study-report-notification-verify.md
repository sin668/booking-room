# 验证报告：monthly-study-report-notification

- 日期：2026-11-25
- 流程：Comet Classic tweak（`verify_mode: full`，`review_mode: off`）
- 实现提交：`6d55341`（tweak: 新增每周一学习月报通知定时任务）
- 基线：`30362d0`（上一 change 归档提交）

## 1. 验证结论

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| tasks.md 全部完成 | PASS | 10/10 均为 `[x]` |
| 改动文件与 tasks 描述一致 | PASS | `6d55341` 变更 13 个文件，交付文件与任务 1.1~4.3 一一对应；其余为 OpenSpec 产物与 `.comet/rulings.md` |
| 编译/运行检查 | PASS | `comet check run … verify` exit=0，日志 `openspec/changes/monthly-study-report-notification/.comet/checks/4e27ee05-…log` |
| 相关测试通过 | PASS | 月报及通知/学习记录回归 44 passed；策略内 pytest 43 passed；`test:distance` 自检通过 |
| 无安全问题 | PASS | 无硬编码密钥；配置经环境变量注入；查询使用 SQLAlchemy ORM；未引入 unsafe 操作 |
| 集成代码审查 | SKIPPED（已记录原因） | tweak 预设 `review_mode: off`，非 autonomous；已对最终 diff 逐文件人工走查（scheduler/notification/main/JS/配置） |
| 核心与边界场景 | PASS | 见第 3 节场景覆盖表 |

## 2. 产物一致性

- **proposal 目标**：定时任务、内容模板、配置开关、按月去重、偏好过滤、设置页文案，全部实现（对应代码见第 3 节）。
- **design.md 决策**：配置项、通知服务方法、调度模块、`main.py` 注册与降级、JS 文案均按设计落地。
- **delta spec 与 design 一致性**：`specs/message-notification-api/spec.md` 的 1 个 Requirement / 6 个 Scenario 均能在 design.md 找到对应设计，无矛盾。
- **独立 Design Doc**：tweak 流程不产出 `docs/superpowers/specs/` Design Doc（`.comet.yaml` 中 `design_doc: null`），该项不适用；本 change 以 `design.md` 作为设计依据。

## 3. 能力规格场景覆盖

Requirement: **Monthly study report notification**

| Scenario | 实现证据 | 测试证据 | 结论 |
| --- | --- | --- | --- |
| Send current month report on Monday | `main.py:259-279` 注册 cron（`day_of_week/hour/minute` 取配置、`Asia/Shanghai`、`id=monthly_study_report`）；`monthly_study_report_scheduler.py:78` 以运行日期作为统计月份 | `tests/test_monthly_study_report.py::test_send_reports_sends_once_and_dedupes` | PASS |
| Report content follows study summary | `notification_service.py:352-357` 使用 `.2f` 小时数与次数/天数模板 | `test_notify_monthly_study_report_content_and_dedupe` 断言完整内容 | PASS |
| Skip duplicate report for the same month | `notification_service.py:342-351` 以 `target_id=YYYY-MM` + `target_type=monthly_study_report` + type + title 去重 | 同上用例断言第二次返回 `None` 且仅 1 条记录 | PASS |
| Skip user with disabled report preference | `send_notification` 默认 `respect_preferences=True`（`notification_service.py:217-229`），读 `report_enabled` | `test_notify_monthly_study_report_respects_disabled_preference`、`test_send_reports_skips_disabled_user` | PASS |
| Skip user without completed study this month | `monthly_study_report_scheduler.py:109-111` `monthly_bookings == 0` 时跳过 | `test_send_reports_skips_user_without_study` | PASS |
| Scheduled job disabled by configuration | `main.py:259-262`（APScheduler 分支）与 `main.py:323-327`（asyncio 降级分支）均以 `MONTHLY_STUDY_REPORT_ENABLED` 控制注册 | 无自动化用例，代码走查确认两分支均受开关约束 | PASS（见 SUGGESTION-2） |

配置项：`config.py:41-43`（启用开关/星期/时间）与 `.env.example:37-39` 已同步。
设置页文案：`br-app/src/pages-sub/utils/notificationTypes.js:25-26` 为「学习月报 / 每周一推送本月学习总结」。

## 4. 执行记录

```
comet check run monthly-study-report-notification verify --local -- sh -c "cd br-server && .venv/bin/python -m pytest tests/test_admin_room_routes.py tests/test_tencent_map_service.py tests/test_study_room_admin_service.py -q && cd ../br-admin && pnpm build >/dev/null 2>&1 && cd ../br-app && npm run test:distance && npm run build:mp-weixin >/dev/null 2>&1 && npm run build:h5 >/dev/null 2>&1"
→ Check verify: exit=0; reused=false
```

额外测试（与策略命令互补）：

```
cd br-server && .venv/bin/python -m pytest tests/test_monthly_study_report.py tests/test_study_record_service.py tests/test_notification_service.py tests/test_booking_notifications.py -q
→ 44 passed
```

## 5. 问题清单

### CRITICAL

无。

### WARNING

无。

### SUGGESTION

1. `design.md:13` 写的是私有 `_parse_monthly_study_report_schedule()`，实现为公开 `parse_monthly_study_report_schedule()`（`monthly_study_report_scheduler.py:26`），以便 `main.py` 与测试复用。仅为命名差异，不影响行为，建议后续更新 design 描述，本次不修改实现。
2. 「配置关闭不注册任务」场景目前只有代码走查，没有 lifespan 注册分支的自动化测试。该场景由两处 `if` 开关直接保证，风险低；如后续需要可在 `main` 生命周期测试中补一条断言。

### 偏差接受记录

- 上述 SUGGESTION 不影响正确性、安全或验收场景，按可接受记录，不在 verify 阶段修改实现。
- 集成代码审查：`review_mode: off`（tweak 预设、非 autonomous），原因与人工走查范围已记录于第 1 节。

## 6. 最终评估

无 CRITICAL / WARNING 问题，6 个规格场景全部覆盖，任务与交付范围一致，可进入归档。
