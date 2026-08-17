# Tasks: 课程详情页

## 1. 工作区隔离

- [x] 1.1 创建 git 分支 `course-detail-page` 和对应 worktree

## 2. 数据库迁移

- [x] 2.1 `courses` 表新增 `description` 列（String(1000)，nullable）
- [x] 2.2 新建 `course_lessons` 表（course_id, title, description, duration_minutes, sort_order, is_free_preview, created_at, updated_at）
- [x] 2.3 `room_follows` 表新增 `follow_type` 列（String(20)，默认 `room`，NOT NULL）
- [x] 2.4 修改 `room_follows` 唯一约束为 `(user_id, room_id, follow_type)`
- [x] 2.5 删除 `room_follows.room_id` 外键约束，改为普通 Integer 列 + 应用层校验
- [x] 2.6 生成 alembic 迁移文件并验证

## 3. 后端：CourseLesson 模型与课时数据

- [x] 3.1 新建 `CourseLesson` 模型（`course_lesson.py`）
- [x] 3.2 新增 `LessonResponse` Schema
- [x] 3.3 课时种子数据脚本（为现有活跃课程生成示例课时）

## 4. 后端：课程详情 API

- [x] 4.1 `Course` 模型添加 `description` 字段
- [x] 4.2 `RoomFollow` 模型添加 `follow_type` 字段，更新表配置
- [x] 4.3 新增 `CourseDetailResponse` Schema（含 teacher、room、lessons、related_courses）
- [x] 4.4 `training_service.py` 新增 `get_course_detail()` 方法（含课时查询和相关课程查询）
- [x] 4.5 `training.py` 路由新增 `GET /courses/{course_id}` 端点
- [x] 4.6 更新 `training.js` 前端 API 封装，新增 `getCourseDetail(courseId)`

## 5. 后端：课程关注功能

- [x] 5.1 `room_follow_service.py` 扩展：follow/unfollow/list 支持 `follow_type` 参数
- [x] 5.2 `room_follow.py` 路由扩展：接受 `follow_type` 查询参数
- [x] 5.3 `roomFollows.js` 前端 API 层扩展 `follow_type` 参数传递

## 6. 后端：测试

- [x] 6.1 课程详情 API 测试（正常、404、非 active 状态、含课时数据）
- [x] 6.2 课程关注 API 测试（关注、取消、列表、幂等性）
- [x] 6.3 现有 room_follow 测试回归验证（确保向后兼容）

## 7. 前端：课程详情页

- [x] 7.1 创建 `course-detail.vue` 页面：Hero 区域 + 自定义导航栏
- [x] 7.2 课程信息卡（标签、名称、评分、价格）
- [x] 7.3 教师信息卡（头像、认证、评分）
- [x] 7.4 课程介绍区域（文本 + 特色亮点网格）
- [x] 7.5 课程目录区域（从 API 获取课时数据 + 展开/收起）
- [x] 7.6 学员评价区域（评分汇总 + 静态占位评价列表）
- [x] 7.7 相关课程横向滚动列表（从 API related_courses 获取）
- [x] 7.8 底部操作栏（心形关注按钮 + 价格 + 立即预约）

## 8. 前端：关注服务与导航

- [x] 8.1 新建 `followedCourses.js` 服务（本地缓存 + API 同步）
- [x] 8.2 `pages.json` 注册课程详情页路由
- [x] 8.3 `training/index.vue` 课程卡片点击跳转到课程详情页
- [x] 8.4 课程详情页关注按钮交互（关注/取消 + Toast）

## 9. 构建验证

- [x] 9.1 后端 pytest 全部通过
- [x] 9.2 前端 br-app 构建无错误
