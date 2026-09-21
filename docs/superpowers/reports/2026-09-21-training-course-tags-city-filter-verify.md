# 验证报告：training-course-tags-city-filter

- 日期：2026-09-21
- Change：training-course-tags-city-filter（workflow: tweak, verify_mode: full）
- 产物语言：zh-CN

## Summary

| 维度 | 状态 |
| --- | --- |
| Completeness（完整性） | 9/9 任务完成；2 个 delta 能力、4 个 Requirement 均有实现映射 |
| Correctness（正确性） | API 3 场景由新测试覆盖（3 passed）；UI 3 场景实现确认且构建通过 |
| Coherence（一致性） | 实现与 design.md 全部决策一致；无 delta spec 与设计矛盾 |

**结论：全部通过，无 CRITICAL / IMPORTANT 问题，可进入归档。**

## 检查项明细（comet-verify Step 2b）

1. **tasks.md 全部完成**：9/9 `[x]`（grep 计数确认）✅
2. **实现符合 design.md**：✅
   - 决策 1「count 仅在 city_id 存在时显式 JOIN StudyRoom」→ `br-server/app/services/training_service.py:313-316`
   - 决策 1「过滤口径 `or_(city_id == X, city_id IS NULL)` 与培训室列表一致」→ `training_service.py:305`（对照培训室 `training_service.py:97`）
   - 决策 2「角标复用 `.cover-status` / `.cover-chip` 样式，零新增 CSS」→ `br-app/src/pages/training/index.vue:237-241`（右上既有 `.course-badge` 保留）
   - 决策 3「fetchCourses 传 city_id；onShow 按 activeTab 分支刷新」→ `index.vue:541`、`index.vue:573-578`
   - 决策 4「路由新增 city_id Query(ge=1) 透传」→ `br-server/app/api/routes/training.py:39,48`
3. **Design Doc（docs/superpowers/specs/）**：不适用——tweak 预设跳过 Superpowers brainstorming/Design Doc，以 change 内 design.md 为设计事实源。
4. **能力规格场景通过**：✅
   - `training-course-list-api` / Filter courses by city → 测试 `test_filter_by_city_a`（含 `total == 2` 断言，防 count 笛卡尔积放大）新鲜运行通过
   - `training-course-list-api` / Courses in rooms without city always visible → 同测试断言「无城市培训室课程」出现在结果中
   - `training-course-list-api` / 默认分页与 category 基线 → `test_no_city_returns_all`（不传 city_id 行为不回归）
   - `training-course-list-ui` / Course card cover badges → index.vue:237-241（左上「可预约」、右下「课程」），构建编译通过
   - `training-course-list-ui` / Course tab passes city_id → index.vue:541
   - `training-course-list-ui` / City switch refreshes active tab → index.vue:573-578
5. **proposal.md 目标满足**：角标一致性 + 城市过滤前后端联动，两目标均落地；回滚方案在 proposal 中成立（均为可选参数/纯展示元素）。
6. **delta spec 与 design doc 无矛盾**：无 Superpowers Design Doc；change 内 design.md 与 delta spec 由同一轮编写且实现未偏离，无漂移。✅
7. **docs/superpowers/specs/ 关联文档**：不适用（tweak 无 Design Doc）。

## 验证证据（新鲜运行）

- 后端：`pytest tests/test_training_course_city_filter.py` → **3 passed**（2026-09-21，本次 verify 内运行）；连同 `test_training_course_visibility.py` 共 7 passed（build 阶段）
- 前端：`npm run build:mp-weixin`（br-app）→ **exit 0**，check 证据已记录（build 与 verify 各一条，policy 匹配 argv+cwd）
- `git diff` 审查范围：`training.py`(+6/-2)、`training_service.py`(+9/-3)、`index.vue`(+13/-1)、`training.js`(+1/-1)、新测试文件 100 行
- 安全检查：city_id 为服务端 `Query(None, ge=1)` 整数参数；SQLAlchemy 参数化过滤，无注入面；无硬编码密钥 ✅

## 代码审查（review_mode: standard 轻量范围：正确性/安全/边界）

- 边界 1：`city_id` 与 `keyword` 同时传入 → count 只 JOIN StudyRoom，不 JOIN Teacher；后者为既有行为（见 WARNING-1），city_id 自身正确。
- 边界 2：培训室 `status=closed` 但课程 `active` → `list_courses` 原本就不按房间状态过滤（既有口径，未改变）。
- 边界 3：count 主查询均用同一 `or_(==city_id, IS NULL)`，total 与 items 口径一致。
- 结论：无正确性/安全/边界问题。

## 问题清单

**CRITICAL / IMPORTANT**：无。

**WARNING（既有问题，范围外，不在本 change 修复）**
1. `tests/test_training_routes.py`、`test_training_service.py`、`test_training_api.py`、`test_training_route_detail.py` 的旧 fixture 仍向 `Course(...)` 传已在排课重构中移除的 `teacher_id`，且未播种 `in_progress` fixed 排课，clean tree（`git stash` 基线）下即 fixture ERROR/结果不符——先于本 change 存在，与本次改动无关；新测试已采用 `test_training_course_visibility.py` 的正确模板。建议后续单独 change 清理。

**SUGGESTION**
1. 「可预约」角标对课程为静态标签（列表口径保证均有进行中排课，语义准确）；若未来引入课程级停开状态需改为动态。

## 跳过项说明

- 未做 main spec 全量覆盖率/漂移深度检查（tweak 精简产物范围，delta 对照已完成）。
