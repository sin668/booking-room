# 设计说明

## 数据格式

`course_schedules.time_slots` 为 JSON 字符串，现行格式（br-admin ScheduleModal 写入）：

```json
[{"weekday": 3, "time_slot": "14:00-16:00"}]
```

- `weekday`：1-7（1=周一，7=周日）
- `time_slot`：`HH:MM-HH:MM`
- 旧数据可能为纯文本（如 `周六 9:00-11:30`、`预约制`）或含 `start`/`end` 字段的对象

## 格式化函数

在 `br-app/src/utils/formatters.js` 新增 `formatCourseSchedule(timeSlots)`：

1. 空值返回 `''`（调用方回退显示"排课待定"）。
2. 字符串不以 `[` 开头 → 视为旧版纯文本，原样返回；JSON 解析失败同样原样返回。
3. 解析数组后逐项归一化为 `{ weekday, start, end }`：优先取 `start`/`end`，否则拆分 `time_slot`；非法项（weekday 不在 1-7、缺少开始时间）丢弃；全部非法时回退原样返回字符串输入。
4. 按 weekday 升序排序后输出：
   - 恰好 5 项且为周一到周五、时间段完全相同 → `工作日 {start}上课`
   - 否则 → `每{周三 14:00，周四 15:00}上课`（首项带"每"，项间中文逗号分隔，只取开始时间）

## 显示与截断（/pages/booking/detail）

- "本培训室课程"的上课时间改为 `formatCourseSchedule(course.schedule)`，空值回退"排课待定"。
- 截断：`.schedule-text` 限制最大宽度，CSS `text-overflow: ellipsis` 单行截断显示 `......`。
- 完整信息显示：
  - H5/桌面端：课程卡片上课时间区域悬停时显示绝对定位 tooltip（CSS `:hover` 控制，仅文案长度超过阈值时渲染）。
  - 移动端兜底：长按上课时间区域通过 `uni.showToast` 显示完整文案。

## 测试

新增 `br-app/scripts/verify-course-schedule-format.js` 断言各分支（单选、多选、工作日、旧文本兼容、非法输入），并在 `package.json` 注册 `test:course-schedule` 脚本；构建使用 `build:h5` 验证编译通过。
