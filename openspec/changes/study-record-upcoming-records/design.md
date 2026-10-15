# Design: study-record-upcoming-records

后端 `study_record_service.py`：

- `_collect_studied_items` 泛化为 `_collect_items(db, user_id) -> tuple[list, list]`，返回 (studied, upcoming)。查询状态集合扩为 completed/in_progress/pending_start（自习室记录需 payment_status=paid）：
  - 自习室：`_is_studied(status)` → studied；pending_start → upcoming（date=booking.date）。
  - 课程：课时排课构建逻辑不变，`_build_course_lesson_records` 增加 `pending_only: bool = False` 反转完成判断；已完成课时（lesson_date < today，复用 `_is_lesson_completed` 的 Asia/Shanghai 口径）→ studied，未完成课时且订单为 pending_start/in_progress → upcoming（status="upcoming"，date=lesson_date）。
- `get_monthly_summary`：统计仍仅基于 studied（口径不变）；`calendar_mark.upcoming = 日期在 upcoming 集合中`。
- `list_study_records`：status=None → studied+upcoming 合并按 date/start_time 倒序；"completed" → studied；"upcoming" → upcoming；month/date 过滤逻辑不变（作用于合并结果）。
- 路由无需改动：`status` 参数与透传已存在。

前端 `index.vue`：

- `upcomingDates` computed（calendar_mark item.upcoming）；calendarDays 单元格增加 upcoming 标记；日历点改为 `.dot-row` 容器：绿点=studied、橙点=upcoming（`$orange`）。
- 图例新增"未开始"（橙色点）。
- 记录列表拆分为双 Tab（复用 `.tab-bar/.tab-item` CSS）：`activeTab` ref（studied/upcoming），`fetchRecords` 恒定携带 `status=completed/upcoming`；空态文案按 Tab 区分；课程图标 `.course-icon-body` 默认绿色（$success），未开始记录叠加 `.course-icon-upcoming` 橙色；状态标签"未开始"橙色。
- `toggleDateFilter` 移除 isFuture 拦截；选中日期时按 `cell.isToday || cell.isFuture` 自动切换 Tab（今日及未来→学习计划，过去→学习记录），取消选中保持当前 Tab。
