## Why

`create_course_booking` 方法中 `get_course_with_lessons` 返回的 `course` 是 dict，但代码使用点号访问属性（如 `course.status`），导致 `AttributeError: 'dict' object has no attribute 'status'`，预约下单接口返回 500。

## What Changes

- 将 `course_booking_service.py` 中 `create_course_booking` 方法内所有 `course.xxx` 点号访问改为 `course["xxx"]` 字典访问（共 5 处：`status`、`room_id`、`id`×2、`name`）

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。纯 bug 修复，不改变任何 spec 级别行为。

## Impact

- 影响模块：`br-server/app/services/course_booking_service.py`
- 影响 API：`POST /api/v1/course-bookings`
- 回滚方案：git revert 单文件修改即可
