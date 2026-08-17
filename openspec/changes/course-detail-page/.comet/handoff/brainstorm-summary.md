# Brainstorm Summary

- Change: course-detail-page
- Date: 2026-08-17

## 确认的技术方案

### 后端

1. **数据库迁移**（单个 alembic 迁移文件）：
   - `courses` 表新增 `description` 列（String(1000), nullable）
   - 新建 `course_lessons` 表（course_id FK, title, description, duration_minutes, sort_order, is_free_preview, created_at, updated_at）
   - `room_follows` 表添加 `follow_type` 列（String(20), server_default='room', NOT NULL）
   - 删除唯一约束 `uq_room_follows_user_room`，新建 `uq_room_follows_user_room_type(user_id, room_id, follow_type)`
   - 删除 `room_follows.room_id` 外键约束，改为普通 Integer 列 + 应用层校验

2. **RoomFollow 模型改造**：保留列名 `room_id` 不变，添加 `follow_type` 字段。删除 ForeignKey 约束，保留 Integer + index。服务层所有方法加 `follow_type` 参数过滤。

3. **课程详情 API**：`GET /api/v1/training/courses/{course_id}`
   - 3 步查询避免 N+1：Course+Teacher+Room → Lessons → Related courses
   - 新增 Schema：`CourseDetailResponse`、`LessonResponse`、`RoomBrief`、`RelatedCourseItem`

4. **关注 API 扩展**：现有端点添加 `follow_type` 查询参数（默认 `room`），向后兼容。

### 前端

5. **course-detail.vue**：Options API 单文件组件，严格参考原型。Hero + 课程信息卡 + 教师卡 + 课程介绍 + 课程目录（API 数据） + 评价（静态占位） + 相关课程（API） + 底部操作栏。

6. **followedCourses.js**：与 `followedRooms.js` 平行，独立 storage key `followed_courses`。

7. **API 层扩展**：`training.js` 新增 `getCourseDetail`，`roomFollows.js` 扩展 `follow_type` 参数。

## 关键取舍与风险

| 取舍/风险 | 决策 |
|-----------|------|
| `room_id` 列名语义不一致 | 保留列名，应用层通过 `follow_type` 解释，减少迁移风险 |
| 删除外键约束 | 必须删除以支持多态引用，应用层校验替代 |
| 评价用静态数据 | 组件预留数据接口，后续替换为 API |
| 课时嵌入详情 API | 避免独立端点，减少请求数 |
| 单文件组件 vs 多组件拆分 | 单文件与 `booking/detail.vue` 风格一致 |

## 测试策略

- 课程详情 API：正常、404、非 active、含课时、无课时空数组、相关课程排除当前课程
- 课程关注：关注/取消/列表/幂等性/同 target 不同 follow_type 并存
- 回归：现有 room_follow 测试全部通过（follow_type 默认 room）
- 前端：br-app 构建无错误

## Spec Patch

无。OpenSpec delta spec 已完整覆盖所有验收场景。
