# 任务清单

## 1. 格式化工具函数

- [x] 1.1 在 `br-app/src/utils/formatters.js` 新增 `formatCourseSchedule(timeSlots)`：解析 time_slots JSON（兼容 `{weekday, time_slot}`、`{weekday, start, end}` 与旧版纯文本），按规则输出"每周三 14:00上课"/"每周三 14:00，周四 15:00上课"/"工作日 14:00上课"

## 2. 培训室详情页显示

- [x] 2.1 `br-app/src/pages/booking/detail.vue` 的"本培训室课程"上课时间改为调用 `formatCourseSchedule(course.schedule)`，空值回退"排课待定"
- [x] 2.2 上课时间超长时单行截断显示 `......`（限制最大宽度 + CSS ellipsis）
- [x] 2.3 悬停/长按显示完整上课时间：H5 使用 CSS `:hover` tooltip，移动端长按用 `uni.showToast` 兜底

## 3. 验证

- [x] 3.1 新增 `br-app/scripts/verify-course-schedule-format.js` 断言各格式化分支，`package.json` 注册 `test:course-schedule` 脚本并运行通过
- [x] 3.2 运行 `npm run build:h5` 确认编译通过
