# 关注课程仅展示有进行中固定班课排课的课程

## Why

br-app 首页「关注课程」板块与 /pages/favorites 关注课程 Tab 目前会展示没有进行中固定班课排课的关注课程（后端 `follow_type=course` 列表对 `course_schedules` 是 LEFT JOIN 语义，无排课也返回，仅价格显示为 0/免费）。这与 C 端其他课程页面的统一口径（`training_service._has_in_progress_fixed_schedule()`：没有进行中固定班课排课的课程不展示）不一致，用户会点进已无可报名班期的课程。

## What Changes

- 后端 `GET /api/v1/room-follows?follow_type=course` 增加过滤：仅返回至少存在一条 `schedule_type=fixed` 且 `schedule_status=in_progress` 排课记录的关注课程；`total` 与列表同口径。
- 复用 `training_service._has_in_progress_fixed_schedule()` 作为单一口径来源，不新增前端改动（首页与 favorites 页均消费该接口）。
- 同步修复/补充相关测试 fixture（关注课程测试此前均未建排课）。

## Impact

- 影响的 capability：`followed-rooms-city-filter`（同一关注列表接口，新增展示口径 requirement）
- 影响的代码：`br-server/app/services/room_follow_service.py`、`br-server/tests/`（test_course_follow.py、test_room_follow_service.py、test_follow_city_filter.py）
- `follow_type=room|teacher` 分支与 follow/unfollow 写接口不变；无 API 签名变更
