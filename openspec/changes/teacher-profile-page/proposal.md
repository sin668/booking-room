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
