# Design: followed-rooms-city-filter

## 背景

`GET /api/v1/room-follows?follow_type=room|course|teacher` 由 `room_follow_service.list_followed_rooms` 实现，三个分支分别 join `study_rooms` / `courses(+course_schedules)` / `teachers`。首页 `pages/index/index.vue#loadFollowedRooms` 经 `services/followedRooms.js#getAllFollowedCategories` 拉取四类关注，目前仅自习室在前端过滤城市。

## 决策

### D1: 过滤放在服务端而非前端

课程、教师分支当前返回 `city_id=None`，前端无数据可过滤；且服务端已有房间→城市的 join 能力。与 training-course-list-api 的既有口径（`city_id` 可选 Query 参数）保持一致。首页删除重复的前端过滤。

### D2: 城市匹配语义（与培训课程城市过滤统一）

```python
or_(StudyRoom.city_id == city_id, StudyRoom.city_id.is_(None))
```

未设置城市的房间（及其课程）在任何城市下都可见，避免存量数据消失。

### D3: teacher 分支用 EXISTS，且不展示无归属教师被误伤

教师与房间是 M:N（`teacher_rooms`）。可见条件：

```
EXISTS(teacher_rooms→study_rooms 且城市匹配或 NULL) OR NOT EXISTS(任何 teacher_rooms)
```

即 `or_(has_city_room, ~has_any_room)`。两个 EXISTS 子查询都显式以 `TeacherRoom.teacher_id == Teacher.id` 关联主表（避免 SQLAlchemy 自动关联冲突）。count 与列表查询使用同一谓词。

### D4: course 分支 count 需补 JOIN

course 列表查询 join `Course`+outerjoin `CourseSchedule`；加 city 条件需再 join `StudyRoom`（`Course.room_id == StudyRoom.id`，inner join 可接受——课程必有 room_id）。count 查询原本只 join Course，引用 StudyRoom 条件时必须同步加 JOIN，否则产生隐式笛卡尔积放大 total（与 training_service 相同的坑）。

### D5: 前端参数可选、默认不传

`getFollowedRooms(followType, cityId?)`、`getAllFollowedCategories(cityId?)`。favorites 页与其他调用方（booking/detail、course-detail、teacher-profile、followedCourses/Teachers service）不传参，行为零变化。首页传 `currentCityId`。

## 不做

- 不改动 follow/unfollow（POST/DELETE）接口。
- 不给课程/教师响应补真实 city_id/city_name 字段（服务端已过滤，前端不再需要）。
- 不改 favorites 页的展示逻辑。
