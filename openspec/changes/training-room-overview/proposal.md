## Why

当前自习室详情页（`pages/booking/detail.vue`）仅服务于自习室座位预约场景。随着 `training-course-list` change 引入 `room_type` 字段（study/training/comprehensive），系统已能区分三种房间类型，但详情页尚未根据类型展示差异化内容。培训室和综合室需要展示教室概况、名师团队和课程列表，且底部操作按钮需根据类型调整。参考 `prototype/training-room.html` 高保真原型图，在现有详情页基础上实现条件渲染。

## What Changes

- **修改门店详情页**：`pages/booking/detail.vue` 根据 `room_type` 条件渲染不同内容
  - 自习室（study）：保持现有行为不变
  - 培训室（training）：将"座位概况"替换为"教室概况"，新增"名师团队"横向滚动卡片和"本培训室课程"纵向列表，底部操作栏为心状关注按钮 + "返回课程"按钮
  - 综合室（comprehensive）：保留"座位概况"并在其下方新增"教室概况"、"名师团队"和"本培训室课程"列表，底部操作栏为心状关注按钮 + "预约自习室"按钮
- **新增培训室详情 API**：`GET /api/v1/training/rooms/{room_id}` 返回培训室详情（含教师列表和课程列表），路由定义不使用尾部斜杠（参考 bug-fixed.md BUG-22）
- **新增前端 API 模块**：`br-app/src/api/training.js` 增加 `getTrainingRoomDetail(roomId)` 函数
- **Vue3 生命周期钩子从 `vue` 包导入**（参考 bug-fixed.md BUG-14）
- **避免在模板中使用 `&lt;` 和 `&gt;` HTML 实体**（参考 bug-fixed.md BUG-20）

## Capabilities

### New Capabilities

- `training-room-detail-api`: 培训室详情 API — 按房间 ID 返回培训室基本信息、教师列表和课程列表的接口

### Modified Capabilities

- `study-room-booking-ui`: 门店详情页 requirement 修改为根据 `room_type` 条件渲染：自习室保持现有座位概况 + 立即预约；培训室显示教室概况 + 名师团队 + 课程列表 + 返回课程按钮；综合室显示座位概况 + 教室概况 + 名师团队 + 课程列表 + 预约自习室按钮

## Impact

**影响模块范围**：

- **br-server**（后端 API）:
  - `app/schemas/course.py` — TrainingRoomDetailResponse 新增（含 teachers 和 courses 嵌套对象）
  - `app/services/training_service.py` — 新增 `get_training_room_detail(room_id)` 方法
  - `app/api/routes/training.py` — 新增 `GET /api/v1/training/rooms/{room_id}` 路由
- **br-app**（微信小程序前端）:
  - `src/pages/booking/detail.vue` — 修改为根据 `room_type` 条件渲染
  - `src/api/training.js` — 新增 `getTrainingRoomDetail(roomId)` 函数
- **不涉及 br-admin**

**依赖**:
- 依赖 `training-course-list` change 的后端基础设施：`room_type` 字段、Teacher 模型、Course 模型、培训室/课程列表 API。两个 change 可并行开发，但本 change 的运行时验证需要 `training-course-list` 的数据库迁移已执行。

**回滚方案**:

1. 后端代码：`git revert` 恢复 `training.py` 路由和 service 变更，删除新增的 schema 字段
2. 前端代码：`git revert` 恢复 `detail.vue`，删除 `api/training.js` 中的 `getTrainingRoomDetail` 函数
3. 不涉及数据库迁移（依赖 `training-course-list` 的迁移，不单独创建迁移文件）
