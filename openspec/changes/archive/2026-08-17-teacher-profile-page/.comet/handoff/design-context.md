# Comet Design Handoff

- Change: teacher-profile-page
- Phase: design
- Mode: compact
- Context hash: ccaa8cbca092d7eded3687ad91f31ded5e836a0da3a957a00d794a62662535c1

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/teacher-profile-page/proposal.md

- Source: openspec/changes/teacher-profile-page/proposal.md
- Lines: 1-40
- SHA256: 7dec3e2a3f7ec58804ebba62692ff833be86cd963716bccbaa0d407bf0e023de

```md
## Why

课程详情页（course-detail.vue）的教师信息卡点击后仅显示"教师主页开发中"的 Toast，缺少教师简介页面。用户无法查看教师的详细介绍、所授课程列表和学员评价，影响培训课程的转化率和用户体验。

## What Changes

- 新增 br-app 教师简介页面（`pages/teacher/profile.vue`），严格参考 `prototype/teacher-profile.html` 原型设计
- 页面包含：教师 Hero 区（头像、姓名、认证标签、教龄等）、统计行（学员数量/授课课程/综合评分）、个人简介、资质认证、教学特色、主讲课程列表、学员评价（静态占位数据）
- 主讲课程列表复用培训室概况页（booking/detail.vue）的"本培训室课程"卡片样式，但将"主讲老师"行替换为原型中的"共X课时 · 含资料"行
- 底部操作栏新增心状关注按钮，使用 `room_follows` 表并新增 `teacher` 关注类型（扩展现有 `follow_type` 枚举）
- 底部"查看课程"按钮改为"返回课程"按钮，点击跳转 `/pages/training/index`
- 后端新增 `GET /api/v1/teachers/{teacher_id}` 教师详情 API，返回教师信息及其所授课程列表
- 扩展 `room_follows` API 的 `follow_type` 参数，支持 `teacher` 类型
- 课程详情页的 `onTeacherTap()` 改为跳转到教师简介页
- Teacher 模型新增 `bio`（个人简介）、`student_count`（学员数量）等字段以支撑页面展示

## Capabilities

### New Capabilities

- `teacher-profile-api`: 教师详情 API，按 teacher_id 返回教师基本信息及其所授活跃课程列表，支撑 br-app 教师简介页数据展示
- `teacher-profile-ui`: br-app 教师简介前端页面，包含教师信息展示、课程列表、关注按钮和学员评价占位区域
- `teacher-follow`: 扩展 room_follows 关注类型支持 teacher，包括 API 参数扩展和前端关注/取消关注交互

### Modified Capabilities

- `training-room-detail-api`: 教师响应结构需扩展 `bio` 和 `student_count` 字段，以支撑教师简介页的数据需求

## Impact

- **br-app**: 新增页面 `pages/teacher/profile.vue`，修改 `pages.json` 路由注册，修改 `pages/training/course-detail.vue` 的 `onTeacherTap()` 跳转逻辑，新增 `api/teacher.js` API 封装，扩展 `services/followedRooms.js` 支持 teacher 类型
- **br-server**: 新增教师详情路由和服务，Teacher 模型扩展字段（alembic 迁移），room_follow 路由和服务的 follow_type 参数扩展（`^(room|course)$` → `^(room|course|teacher)$`）
- **数据库**: Teacher 表新增 `bio`、`student_count` 列；room_follows 表 follow_type 的校验模式需更新
- **依赖**: 无新增外部依赖

## 回滚方案

- 前端：删除 teacher/profile.vue 页面及路由注册，恢复 course-detail.vue 的 `onTeacherTap()` 为 Toast 提示
- 后端：回退 Teacher 模型迁移，回退 room_follow API 的 follow_type 参数校验
- 数据：Teacher 表新增列可保留，不影响现有功能

```

## openspec/changes/teacher-profile-page/design.md

- Source: openspec/changes/teacher-profile-page/design.md
- Lines: 1-66
- SHA256: 7b6c5d8c1f0733aa0499ca8e41a793d619f3899463c4b0b2c8b3f626a2a7ff1e

```md
## Context

当前 Teacher 模型字段有限（name, avatar, title, rating），缺少教师简介页所需的 bio、student_count 等字段。room_follows 的 follow_type 已支持 room 和 course，扩展 teacher 类型是低成本的。培训室概况页（booking/detail.vue）的课程列表卡片结构可作为教师简介页课程卡片的参考基础。原型设计见 `prototype/teacher-profile.html`。

## Goals / Non-Goals

**Goals:**
- 新增教师详情 API 和前端教师简介页面
- 扩展 Teacher 模型支持 bio 和 student_count
- 扩展 room_follows follow_type 支持 teacher
- 课程卡片展示"共X课时 · 含资料"（通过查询 course_lessons 计数获取 lesson_count）

**Non-Goals:**
- 学员评价暂不实现后端 API，前端使用静态占位数据
- 不实现教师资质认证、教学特色等后端字段（原型中的资质认证和教学特色区域使用前端静态数据）
- 不修改 br-admin 管理后台

## Decisions

### Decision 1: Teacher 模型扩展方式 — 直接新增列

**选择**: 在 Teacher 表新增 `bio` (String(1000), nullable) 和 `student_count` (Integer, default=0) 列。

**理由**: 字段简单且确定性强，直接扩展最直观。不需要 JSON 扩展或关联表。

**替代方案**: 使用 JSON 扩展字段存储教师元数据 — 过于灵活，查询不便，且 bio 和 student_count 是高频展示字段。

### Decision 2: 教师详情 API 的课程 lesson_count 获取方式

**选择**: 在 TeacherService 中通过 `func.count(CourseLesson.id)` 子查询批量获取每门课程的课时数，避免 N+1 查询。

**理由**: 一次查询获取所有课程的课时计数，性能优于逐课程查询。

**替代方案**: 在 Course 模型新增 lesson_count 冗余字段 — 增加数据一致性维护成本，不推荐。

### Decision 3: 教师关注使用 room_follows 表 + follow_type=teacher

**选择**: 复用现有 room_follows 表和 follow_type 机制，新增 "teacher" 类型。API 的 follow_type 参数正则从 `^(room|course)$` 扩展为 `^(room|course|teacher)$`。

**理由**: 最小改动量，与现有 room/course 关注行为一致。唯一约束 `(user_id, room_id, follow_type)` 天然支持同一 teacher_id 在不同 follow_type 下的独立关注。

**注意**: room_follows 表的 `room_id` 列在 teacher 类型中存储的是 teacher_id，语义上是"被关注目标 ID"。无需改名列名，但服务和 API 层需文档化说明。

### Decision 4: 前端教师关注状态管理

**选择**: 新建 `services/followedTeachers.js`，参照 `services/followedRooms.js` 的模式，使用独立 localStorage key `followed_teachers` 管理教师关注状态。API 调用使用 `follow_type=teacher`。

**理由**: 与现有 room/course 关注逻辑隔离，避免互相干扰。遵循项目已有的服务分层模式。

### Decision 5: 前端页面文件位置

**选择**: 新页面放在 `br-app/src/pages/teacher/profile.vue`，路由注册为 `pages/teacher/profile`。

**理由**: 与 `pages/training/` 目录平行，语义清晰。未来如需增加教师相关其他页面（如教师课程列表），可在 `pages/teacher/` 目录下扩展。

### Decision 6: 课程卡片"共X课时 · 含资料"的数据来源

**选择**: 后端教师详情 API 返回的每门课程包含 `lesson_count` 字段（该课程的 course_lessons 记录数）。前端直接展示 `共{lesson_count}课时 · 含资料`。

**理由**: 后端聚合查询比前端多次请求更高效，且 lesson_count 是课程的固有属性。

## Risks / Trade-offs

- **room_follows.room_id 语义**: teacher 类型中 room_id 存储 teacher_id，可能造成理解歧义。通过在服务和 API 层文档化说明来缓解。
- **Teacher 表迁移**: 新增列需 alembic 迁移，对已有数据无影响（均为 nullable/有默认值）。
- **前端静态评价数据**: 后续实现真实评价 API 时需要替换，但页面结构已预留评价区域，改动量可控。

```

## openspec/changes/teacher-profile-page/tasks.md

- Source: openspec/changes/teacher-profile-page/tasks.md
- Lines: 1-44
- SHA256: 68bea3b967324333713c0fe3d255a440d442653c338cda6cbf0ab13a8004e6be

```md
## 1. 后端 — Teacher 模型扩展与迁移

- [ ] 1.1 Teacher 模型新增 `bio` (String(1000), nullable) 和 `student_count` (Integer, default=0) 字段
- [ ] 1.2 生成 alembic 迁移文件，为 teachers 表添加 bio 和 student_count 列
- [ ] 1.3 更新 TeacherResponse schema，新增 bio 和 student_count 字段
- [ ] 1.4 更新培训室详情 API 的 TeacherBrief schema，同步新增 bio 和 student_count 字段

## 2. 后端 — 教师详情 API

- [ ] 2.1 新建 `br-server/app/schemas/teacher.py` 中的 TeacherDetailResponse（含 courses 数组和 lesson_count）
- [ ] 2.2 新建 `br-server/app/services/teacher_service.py`，实现 get_teacher_detail 方法（查询教师信息 + 关联课程 + 课时计数）
- [ ] 2.3 新建 `br-server/app/api/routes/teacher.py` 路由，注册 `GET /api/v1/teachers/{teacher_id}`（不使用尾部斜杠）
- [ ] 2.4 在 `br-server/app/main.py` 注册 teacher 路由
- [ ] 2.5 编写教师详情 API 单元测试（覆盖有课程、无课程、不存在教师场景）

## 3. 后端 — room_follows follow_type 扩展

- [ ] 3.1 扩展 room_follow 路由的 follow_type 参数正则：`^(room|course)$` → `^(room|course|teacher)$`
- [ ] 3.2 扩展 room_follow_service 的 follow/unfollow/list 方法，支持 teacher 类型（teacher 类型不校验 study_rooms 表，直接创建记录）
- [ ] 3.3 编写 teacher follow 类型单元测试（关注、取消关注、幂等、类型隔离）

## 4. 前端 — API 层与服务层

- [ ] 4.1 新建 `br-app/src/api/teacher.js`，封装 getTeacherDetail API
- [ ] 4.2 新建 `br-app/src/services/followedTeachers.js`，实现教师关注/取消关注/状态查询（参照 followedRooms.js 模式，使用独立 localStorage key）
- [ ] 4.3 扩展 `br-app/src/api/roomFollows.js`，followRoom/unfollowRoom 支持传入 follow_type='teacher'

## 5. 前端 — 教师简介页面

- [ ] 5.1 创建 `br-app/src/pages/teacher/profile.vue` 页面，严格参考 `prototype/teacher-profile.html` 原型实现以下区域：Hero 区、统计行、个人简介、主讲课程列表、学员评价（静态占位）、底部操作栏
- [ ] 5.2 主讲课程列表复用培训室概况页的课程卡片结构，将"主讲老师"行替换为"共X课时 · 含资料"行
- [ ] 5.3 实现心状关注按钮交互（右上角 + 底部操作栏），调用 followedTeachers 服务
- [ ] 5.4 底部"返回课程"按钮点击跳转 `/pages/training/index`（switchTab）
- [ ] 5.5 在 `pages.json` 注册 `pages/teacher/profile` 路由（自定义导航栏）

## 6. 前端 — 课程详情页集成

- [ ] 6.1 修改 `course-detail.vue` 的 `onTeacherTap()` 方法，跳转到 `/pages/teacher/profile?teacher_id={teacher.id}`

## 7. 验证

- [ ] 7.1 后端 pytest 全部通过（新增测试 + 回归测试）
- [ ] 7.2 前端构建无错误（`npm run build`）
- [ ] 7.3 检查避免 bug-fixed.md 中的已知问题：onMounted 从 vue 导入（BUG-14）、路由不使用尾部斜杠（BUG-22）、WXML 不使用 HTML 实体（BUG-20）

```

## openspec/changes/teacher-profile-page/specs/teacher-follow/spec.md

- Source: openspec/changes/teacher-profile-page/specs/teacher-follow/spec.md
- Lines: 1-39
- SHA256: 6a35d1708b00895853563377754327ba57ebfb954d014f1605accd5b9807cb87

```md
## Purpose

扩展 room_follows 关注系统支持 teacher 关注类型，使用户可以关注/取消关注教师，与现有的 room 和 course 关注类型并存。

## ADDED Requirements

### Requirement: follow_type 参数支持 teacher

room_follows API 的 `follow_type` 查询参数 SHALL 从 `^(room|course)$` 扩展为 `^(room|course|teacher)$`，支持教师关注/取消关注/列表查询。

#### Scenario: 关注教师

- **GIVEN** 用户未关注教师 id=1
- **WHEN** 客户端发送 `POST /api/v1/room-follows/1?follow_type=teacher`
- **THEN** 返回 HTTP 201，创建 `follow_type=teacher` 的关注记录

#### Scenario: 取消关注教师

- **GIVEN** 用户已关注教师 id=1（`follow_type=teacher`）
- **WHEN** 客户端发送 `DELETE /api/v1/room-follows/1?follow_type=teacher`
- **THEN** 返回 HTTP 204，仅删除 `follow_type=teacher` 的记录，不影响同一 room_id 的其他 follow_type 记录

#### Scenario: 查询教师关注列表

- **GIVEN** 用户关注了 2 位教师
- **WHEN** 客户端发送 `GET /api/v1/room-follows?follow_type=teacher`
- **THEN** 返回 HTTP 200，`total` 为 2

#### Scenario: 重复关注教师（幂等）

- **GIVEN** 用户已关注教师 id=1（`follow_type=teacher`）
- **WHEN** 客户端再次发送 `POST /api/v1/room-follows/1?follow_type=teacher`
- **THEN** 返回 HTTP 200，不创建重复记录

#### Scenario: teacher 类型与 room/course 类型互不干扰

- **GIVEN** 用户对同一 id=1 分别有 `follow_type=room` 和 `follow_type=teacher` 的关注记录
- **WHEN** 客户端发送 `DELETE /api/v1/room-follows/1?follow_type=teacher`
- **THEN** 仅删除 `follow_type=teacher` 的记录，`follow_type=room` 的记录保留

```

## openspec/changes/teacher-profile-page/specs/teacher-profile-api/spec.md

- Source: openspec/changes/teacher-profile-page/specs/teacher-profile-api/spec.md
- Lines: 1-45
- SHA256: 8eba93b1992ca56a21ae9eebd08a1dee53ac86fdaf6d29a46a5d9e1030a923a9

```md
## Purpose

教师详情 API 提供按教师 ID 查询单个教师详情的接口，返回教师基本信息及其所授活跃课程列表，支撑 br-app 教师简介页面的数据展示。

## ADDED Requirements

### Requirement: Get teacher detail API

系统 SHALL 提供 `GET /api/v1/teachers/{teacher_id}` 接口，按教师 ID 返回教师详情。响应 SHALL 包含教师基本信息和该教师所授的所有活跃课程列表。路由定义不使用尾部斜杠。

#### Scenario: Successful detail request for teacher with courses

- **GIVEN** 一位 id=1 的教师，关联了 3 门 `status=active` 的课程
- **WHEN** 客户端发送 `GET /api/v1/teachers/1`
- **THEN** 返回 HTTP 200，响应包含教师基本信息（id、name、avatar、title、rating、bio、student_count）和 `courses` 数组
- **AND** 每门课程包含 id、name、cover_image、category、price、rating、enrollment_count、schedule、tags（数组）、status、room_id、room_name、lesson_count（课时数）

#### Scenario: Teacher with no courses

- **GIVEN** 一位 id=2 的教师，未关联任何活跃课程
- **WHEN** 客户端发送 `GET /api/v1/teachers/2`
- **THEN** 返回 HTTP 200，`courses` 数组为空

#### Scenario: Non-existent teacher returns 404

- **WHEN** 客户端发送 `GET /api/v1/teachers/999`
- **THEN** 返回 HTTP 404，错误信息说明教师不存在

#### Scenario: Teacher detail includes bio and student_count

- **GIVEN** 一位 id=1 的教师，`bio` 字段为 "专注考研政治辅导8年"，`student_count` 为 328
- **WHEN** 客户端发送 `GET /api/v1/teachers/1`
- **THEN** 响应中 `bio` 为 "专注考研政治辅导8年"，`student_count` 为 328

#### Scenario: Teacher with null bio

- **GIVEN** 一位 id=3 的教师，`bio` 字段为 null
- **WHEN** 客户端发送 `GET /api/v1/teachers/3`
- **THEN** 响应中 `bio` 为 null

#### Scenario: Course lesson_count in response

- **GIVEN** 教师 id=1 的一门课程关联了 12 个课时（course_lessons 记录）
- **WHEN** 客户端发送 `GET /api/v1/teachers/1`
- **THEN** 该课程的 `lesson_count` 为 12

```

## openspec/changes/teacher-profile-page/specs/teacher-profile-ui/spec.md

- Source: openspec/changes/teacher-profile-page/specs/teacher-profile-ui/spec.md
- Lines: 1-93
- SHA256: db21474356d31a5fd69f80083f72b3051b1a4debeb8c523043a815d2e6526790

[TRUNCATED]

```md
## Purpose

教师简介前端页面展示教师的详细信息、主讲课程列表和学员评价，为 br-app 用户提供完整的教师认知和关注入口。

## ADDED Requirements

### Requirement: 教师简介页面路由

系统 SHALL 在 `pages/teacher/profile.vue` 注册教师简介页面，通过 `pages.json` 配置路由 `pages/teacher/profile`，接收 `teacher_id` 查询参数。页面使用自定义导航栏。

#### Scenario: 从课程详情页跳转到教师简介页

- **GIVEN** 用户在课程详情页，该课程关联了教师 id=1
- **WHEN** 用户点击教师信息卡
- **THEN** 跳转到 `/pages/teacher/profile?teacher_id=1`

### Requirement: 教师信息展示

页面 SHALL 展示教师 Hero 区（背景渐变、头像、姓名、认证标签、教龄/学历信息）、统计行（学员数量、授课课程数、综合评分）、个人简介区域。

#### Scenario: 加载教师详情数据

- **GIVEN** 教师 id=1 存在且后端返回有效数据
- **WHEN** 页面加载完成
- **THEN** 展示教师头像、姓名、认证标签、bio 信息
- **AND** 统计行显示学员数量、授课课程数（courses 数组长度）、综合评分

#### Scenario: 教师数据加载失败

- **WHEN** 后端 API 返回 404 或网络错误
- **THEN** 显示错误提示，不展示页面内容

### Requirement: 主讲课程列表

页面 SHALL 展示该教师的所有课程列表，卡片样式复用培训室概况页的"本培训室课程"卡片结构。每张课程卡片 SHALL 包含课程封面、课程名称、"共X课时 · 含资料"行（替换原"主讲老师"行）、评分和学员数、价格和预约按钮。

#### Scenario: 展示课程列表

- **GIVEN** 教师 id=1 关联了 2 门活跃课程
- **WHEN** 页面加载完成
- **THEN** 显示"主讲课程"标题和"共2门"副标题
- **AND** 展示 2 张课程卡片

#### Scenario: 课程卡片显示课时数

- **GIVEN** 一门课程关联了 12 个课时
- **WHEN** 课程卡片渲染完成
- **THEN** 显示"共12课时 · 含资料"

#### Scenario: 无课程时显示空状态

- **GIVEN** 教师未关联任何活跃课程
- **WHEN** 页面加载完成
- **THEN** 显示"暂无课程"空状态提示

### Requirement: 心状关注按钮

页面右上角 SHALL 显示心状关注按钮（未关注时为空心 `far fa-heart`，已关注时为实心 `fas fa-heart`）。点击按钮调用 `room_follows` API，`follow_type=teacher`。

#### Scenario: 关注教师

- **GIVEN** 用户未关注该教师
- **WHEN** 用户点击心状关注按钮
- **THEN** 调用 `POST /api/v1/room-follows/{teacher_id}?follow_type=teacher`
- **AND** 按钮变为已关注状态（实心心）
- **AND** 显示"已关注"Toast

#### Scenario: 取消关注教师

- **GIVEN** 用户已关注该教师
- **WHEN** 用户点击心状关注按钮
- **THEN** 调用 `DELETE /api/v1/room-follows/{teacher_id}?follow_type=teacher`
- **AND** 按钮变为未关注状态（空心心）
- **AND** 显示"已取消关注"Toast

### Requirement: 学员评价区域

页面 SHALL 展示学员评价区域，使用静态占位数据。评价区域包含标题"学员评价"、评价数量、评价列表和"查看全部评价"按钮。

#### Scenario: 展示静态评价数据

```

Full source: openspec/changes/teacher-profile-page/specs/teacher-profile-ui/spec.md

## openspec/changes/teacher-profile-page/specs/training-room-detail-api/spec.md

- Source: openspec/changes/teacher-profile-page/specs/training-room-detail-api/spec.md
- Lines: 1-17
- SHA256: bc3cf440ebc9ab041223ee8ef3bad907291ef4df3468bf53400dbc9a43fcc9c6

```md
## MODIFIED Requirements

### Requirement: Teacher response includes bio and student_count fields

培训室详情 API 的教师响应结构 SHALL 在现有字段（id、name、avatar、title、rating）基础上新增 `bio`（个人简介，可为 null）和 `student_count`（学员数量，整数，默认 0）字段。

#### Scenario: Teacher with bio in training room detail

- **GIVEN** 培训室 id=1 的一位教师 bio 为 "专注考研政治辅导8年"，student_count 为 328
- **WHEN** 客户端发送 `GET /api/v1/training/rooms/1`
- **THEN** `teachers` 数组中该教师的 `bio` 为 "专注考研政治辅导8年"，`student_count` 为 328

#### Scenario: Teacher with null bio in training room detail

- **GIVEN** 培训室 id=1 的一位教师 bio 为 null
- **WHEN** 客户端发送 `GET /api/v1/training/rooms/1`
- **THEN** `teachers` 数组中该教师的 `bio` 为 null，`student_count` 为 0

```
