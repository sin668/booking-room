# 课程上课时间统一格式化与培训室详情显示

## 为什么

当前 br-app 从培训室详情接口拿到的课程 `schedule` 字段是 `course_schedules.time_slots` 的原始 JSON 字符串（如 `[{"weekday":3,"time_slot":"14:00-16:00"}]`），在 `/pages/booking/detail` 的"本培训室课程"列表中直接展示，用户看到的是不可读的 JSON。需要将其统一处理为人类可读的上课时间文案。

## 变更内容

- 在 br-app 新增统一的上课时间格式化工具函数，将 `time_slots` 数据处理为可读文案：
  - 单个时间段：`每周三 14:00上课`（时间为时间段开始时间）
  - 多个时间段：`每周三 14:00，周四 15:00上课`
  - 周一至周五选择同一时间段：`工作日 14:00上课`
  - 兼容旧格式（非 JSON 文本如 `周六 9:00-11:30`、`预约制` 原样返回）
- 在 `/pages/booking/detail` 培训室详情的"本培训室课程"中调用该函数显示上课时间：
  - 文案超过一定长度时截断并显示 `......`
  - 鼠标悬停（H5）或长按（移动端兜底）时显示完整上课时间

## 影响范围

- 受影响能力：course-schedule-time-ui（新增）
- 受影响代码：
  - `br-app/src/utils/formatters.js`（新增格式化函数）
  - `br-app/src/pages/booking/detail.vue`（调用与显示、截断、悬停提示）
  - `br-app/scripts/verify-course-schedule-format.js`（验证脚本）
- 不修改后端接口和数据库结构；`schedule` 字段仍返回原始 `time_slots`，格式化在前端统一完成。
