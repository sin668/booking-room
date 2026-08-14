## 1. 数据库迁移与模型

- [x] 1.1 创建 Alembic 迁移文件：`study_rooms` 表增加 `room_type` 列（VARCHAR(20), server_default='study', nullable=False），同一迁移中创建 `teachers` 表和 `courses` 表（courses 含 teacher_id 外键关联 teachers.id，参照 specs/training-course-list-api Teacher/Course database model）
- [x] 1.2 更新 `br-server/app/models/study_room.py`：增加 `room_type` 字段（Mapped[str], default="study"）
- [x] 1.3 创建 `br-server/app/models/teacher.py`：定义 Teacher 模型（name, avatar, title, rating, created_at, updated_at）
- [x] 1.4 创建 `br-server/app/models/course.py`：定义 Course 模型（room_id FK, teacher_id FK→teachers.id 可空, name, cover_image, category, price, rating, enrollment_count, schedule, tags, status, is_hot, sort_order, created_at, updated_at）
- [x] 1.5 在 `br-server/app/models/__init__.py` 注册 Teacher 和 Course 模型导出
- [x] 1.6 执行 `alembic upgrade head` 并验证迁移成功

## 2. 后端 Schema

- [x] 2.1 更新 `br-server/app/schemas/study_room.py`：StudyRoomResponse 增加 `room_type` 字段；RoomCreate/RoomUpdate 增加 `room_type` 可选字段
- [x] 2.2 创建 `br-server/app/schemas/teacher.py`：定义 TeacherResponse（id, name, avatar, title, rating）
- [x] 2.3 创建 `br-server/app/schemas/course.py`：定义 CourseResponse（含 teacher 嵌套对象、tags 数组解析）、CourseListResponse、TrainingRoomResponse（含 hot_courses，hot_courses 中每条含 teacher 嵌套对象）、TrainingRoomListResponse

## 3. 后端 Service

- [x] 3.1 更新 `br-server/app/services/study_room_service.py`：`list_study_rooms` 和 `admin_list_rooms` 支持 `room_type` 过滤参数
- [x] 3.2 创建 `br-server/app/services/training_service.py`：实现 `list_training_rooms`（查询 room_type in [training, comprehensive]，附带热门课程，JOIN teachers 获取教师信息）和 `list_courses`（按 category 过滤，JOIN study_rooms 获取 room_name，JOIN teachers 获取教师信息）
- [x] 3.3 更新 `br-server/app/services/seed_data.py`：增加 3 间培训室（room_type=training）和 1 间综合室（room_type=comprehensive），约 5 位教师数据，以及约 10 条课程数据覆盖 primaryschool/middleschool/civil_service/skills 分类

## 4. 后端 API Routes

- [x] 4.1 更新 `br-server/app/api/routes/study_room.py`：list_study_rooms 增加 `room_type` 查询参数（Query(None, pattern="^(study|training|comprehensive)$")）
- [x] 4.2 创建 `br-server/app/api/routes/training.py`：GET /api/v1/training/rooms（培训室列表）和 GET /api/v1/training/courses（课程列表），**注意：路由定义不得使用尾部斜杠（参考 bug-fixed.md BUG-22）**
- [x] 4.3 在 `br-server/app/main.py` 注册 training_router

## 5. 后端测试

- [x] 5.1 创建 `br-server/tests/test_training_api.py`：测试培训室列表（默认分页、城市过滤、综合室出现、自习室排除、热门课程附带含教师信息）、课程列表（分类过滤、分页、tags 解析、teacher 嵌套对象）
- [x] 5.2 更新 `br-server/tests/test_api_homepage.py` 或 `test_admin_room_routes.py`：增加 room_type 过滤和响应字段验证
- [x] 5.3 运行 `pytest tests/ -q` 确保全部测试通过

## 6. 前端 API 模块

- [x] 6.1 创建 `br-app/src/api/training.js`：封装 getTrainingRooms(params) 和 getTrainingCourses(params) 接口调用

## 7. 前端页面实现

- [ ] 7.1 创建 `br-app/src/pages/training/index.vue` 页面骨架（参考 prototype/training.html 高保真原型图，保持配色 #4F6EF7、背景 #F5F6FA、卡片 rounded-2xl shadow-sm）
- [ ] 7.2 实现搜索栏 UI（placeholder "搜索课程、老师"，纯展示不触发后端请求）
- [ ] 7.3 实现分类 TAB 栏（全部 + 小学辅导/中学辅导/公考备考/技能提升，横向滚动，选中高亮下划线。各 TAB 对应 category 值：小学辅导=primaryschool、中学辅导=middleschool、公考备考=civil_service、技能提升=skills）
- [ ] 7.4 实现"全部"TAB 培训室卡片列表（封面图、名称、营业状态、评分、地址、设施标签、可展开热门课程）
- [ ] 7.5 实现培训室卡片展开/收起热门课程（max-height 过渡动画，展开图标旋转）
- [ ] 7.6 实现分类 TAB 课程卡片列表（封面图、名称、状态标签、教师信息、所属培训室、评分、报名人数、价格、预约按钮）
- [ ] 7.7 实现加载状态和空状态提示（"暂无培训室"/"暂无课程"）
- [ ] 7.8 在 `br-app/src/pages.json` 注册培训页面路由（pages/training/index）
- [ ] 7.9 **注意：Vue3 生命周期钩子（onMounted 等）从 `vue` 包导入，不能从 `@dcloudio/uni-app` 导入（参考 bug-fixed.md BUG-14）**
- [ ] 7.10 **注意：避免在 Vue 模板中使用 `&lt;` 和 `&gt;` HTML 实体，使用 Unicode 字符（参考 bug-fixed.md BUG-20）**

## 8. 前端底部导航

- [ ] 8.1 在底部导航栏（tabBar 或自定义组件）增加"培训"入口，图标使用 graduation-cap，点击导航到 pages/training/index

## 9. 代码审查与重构

- [ ] 9.1 确保后端 Clean Architecture 分层：routes 仅处理 HTTP → services 处理业务逻辑 → models 定义数据 → schemas 定义响应
- [ ] 9.2 消除重复代码：room_type 枚举值和 category 枚举值提取为常量复用
- [ ] 9.3 确保前端组件分层：页面调用 api 模块，api 模块调用 utils/request.js
- [ ] 9.4 检查所有新路由无尾部斜杠，现有路由风格一致

## 10. API 文档更新

- [ ] 10.1 在 `docs/api.md` 补充 `GET /api/v1/training/rooms` 接口文档（路径、参数、响应示例）
- [ ] 10.2 在 `docs/api.md` 补充 `GET /api/v1/training/courses` 接口文档
- [ ] 10.3 更新 `docs/api.md` 中 `GET /api/v1/rooms` 接口文档，增加 `room_type` 查询参数和响应字段说明

## 11. 最终验证

- [ ] 11.1 运行后端全部测试：`conda activate booking-room && cd br-server && pytest tests/ -q`
- [ ] 11.2 前端构建验证：`nvm use v22.22.0 && cd br-app && npm run build`
- [ ] 11.3 验证现有自习室预约功能不受影响
