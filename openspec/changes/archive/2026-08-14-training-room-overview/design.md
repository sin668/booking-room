## Context

当前自习室详情页 `pages/booking/detail.vue` 仅服务于自习室座位预约场景，固定展示座位概况统计和"立即预约"按钮。`training-course-list` change 已在 `study_rooms` 表增加 `room_type` 字段（study/training/comprehensive），并创建了 `teachers` 和 `courses` 表及培训室列表/课程列表 API。本 change 在此基础上扩展详情页，根据 `room_type` 条件渲染差异化内容。参见 proposal.md 了解动机。

## Goals / Non-Goals

**Goals:**

- 修改 `pages/booking/detail.vue` 根据 `room_type` 条件渲染：自习室保持不变，培训室显示教室概况+名师团队+课程列表，综合室显示座位概况+教室概况+名师团队+课程列表
- 新建 `GET /api/v1/training/rooms/{room_id}` API 返回培训室详情（含教师和课程数据）
- 前端根据 `room_type` 条件调用不同 API，避免不必要的请求
- 底部操作栏按钮根据 `room_type` 调整

**Non-Goals:**

- 不实现培训课程列表页面（`pages/training/index`，由 `training-course-list` change 负责）
- 不实现课程详情页或课程预约/下单/支付功能
- 不实现教师详情页
- 不涉及 br-admin 后台管理
- 不重复 `training-course-list` 已定义的后端模型和列表 API

## Decisions

### 1. 修改现有 detail.vue 而非创建新页面

**选择**：在现有 `pages/booking/detail.vue` 中根据 `room_type` 条件渲染，而非为培训室创建独立页面。

**理由**：用户明确要求"基于自习室详情页面来实现"，且自习室、培训室和综合室共享大量页面结构（封面图、名称、评分、地址、环境照片等）。条件渲染避免代码重复，一个页面处理三种类型更易维护。综合室同时需要座位和培训数据，单页面更易于组合展示。

**备选方案**：为培训室创建独立页面 `pages/training/room-detail.vue`。被否决因为大量页面结构重复，且综合室需要同时展示座位和培训内容，独立页面无法自然组合。

### 2. 新建培训室详情 API 而非扩展现有房间详情 API

**选择**：新建 `GET /api/v1/training/rooms/{room_id}` 返回培训室详情（含教师和课程），不修改现有 `GET /api/v1/rooms/{room_id}`。

**理由**：现有房间详情 API 服务于自习室预约流程，响应结构以座位为核心。培训室详情需要教师和课程数据，属于不同的业务领域。使用独立的 `/api/v1/training/` 前缀与 `training-course-list` change 的培训室列表 API 保持一致，职责清晰。前端根据 `room_type` 决定是否调用此 API，避免自习室请求不必要的培训数据。

**备选方案**：扩展现有 `GET /api/v1/rooms/{room_id}` 响应增加 `teachers` 和 `courses` 字段。被否决因为自习室请求会附带不必要的培训数据，且两种业务逻辑耦合在同一接口中。

### 3. 前端根据 room_type 条件调用 API

**选择**：前端先通过 `GET /api/v1/rooms/{room_id}` 获取房间基本信息（含 `room_type`），再根据 `room_type` 决定后续 API 调用：
- `study`：调用 `GET /api/v1/rooms/{room_id}/seats/stats` 获取座位统计
- `training`：调用 `GET /api/v1/training/rooms/{room_id}` 获取教师和课程
- `comprehensive`：同时调用座位统计和培训室详情两个 API

**理由**：按需请求减少不必要的网络流量和响应体积。综合室需要两种数据，使用 `Promise.all` 并行请求。

**备选方案**：一次性请求所有数据。被否决因为自习室不需要培训数据，培训室不需要座位数据。

### 4. 教室概况统计数据来源

**选择**：教室概况统计卡片（培训教室数、小班容量、认证讲师数、累计学员数）的数据由后端 `GET /api/v1/training/rooms/{room_id}` 响应提供，前端不硬编码。

**理由**：教室数量和讲师数需要根据数据库实时计算，硬编码会导致数据不准确。后端通过 COUNT 查询和 JOIN 聚合统计数据。

**备选方案**：前端根据已获取的 `teachers` 数组和 `courses` 数组在前端计算统计。被否决因为"培训教室数"和"累计学员数"等指标无法仅从教师和课程列表推导。

### 5. UI 实现参考原型图

**选择**：培训室和综合室的 UI 实现参考 `prototype/training-room.html` 高保真原型图，保持配色 #4F6EF7、背景 #F5F6FA、卡片白色 rounded-2xl shadow-sm 等设计要素一致。

**理由**：项目已有统一的设计规范和原型体系，参考原型图确保视觉一致性。现有 detail.vue 已使用 rpx 单位和 SCSS 变量，新增部分沿用相同样式体系。

## Risks / Trade-offs

- **[依赖风险]** → 本 change 依赖 `training-course-list` change 的数据库迁移（room_type 列、teachers 表、courses 表）。两个 change 可并行开发代码，但运行时验证需要 training-course-list 的迁移已执行。缓解：在 tasks.md 中明确标注依赖关系，验证步骤中先确认 training-course-list 迁移状态。
- **[API 尾部斜杠问题]** → 根据 bug-fixed.md BUG-22，所有新路由定义不得使用尾部斜杠。新路由使用 `@router.get("/{room_id}")` 而非 `@router.get("/{room_id}/")`。
- **[uni-app 生命周期钩子导入]** → 根据 bug-fixed.md BUG-14，`onMounted` 等 Vue 3 生命周期钩子必须从 `vue` 包导入，不能从 `@dcloudio/uni-app` 导入。`onLoad`、`onShow` 等 uni-app 页面钩子从 `@dcloudio/uni-app` 导入。
- **[WXML 非法字符]** → 根据 bug-fixed.md BUG-20，避免在 Vue 模板中使用 `&lt;` 和 `&gt;` HTML 实体，使用 Unicode 字符替代。
- **[页面性能]** → 综合室需要同时请求座位统计和培训室详情两个 API。使用 `Promise.all` 并行请求，页面 loading 状态在两个请求都完成后隐藏。
- **[条件渲染复杂度]** → detail.vue 将包含三种类型的条件渲染逻辑，模板和 script 复杂度增加。通过 computed 属性封装 room_type 判断逻辑，保持模板可读性。

## Migration Plan

1. **后端代码部署**：
   - 在 `training_service.py` 新增 `get_training_room_detail(room_id)` 方法
   - 在 `schemas/course.py` 新增 `TrainingRoomDetailResponse` schema
   - 在 `routes/training.py` 新增 `GET /{room_id}` 路由（不使用尾部斜杠）
   - 运行测试验证

2. **前端代码部署**：
   - 在 `api/training.js` 新增 `getTrainingRoomDetail(roomId)` 函数
   - 修改 `pages/booking/detail.vue` 添加条件渲染逻辑
   - 构建验证

3. **回滚**：
   - `git revert` 回滚后端路由、service 和 schema 变更
   - `git revert` 回滚前端 detail.vue 和 api/training.js 变更
   - 不涉及数据库迁移回滚

## UI Implementation Reference

页面实现参考 `prototype/training-room.html` 高保真原型图，保持以下设计要素一致：

- **配色**：primary #4F6EF7，背景 #F5F6FA，卡片白色 rounded-2xl shadow-sm
- **教室概况**：2x2 网格统计卡片（培训教室数、小班容量、认证讲师、累计学员），每张卡片含图标和数字
- **名师团队**：横向滚动卡片，每张含头像、姓名、头衔、评分
- **课程列表**：纵向列表，每条含封面图、课程名、状态标签、教师信息、排课时间、价格、预约按钮
- **底部操作栏**：心状关注按钮 + 类型对应的主操作按钮

```
页面加载序列图：

Client (br-app)               Server (br-server)
    |                              |
    |── GET /api/v1/rooms/{id} ───▶|
    |                              |
    |◀── 200 { room_type, ...} ────|
    |                              |
    | (room_type=study)            |
    |── GET /rooms/{id}/seats/stats▶|
    |◀── 200 { total, available,...│
    |                              |
    | (room_type=training)         |
    |── GET /training/rooms/{id} ─▶|
    |                              |
    |                              |── 查询 courses WHERE room_id=id
    |                              |   AND status=active
    |                              |── JOIN teachers 获取教师信息
    |                              |── 聚合统计（教室数、讲师数等）
    |                              |
    |◀── 200 { room, teachers,    │
    |           courses, stats } ─│
    |                              |
    | (room_type=comprehensive)    |
    |── GET /rooms/{id}/seats/stats│
    |── GET /training/rooms/{id} ─▶ (Promise.all 并行)
    |◀── 200 { seat stats }       │
    |◀── 200 { room, teachers,   │
    |           courses, stats } ─│
    |                              |
```
