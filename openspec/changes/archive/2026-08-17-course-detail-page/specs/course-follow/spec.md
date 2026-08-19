# Course Follow

## ADDED Requirements

### REQ-CF-1: follow_type 字段

`room_follows` 表新增 `follow_type` 列（String(20)，默认值 `room`，不可为空），用于区分关注类型：
- `room`：自习室/培训室关注（现有数据）
- `course`：课程关注

唯一约束调整为 `(user_id, room_id, follow_type)`，允许同一用户同时关注同一教室的房间和课程。

### REQ-CF-2: 关注 API 扩展

现有关注 API 端点接受可选 `follow_type` 查询参数：
- `POST /api/v1/room-follows/{target_id}?follow_type=course`：关注课程
- `DELETE /api/v1/room-follows/{target_id}?follow_type=course`：取消关注课程
- `GET /api/v1/room-follows?follow_type=course`：获取关注的课程列表

当 `follow_type=course` 时，`room_id` 字段实际存储 `course_id`。

### REQ-CF-3: 前端关注服务

新建 `br-app/src/services/followedCourses.js`，提供课程关注的本地缓存和 API 同步：
- `followCourse(course)`：本地缓存 + 后端持久化
- `unfollowCourse(courseId)`：本地移除 + 后端删除
- `isCourseFollowed(courseId)`：检查本地缓存
- 使用独立的 storage key `followed_courses`

### REQ-CF-4: 向后兼容

- 现有 `room_follows` 数据在迁移时自动填充 `follow_type = 'room'`
- 现有 API 不传 `follow_type` 时默认为 `room`，行为不变
- 现有前端关注自习室功能不受影响
