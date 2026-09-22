## ADDED Requirements

### Requirement: Followed courses schedule visibility

`GET /api/v1/room-follows?follow_type=course` SHALL 仅返回至少存在一条 `schedule_type=fixed` 且 `schedule_status=in_progress` 排课记录的关注课程；`total` SHALL 与过滤后的 items 数量一致。该口径 SHALL 与 C 端其他课程页面（课程列表/培训室详情/热门课程/相关课程）的隐藏规则一致。`follow_type=room|teacher` 及关注/取消关注接口 SHALL 不受影响。

#### Scenario: 有进行中固定班课排课的关注课程正常返回

- **WHEN** 用户关注的课程存在一条 fixed + in_progress 排课
- **THEN** 该课程出现在关注课程列表中，价格取该排课的价格

#### Scenario: 无进行中固定班课排课的关注课程被隐藏

- **WHEN** 用户关注的课程没有任何排课，或排课为 pending_start / completed / custom 类型
- **THEN** 该课程不出现在关注课程列表中，且不计入 `total`

#### Scenario: 房间与教师关注不受影响

- **WHEN** 请求 `follow_type=room` 或 `follow_type=teacher`
- **THEN** 返回结果与本变更前的口径一致（不按排课过滤）
