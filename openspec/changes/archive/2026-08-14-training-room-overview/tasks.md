## 1. 后端 Schema

- [x] 1.1 在 `br-server/app/schemas/course.py` 新增 `TrainingRoomDetailResponse`：包含房间基本信息字段（id、name、description、cover_image、address、business_hours、status、room_type、min_price、city_id、city_name、rating）+ `teachers` 数组（TeacherResponse 嵌套）+ `courses` 数组（CourseResponse 嵌套）+ 教室概况统计字段（classroom_count、class_capacity、teacher_count、total_students）
- [x] 1.2 确认 `TeacherResponse`（id、name、avatar、title、rating）已在 `br-server/app/schemas/teacher.py` 中定义（由 `training-course-list` change 创建），如不存在则创建
- [x] 1.3 确认 `CourseResponse`（含 teacher 嵌套对象、tags 数组解析）已在 `br-server/app/schemas/course.py` 中定义（由 `training-course-list` change 创建），如不存在则创建

## 2. 后端 Service

- [x] 2.1 在 `br-server/app/services/training_service.py` 新增 `get_training_room_detail(room_id: int)` 方法：查询 `study_rooms` 表中 `room_type in (training, comprehensive)` 且指定 id 的房间，如果不存在或类型不匹配返回 None
- [x] 2.2 在 `get_training_room_detail` 中查询该房间下所有 `status=active` 的课程（JOIN teachers 获取教师信息），按 `sort_order` 排序
- [x] 2.3 在 `get_training_room_detail` 中从课程列表提取去重后的教师列表
- [x] 2.4 在 `get_training_room_detail` 中聚合教室概况统计数据：培训教室数（该房间下 status=active 的课程总数）、小班容量（固定值 8-12）、认证讲师数（去重教师数）、累计学员数（该房间所有课程 enrollment_count 之和）
- [x] 2.5 组装 `TrainingRoomDetailResponse` 并返回

## 3. 后端 API Routes

- [x] 3.1 在 `br-server/app/api/routes/training.py` 新增 `GET /{room_id}` 路由（**注意：路由定义不使用尾部斜杠，参考 bug-fixed.md BUG-22**），调用 `training_service.get_training_room_detail(room_id)`，返回 `TrainingRoomDetailResponse`
- [x] 3.2 路由处理 404 情况：房间不存在或类型不是 training/comprehensive 时返回 HTTP 404
- [x] 3.3 确认路由已在 `br-server/app/main.py` 中注册（由 `training-course-list` change 创建的 training_router，新增路由会自动包含）

## 4. 后端测试

- [x] 4.1 在 `br-server/tests/test_training_api.py` 新增培训室详情接口测试：正常请求培训室详情（验证响应字段完整性：房间信息、teachers 数组、courses 数组、教室概况统计）
- [x] 4.2 新增综合室详情请求测试：验证综合室返回与培训室相同的结构
- [x] 4.3 新增 404 场景测试：请求自习室 room_id 返回 404、请求不存在的 room_id 返回 404
- [x] 4.4 新增教师去重测试：多门课程关联同一教师时 teachers 数组去重
- [x] 4.5 新增空课程场景测试：培训室无课程时 teachers 和 courses 数组为空
- [x] 4.6 新增 tags 解析测试：课程 tags 字段从逗号分隔字符串解析为数组
- [x] 4.7 新增无教师课程测试：课程未关联教师时 teacher 字段为 null
- [x] 4.8 运行 `pytest tests/test_training_api.py -q` 确保全部测试通过（**注意：依赖 training-course-list change 的数据库迁移已执行**）

## 5. 前端 API 模块

- [x] 5.1 在 `br-app/src/api/training.js` 新增 `getTrainingRoomDetail(roomId)` 函数，封装 `GET /api/v1/training/rooms/{room_id}` 请求（**注意：URL 不使用尾部斜杠，参考 bug-fixed.md BUG-22**）

## 6. 前端页面实现

- [x] 6.1 修改 `br-app/src/pages/booking/detail.vue` 的 `data()` 增加 `trainingData`（存储培训室详情数据：teachers、courses、教室概况统计）和 `roomType`（从房间信息获取 room_type 字段）
- [x] 6.2 修改 `loadData()` 方法：先调用 `fetchBookingRoom(this.roomId)` 获取房间基本信息和 room_type，再根据 room_type 条件调用后续 API（**注意：Vue3 生命周期钩子从 `vue` 包导入，参考 bug-fixed.md BUG-14**）
  - room_type=study：调用 `getSeatStats(this.roomId)`（现有逻辑）
  - room_type=training：调用 `getTrainingRoomDetail(this.roomId)`
  - room_type=comprehensive：`Promise.all` 并行调用 `getSeatStats` 和 `getTrainingRoomDetail`
- [x] 6.3 新增 computed 属性：`isStudyRoom`、`isTrainingRoom`、`isComprehensiveRoom`、`trainingRoomStats`（教室概况统计）、`teachers`（名师团队列表）、`courses`（课程列表）
- [x] 6.4 在模板中添加条件渲染：培训室显示教室概况（替换座位概况）、名师团队横向滚动卡片、本培训室课程纵向列表
- [x] 6.5 综合室模板中保留座位概况，并在其下方添加教室概况、名师团队、课程列表
- [x] 6.6 实现教室概况统计卡片 UI（参考 prototype/training-room.html，2x2 网格：培训教室数、小班容量、认证讲师、累计学员）
- [x] 6.7 实现名师团队横向滚动卡片 UI（教师头像、姓名、头衔、评分，横向 scroll-view）
- [x] 6.8 实现本培训室课程纵向列表 UI（封面图、课程名、状态标签、教师信息、排课时间、价格、预约入口，参考 prototype/training-room.html）
- [x] 6.9 修改底部操作栏条件渲染：
  - study：心状关注按钮 + "立即预约"按钮（现有逻辑）
  - training：心状关注按钮 + "返回课程"按钮（跳转到 `pages/training/index`）
  - comprehensive：心状关注按钮 + "预约自习室"按钮（跳转到座位选择页）
- [x] 6.10 实现空状态提示：培训室无课程时名师团队和课程列表区域显示"暂无课程"
- [x] 6.11 新增"返回课程"按钮的 `onBackToCourses()` 方法和"预约自习室"按钮的 `onBookStudy()` 方法
- [x] 6.12 **注意：避免在 Vue 模板中使用 `&lt;` 和 `&gt;` HTML 实体，使用 Unicode 字符（参考 bug-fixed.md BUG-20）**
- [x] 6.13 新增 SCSS 样式：教室概况统计卡片、名师团队卡片、课程列表卡片、培训室简介、教学设施网格等样式，保持与现有 detail.vue 风格一致（rpx 单位、SCSS 变量、rounded-2xl shadow-sm）

## 7. 代码审查与重构

- [x] 7.1 确保后端 Clean Architecture 分层：routes 仅处理 HTTP → services 处理业务逻辑 → models 定义数据 → schemas 定义响应
- [x] 7.2 消除重复代码：复用 `training-course-list` change 已定义的 `TeacherResponse` 和 `CourseResponse`，不重复定义
- [x] 7.3 确保前端组件分层：detail.vue 调用 api 模块，api 模块调用 utils/request.js
- [x] 7.4 检查所有新路由无尾部斜杠，与现有路由风格一致

## 8. API 文档更新

- [x] 8.1 在 `docs/api.md` 补充 `GET /api/v1/training/rooms/{room_id}` 接口文档（路径、路径参数、响应示例、404 场景说明）

## 9. 最终验证

- [x] 9.1 运行后端全部测试：`conda activate booking-room && cd br-server && pytest tests/ -q`（**注意：依赖 training-course-list change 的数据库迁移已执行**）
- [x] 9.2 前端构建验证：`nvm use v22.22.0 && cd br-app && npm run build`
- [x] 9.3 验证现有自习室预约功能不受影响（自习室详情页行为与修改前完全一致）
