# Design: study-record-in-progress-plan

后端 `study_record_service.py`（`_collect_items` 构建循环与列表派发）：

- 自习室订单分支改为按订单状态三路分派：`completed` → studied 集合（status="completed"）；`in_progress` → upcoming 集合（status="in_progress"）；`pending_start`（已支付）→ upcoming 集合（status="upcoming"）。`_is_studied` 仅供课程分支判定历史课时归属，不再决定自习室订单去向。
- 课程分支：`_is_studied(b.status)` 的已完成课时仍进 studied（不变）；未完成课时进 upcoming 时，`status` 由订单状态映射——`in_progress` 订单 → "in_progress"，`pending_start` 订单 → "upcoming"。
- `get_monthly_summary`：统计基于 studied 集合聚合，自习室进行中订单移出后自然不计入（monthly_hours/monthly_bookings/total_hours/streak 口径 = 已完成学习）；`calendar_mark.upcoming` 基于 upcoming 集合，进行中记录日期自动带橙点，studied=False。
- `list_study_records`：`status=upcoming` 返回 upcoming 集合（含 in_progress 状态条目），默认合并逻辑不变；路由/schema 不动。

前端 `index.vue`：

- 状态标签三路：`completed` → 绿色"已学习"；`in_progress` → 绿色"进行中"（新增 `.status-in-progress`，同绿色系）；否则橙色"未开始"。
- 课程图标：仅 `status === 'upcoming'` 橙色，`in_progress` 走默认绿色。
- Tab 请求参数（status=completed/upcoming）、日历橙点、点击日期自动切换 Tab 均不变。
