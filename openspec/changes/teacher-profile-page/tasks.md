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
