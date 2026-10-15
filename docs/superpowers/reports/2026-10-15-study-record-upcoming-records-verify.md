# 验证报告：study-record-upcoming-records

- 日期：2026-10-15
- 变更基线：`538d5d1`（chore: archive study-record-date-filter）
- 验证模式：full（scale 建议 full：tasks 9 > 3、delta spec 2 能力 > 1、变更文件 11 > 8）
- 工作流：Comet Classic tweak，schema spec-driven

## Summary

| 维度 | 状态 |
|------|------|
| Completeness | 9/9 tasks ✓；2 个 delta spec 能力共 4 条 Requirement 全部有实现证据 |
| Correctness | 4/4 Requirement 覆盖；13 个 Scenario 中后端场景有测试覆盖、UI 场景经代码核对+构建验证 |
| Coherence | 实现与 design.md 一致（含 build 期间三次用户增量调整，产物已同步）；符合项目现有模式 |

**最终结论：PASS，无 CRITICAL / IMPORTANT 问题，可归档。**

## 检查项逐条结果（comet-verify full 清单）

1. **tasks.md 全部完成**：9/9 `[x]`（Runtime taskState total=9 completed=9）。
2. **实现符合 change design.md**：后端 `_collect_items` 双集合、`pending_only` 反转、summary `upcoming` 标记、list status 派发均按设计落地（`br-server/app/services/study_record_service.py:162/117/349/384-390`）；前端双 Tab、橙色未开始、状态配色、点击日期自动切换 Tab 已实现并提交，design.md 前端章节在 build 增量调整后已同步更新。
3. **Design Doc（docs/superpowers/specs/）**：tweak 预设不产出独立 Design Doc（design_doc=null），以 change 内 design.md 为准——不适用。
4. **能力规格场景**：
   - study-record-api：分页默认含 upcoming（`test_list_excludes_non_studied` 合并口径）、月份/单日/status=upcoming 过滤（`test_list_upcoming_seat_status_and_date_filter`、`test_list_filter_by_date`）、401（既有 API 测试）；summary upcoming 标记且不计入统计（`test_calendar_mark_upcoming_excluded_from_stats`、`TestUpcomingCourseLessons::test_in_progress_booking_future_lesson_is_upcoming`）。
   - study-record-ui：日历绿/橙点与图例、双 Tab 请求 `status=completed/upcoming`、课程图标绿/橙、状态标签配色、点击日期过滤与自动切换 Tab（今日及未来→学习计划）——经 `br-app/src/pages-sub/study-record/index.vue` 代码核对，`npm run build:mp-weixin` 构建通过（build 证据 check `bf57c567`）。
5. **proposal.md 目标**：未开始记录进入日历与列表、点击日期过滤可用、双 Tab 与配色调整均满足。
6. **delta spec 与 design doc 无矛盾**：build 期间的 Tab 拆分、橙色、自动切换调整已同步写入 delta spec 与 design.md（提交 `80d5893`），无残留"蓝色"表述。
7. **docs/superpowers/specs/ 关联设计文档**：tweak 无独立 Design Doc，跳过（同第 3 项）。

## 检查证据

- **后端定向测试**：`comet check run verify`（br-server，pytest 三个学习记录测试文件）exit=0，36 passed（check `80095a24`）。
- **前端构建**：`comet check run build`（br-app，`npm run build:mp-weixin`）exit=0（check `bf57c567`），build 守卫 14/14 通过。
- **全量后端套件说明（WARNING，接受偏差）**：`tests/` 全量存在 15 个失败（test_activity_coupon_campaign×2、test_admin_user_management×1、test_api_booking 退款梯度×1、test_coupon_service TestAvailableCouponsForBooking×8、test_models_import TestCourseModel×3）。已在本 change 基线提交 `538d5d1` 的临时 git worktree 中运行同一组文件复现完全相同的 15 个失败，证明为改动前既有的陈旧测试漂移（如 Course 模型早移列而测试未更新），与学习记录模块无交集，不阻塞本 change。
- **安全**：diff 无硬编码密钥、无新增 unsafe 操作；status 参数经 FastAPI pattern `^(completed|upcoming)$` 白名单校验。
- **统计口径不变**：monthly_hours/bookings/total_hours 仅统计 studied，新增测试显式断言 upcoming 不计入。

## 代码审查

- `review_mode: off`（tweak 设置，用户于 open 阶段选定）：按配置跳过自动独立代码审查；本报告以需求-实现映射与测试证据替代交叉审查，原因记录于此。

## 偏差记录

- 无需要用户接受的 WARNING/SUGGESTION 实现偏差（全量套件 15 失败为基线既有问题，已用基线复现证明与本 change 无关）。
