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
