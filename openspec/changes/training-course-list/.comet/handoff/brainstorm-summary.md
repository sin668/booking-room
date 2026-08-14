# Brainstorm Summary

- Change: training-course-list
- Date: 2026-08-14

## 确认的技术方案

### 后端数据模型
- Teacher 模型：teachers 表（id, name, avatar, title, rating, created_at, updated_at）
- Course 模型：courses 表（room_id FK, teacher_id FK→teachers.id 可空, name, cover_image, category, price, rating, enrollment_count, schedule, tags, status, is_hot, sort_order, timestamps）
- StudyRoom 扩展：增加 room_type VARCHAR(20) 字段（study/training/comprehensive, default=study）
- 不使用 ORM relationship，service 层显式 JOIN（避免 BUG-16 MissingGreenlet）

### 数据库迁移
- 单个 Alembic 迁移文件：add_column room_type + create_table teachers + create_table courses
- 创建索引：courses.room_id, courses.teacher_id, courses.category
- server_default='study' 确保现有数据安全迁移

### API Schema
- TeacherResponse: id, name, avatar, title, rating
- HotCourseItem: id, name, cover_image, teacher: TeacherResponse|None, price, enrollment_count
- TrainingRoomResponse: StudyRoom 字段 + room_type + hot_courses: list[HotCourseItem]
- CourseResponse: id, name, cover_image, teacher, category, price, rating, enrollment_count, schedule, tags: list[str], status, room_id, room_name
- tags 在 Pydantic @field_validator 中从逗号分隔字符串解析为 list[str]

### Service 层
- list_training_rooms: 两步查询 + Python 组装（Step1 查培训室分页, Step2 批量查热门课程 JOIN teachers, Python groupby 分组每组取 3 条）
- list_courses: 单次查询 JOIN study_rooms + teachers

### 前端架构
- 单文件页面 pages/training/index.vue，内联模板不拆分组件
- Vue3 Composition API + script setup
- 原生 tabBar 插入第 5 个 tab（首页/预约/培训/订单/我的）
- 需准备 training.png 和 training-active.png 图标

### 测试策略
- test_training_api.py: 13 个测试用例覆盖培训室列表、课程列表、教师嵌套、tags 解析
- 更新 test_api_homepage.py: room_type 过滤和响应字段验证

## 关键取舍与风险

- 热门课程两步查询而非单次 LATERAL JOIN：牺牲 1 次额外 DB 查询换取代码简洁性
- 不使用 ORM relationship：避免 async session 下的懒加载问题
- tags 使用逗号分隔字符串 + Pydantic 解析：简单方案，不支持按标签高效查询
- Teacher 表 JOIN 开销：通过索引 teacher_id 外键控制
- TabBar 5 tab 正好达到 uni-app 原生 tabBar 上限

## 测试策略

- 后端：pytest tests/test_training_api.py + 更新现有测试
- 前端：npm run build 构建验证
- 运行环境：conda activate booking-room (Python 3.12.11), nvm use v22.22.0 (Node v22.22.0)

## Spec Patch

无。OpenSpec delta spec 验收场景已充分，无需回写。
