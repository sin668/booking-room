# Verification Report: followed-courses-schedule-filter

- 日期：2026-09-22
- 模式：full（含 delta spec）
- Schema：spec-driven

## Summary

| Dimension    | Status |
|--------------|--------|
| Completeness | 5/5 tasks 完成；1/1 requirement 已实现 |
| Correctness  | 3/3 delta scenarios 有实现与测试覆盖 |
| Coherence    | D1/D2/D3 设计决策均已落实 |

## 检查项

1. **tasks.md**：1.1/1.2/1.3/2.1/2.2 全部 `[x]`。
2. **Requirement: Followed courses schedule visibility**
   - 实现：`br-server/app/services/room_follow_service.py` course 分支 `course_filters` 追加
     `training_service._has_in_progress_fixed_schedule()`（EXISTS，fixed + in_progress，
     显式 correlate Course），count 与列表共用同一 filters，同口径。
   - 口径复用：与 `training_service` 中 list_courses / 培训室详情 / 热门课程 / 相关课程
     使用同一 helper，符合"与 C 端其他课程页面隐藏规则一致"。
3. **Scenario 覆盖**
   - 有排课正常返回并取排课价格：`tests/test_course_follow.py::test_followed_course_without_in_progress_fixed_schedule_hidden`
     断言可见课程 `min_price == 88.0`（取自排课 price）。
   - 无排课 / pending_start / completed / custom 隐藏且不计 total：同上用例构造 4 门隐藏课程，
     `total == 1` 且仅返回有进行中固定班课排课的课程。
   - room/teacher 不受影响：`test_room_and_teacher_follows_unaffected_by_schedule_filter` +
     `tests/test_follow_city_filter.py` teacher/room 用例回归通过。
4. **Design 一致性**
   - D1 复用 helper：已落实（import `_has_in_progress_fixed_schedule`，无循环依赖）。
   - D2 过滤位置：已落实（course_filters 同灌 count/list；保留 outerjoin 取 price）。
   - D3 前端零改动：已落实（本 change 无 br-app 源码提交，构建仅回归验证）。
5. **测试与构建证据**
   - pytest：`tests/test_course_follow.py + test_room_follow_service.py + test_follow_city_filter.py`
     → 22 passed。
   - 回归：`pytest -k "follow or training or course"` → 186 passed, 3 failed
     （`test_models_import.py` 3 项为 schema 迁移后既有陈旧断言，stash 基线确认改动前已失败，与本 change 无关）。
   - br-app：`npm run build:mp-weixin` exit 0（comet check 证据，build/verify 守卫同目录消费）。

## Issues

- **WARNING（设计内已知限制，接受）**：一门课程若同时存在 2+ 条 fixed+in_progress 排课，
  列表 outerjoin 会产生重复条目，而 count 按关注记录计数，`total` 与 items 数不一致。
  该行为在本变更前即存在（outerjoin 取价格），design D2 明确"不在本次范围"；
  现有业务约束下每课程同时仅一条进行中固定班课排课。
- POST/DELETE 关注接口与 `follow_room` 的 outerjoin 未改动，符合 spec"不受影响"要求；
  备注：`follow_room`/`get_course_detail` 的 `.one_or_none()` 在多排课下会抛
  MultipleResultsFound，为既有独立问题，不在本 change 范围。

## 结论

**PASS** — 无 CRITICAL/IMPORTANT 问题，可进入归档。
