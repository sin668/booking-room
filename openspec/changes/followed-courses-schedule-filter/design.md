# Design: followed-courses-schedule-filter

## 决策

### D1: 服务端单一口径，复用既有 EXISTS helper

`training_service._has_in_progress_fixed_schedule()`（对 `Course` 显式 correlate 的 EXISTS）已是 C 端课程列表/培训室详情/热门/相关课程的统一隐藏口径。`room_follow_service.list_followed_rooms` 的 course 分支直接 import 复用，避免第五处复制过滤逻辑；correlate 注释中说明的场景（外层 JOIN CourseSchedule 时自动关联吞 FROM）正是本分支的查询形态（列表 outerjoin CourseSchedule 取价格）。

### D2: 过滤位置

- course 分支：`course_filters` 追加该 EXISTS 条件；count 与列表共用同一 filters 列表，天然同口径。
- 保留 CourseSchedule 的 outerjoin 取 `schedule.price`：过滤后每门课至少有一条匹配排课，outerjoin 语义足够（多排课时的重复行为与现状一致，不在本次范围）。
- `follow_type=room|teacher` 不引用排课，不变；POST/DELETE 关注接口不变。

### D3: 前端零改动

首页与 favorites 页都经 `getAllFollowedCategories` → 该接口取数，服务端过滤后自动生效。

## 测试影响

既有关注课程测试的 fixture 均未创建排课，新口径下课程会被隐藏：`test_course_follow.py`、`test_room_follow_service.py`、`test_follow_city_filter.py` 的课程 fixture 各补一条 fixed+in_progress 排课；新增「无进行中排课的关注课程不返回」「待开始/已完成排课不返回」用例。
