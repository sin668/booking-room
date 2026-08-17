## Why

br-app 培训课程列表页已上线，但缺少课程详情页面。用户点击课程后无法查看完整信息（教师、介绍、课程目录、评价等），也无法关注感兴趣的课程。需要参考高保真原型 `prototype/course-detail.html` 实现课程详情页，复用自习室关注机制（`room_follows` 表）并添加类型区分字段。

## What Changes

- **新增课程详情 API**：`GET /api/v1/training/courses/{course_id}` 返回课程完整信息（含教师、教室、课程目录）
- **新增课程课时表**：`course_lessons` 表存储课程目录（课时标题、时长、排序等）
- **扩展关注表**：`room_follows` 表新增 `follow_type` 字段（`room` / `course`），支持课程关注
- **新增课程详情前端页面**：`br-app/src/pages/training/course-detail.vue`，严格参考原型实现
- **课程列表导航**：培训页课程卡片点击跳转到课程详情页
- **底部操作栏**：左侧心形关注按钮 + 价格展示 + 立即预约按钮
- **数据库迁移**：为 `room_follows` 表添加 `follow_type` 列，新增 `course_lessons` 表

## Capabilities

### New Capabilities

- `course-detail-api`: 课程详情后端 API，返回课程完整信息（基本信息、教师、教室、标签、课程目录等）
- `course-lessons`: 课程课时数据模型和 API，支持课程目录展示
- `course-detail-ui`: 课程详情前端页面，包含 Hero 图、课程信息卡、教师信息、课程介绍、课程目录、学员评价、相关课程、底部操作栏（含关注按钮）
- `course-follow`: 课程关注功能，扩展 room_follows 表添加 follow_type 字段，复用已有关注 API 模式

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- **br-server**：
  - 新增路由：`br-server/app/api/routes/training.py` 添加课程详情端点
  - 新增服务方法：`br-server/app/services/training_service.py` 添加 `get_course_detail`
  - 新增模型：`br-server/app/models/course_lesson.py` 课时模型
  - 新增 Schema：`br-server/app/schemas/course.py` 添加 `CourseDetailResponse`、`LessonResponse`
  - 模型修改：`br-server/app/models/room_follow.py` 添加 `follow_type` 字段
  - 服务修改：`br-server/app/services/room_follow_service.py` 支持 follow_type 过滤
  - 路由修改：`br-server/app/api/routes/room_follow.py` 接受 follow_type 参数
  - 数据库迁移：新增 alembic 迁移文件（`course_lessons` 表 + `room_follows.follow_type` + `courses.description`）
  - 测试：新增课程详情 API 测试、课时 API 测试和课程关注测试

- **br-app**：
  - 新增页面：`br-app/src/pages/training/course-detail.vue`
  - 路由注册：`br-app/src/pages.json` 添加课程详情页路由
  - API 封装：`br-app/src/api/training.js` 添加 `getCourseDetail`
  - 导航修改：`br-app/src/pages/training/index.vue` 课程卡片添加点击跳转
  - 关注服务扩展：新建 `br-app/src/services/followedCourses.js`

- **数据库**：
  - `room_follows` 表新增 `follow_type` 列（默认值 `room`，向后兼容）
  - 新增 `course_lessons` 表
  - `courses` 表新增 `description` 列

## 回滚方案

- 后端：`follow_type` 字段设默认值 `room`，迁移可安全回滚（downgrade 删除列）；`course_lessons` 表可安全删除
- 前端：新增页面和路由，删除即可回滚，不影响现有功能
- API：新增端点，不影响现有端点
