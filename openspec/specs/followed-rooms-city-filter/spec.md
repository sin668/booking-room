# followed-rooms-city-filter Specification

## Purpose
TBD - created by archiving change followed-rooms-city-filter. Update Purpose after archive.

## Requirements

### Requirement: Followed rooms list city filtering

`GET /api/v1/room-follows` SHALL 支持可选查询参数 `city_id`（整数，>=1）。传入时，`follow_type=room` 分支 SHALL 只返回所属房间 `city_id` 匹配的房间关注；`follow_type=course` 分支 SHALL 经 `courses.room_id → study_rooms.city_id` 过滤课程关注。归属房间 `city_id` 为 NULL 的记录 SHALL 在任何城市过滤下仍然可见。不传 `city_id` 时接口行为 SHALL 与现状完全一致，`total` SHALL 与过滤后的 items 数量一致。

#### Scenario: 按城市过滤房间关注

- **WHEN** 用户关注了城市 A 与城市 B 的各一间房间，请求 `city_id=A`
- **THEN** 仅返回城市 A 的房间关注，`total` 为 1

#### Scenario: 未设置城市的房间始终可见

- **WHEN** 用户关注了一间 `city_id` 为 NULL 的房间，请求任意 `city_id`
- **THEN** 该房间关注仍被返回

#### Scenario: 课程按所属房间城市过滤

- **WHEN** 用户关注了属城市 A 房间的课程和属城市 B 房间的课程，请求 `follow_type=course&city_id=B`
- **THEN** 仅返回城市 B 房间下的课程关注

#### Scenario: 不传 city_id 行为不变

- **WHEN** 请求不带 `city_id`
- **THEN** 返回该用户该 `follow_type` 的全部关注（含所有城市）

### Requirement: Followed teachers city filtering

`follow_type=teacher` 且传入 `city_id` 时，系统 SHALL 仅返回满足以下任一条件的教师关注：(a) 经 `teacher_rooms → study_rooms` 存在至少一个城市匹配或 `city_id` 为 NULL 的归属房间；(b) 该教师在 `teacher_rooms` 中无任何房间关联。

#### Scenario: 教师任一归属房间匹配城市

- **WHEN** 教师甲关联了城市 A 与城市 B 两间培训室，用户已关注，请求 `follow_type=teacher&city_id=B`
- **THEN** 教师甲被返回

#### Scenario: 教师归属房间均不匹配城市

- **WHEN** 教师乙只关联城市 A 的培训室，请求 `city_id=B`
- **THEN** 教师乙不被返回

#### Scenario: 无房间关联的教师始终可见

- **WHEN** 教师丙在 `teacher_rooms` 中无记录，请求任意 `city_id`
- **THEN** 已关注的教师丙仍被返回

### Requirement: Homepage follow sections city linkage

br-app 首页的「关注自习室 / 关注培训室 / 关注课程 / 关注教师」四个板块 SHALL 将当前选中城市的 `city_id` 传给关注列表接口，由服务端完成过滤；首页 SHALL 不再对返回结果做前端城市过滤。其他关注消费方（favorites 页、详情页关注态）不传 `city_id`，行为保持不变。

#### Scenario: 切换城市后首页关注板块联动

- **WHEN** 用户在首页把城市从 A 切换到 B 后页面重新加载数据
- **THEN** 四个关注板块仅展示城市 B（及无城市归属）的房间、课程与教师

#### Scenario: 未选择城市时不过滤

- **WHEN** 城市 store 无当前城市（`currentCityId` 为 null）
- **THEN** 首页请求不携带 `city_id`，展示全部关注

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
