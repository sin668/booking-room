## Context

现有 `study_rooms` 表仅服务于自习室座位预约系统。本变更需要扩展该表增加 `room_type` 字段以区分自习室、培训室和综合室，新建 `teachers` 表和 `courses` 表支撑培训课程列表展示。前端在 br-app 新增培训课程列表页面，参考 `prototype/training.html` 高保真原型图。参见 proposal.md 了解动机。

## Goals / Non-Goals

**Goals:**

- 数据库层：`study_rooms` 表增加 `room_type` 列（枚举，默认 study），新建 `teachers` 表和 `courses` 表（courses 通过 `teacher_id` 外键关联 teachers）
- 后端 API：现有自习室列表 API 支持 room_type 过滤；新建培训室列表和课程列表两个接口
- 前端页面：实现培训课程列表页面，包含分类 TAB 切换、培训室卡片（可展开热门课程）、课程卡片列表、搜索栏 UI
- 现有自习室预约功能不受影响

**Non-Goals:**

- 不实现培训室详情页和课程详情页（training-room.html、course-detail.html）
- 不实现 Admin 后台管理功能（br-admin）
- 不实现课程预约/下单/支付功能
- 不实现后端搜索 API（搜索栏仅前端 UI 展示）
- 不实现教师详情页或教师管理功能（仅创建 teachers 表供 courses 关联）

## Decisions

### 1. room_type 使用字符串枚举而非独立类型表

**选择**：在 `study_rooms` 表增加 `room_type` VARCHAR(20) 列，枚举值为 study / training / comprehensive，默认 study。

**理由**：三种类型是固定枚举，不会频繁增加新类型。使用字符串字段比独立类型表更简单，避免多表 JOIN 开销。现有数据迁移只需设置默认值 study。

**备选方案**：创建独立的 `room_types` 表，通过外键关联。被否决因为类型数量固定且少，独立表增加不必要的复杂度。

### 2. 创建独立 Teacher 表，courses 通过 teacher_id 外键关联

**选择**：创建 `teachers` 表（id, name, avatar, title, rating, created_at, updated_at），`courses` 表通过 `teacher_id` 外键关联 `teachers.id`，不再在 courses 表中存储教师姓名和头像。

**理由**：教师是独立实体，一位教师可讲授多门课程。独立表避免数据冗余（同一教师姓名/头像在多门课程中重复），支持后续教师详情页、教师管理等功能扩展。课程列表通过 JOIN 获取教师信息，性能开销可接受。

**备选方案**：在 courses 表中直接存储 teacher_name 和 teacher_avatar 字段。被否决因为数据冗余，且后续扩展教师功能时需要数据迁移。

### 3. 课程分类使用字符串枚举而非分类表

**选择**：`courses.category` 使用 VARCHAR(30) 枚举字段，值为 primaryschool / middleschool / postgraduate / civil_service / language / skills / professional。

**理由**：分类数量固定且少（7 个枚举值），使用枚举字段足够。本次前端 TAB 先放置 5 个：全部、小学辅导（primaryschool）、中学辅导（middleschool）、公考备考（civil_service）、技能提升（skills），剩余分类（postgraduate/language/professional）后续按需添加 TAB。

**备选方案**：创建 `course_categories` 表。被否决因为分类数量固定且少。

### 4. 培训室列表 API 独立路由前缀

**选择**：新建 `GET /api/v1/training/rooms` 和 `GET /api/v1/training/courses`，使用独立 `/training/` 前缀。

**理由**：培训相关接口是新的业务领域，独立前缀有利于后续扩展（培训室详情、课程详情、预约等）。与现有 `/api/v1/rooms` 区分清晰，避免在现有接口上叠加过多参数。

**备选方案**：在现有 `/api/v1/rooms` 接口增加参数区分培训室和自习室。被否决因为职责不清，且培训室需要附带热门课程数据，响应结构不同。

### 5. 热门课程通过子查询附带返回

**选择**：培训室列表接口中，每个培训室附带最多 3 条 `is_hot=true` 的课程（`hot_courses` 字段）。

**理由**：原型图"全部"TAB 中培训室卡片可展开显示热门课程，一次请求获取所有数据减少前端请求次数。使用子查询限制每间培训室最多 3 条，避免数据量过大。

**备选方案**：前端先请求培训室列表，再为每间培训室单独请求热门课程。被否决因为 N+1 请求问题，用户体验差。

### 6. 综合室在两个列表中都出现

**选择**：room_type 为 comprehensive 的综合室同时出现在自习室列表（`GET /api/v1/rooms`）和培训室列表（`GET /api/v1/training/rooms`）中。

**理由**：综合室可同时作为自习室和培训室使用，需要在两个列表中都可见。用户可以通过自习室列表预约座位，也可以通过培训室列表查看课程。

### 7. 前端页面使用 uni-app 页面组件

**选择**：在 `br-app/src/pages/training/` 目录新建 `index.vue` 页面，使用 Vue3 Composition API + `<script setup>` 语法。

**理由**：遵循 br-app 现有页面结构惯例（如 `pages/booking/detail.vue`、`pages/study-record/index.vue`）。uni-app 框架要求页面放在 `pages/` 目录下并在 `pages.json` 注册。

**注意**：根据 bug-fixed.md BUG-14，`onMounted` 等 Vue 3 生命周期钩子必须从 `vue` 包导入，不能从 `@dcloudio/uni-app` 导入。`onLoad`、`onShow` 等 uni-app 页面钩子从 `@dcloudio/uni-app` 导入。

## Risks / Trade-offs

- **[数据库迁移风险]** → study_rooms 表已有数据，增加 room_type 列需设置安全默认值。迁移脚本使用 `server_default='study'` 确保现有数据自动获得 study 类型。
- **[API 尾部斜杠问题]** → 根据 bug-fixed.md BUG-22，所有新路由定义不得使用尾部斜杠。使用 `@router.get("")` 而非 `@router.get("/")`。
- **[uni-app onMounted 导入问题]** → 根据 bug-fixed.md BUG-14，必须从 `vue` 包导入生命周期钩子。
- **[WXML 非法字符问题]** → 根据 bug-fixed.md BUG-20，避免在 Vue 模板中使用 `&lt;` 和 `&gt;` HTML 实体，使用 Unicode 字符替代。
- **[页面性能]** → 培训室列表附带热门课程可能导致单次响应数据量较大。通过限制每间培训室最多 3 条热门课程和分页控制。
- **[Course 表 tags 字段]** → 使用逗号分隔字符串存储标签，查询时由后端解析为数组。简单方案，但不支持按标签高效查询。当前范围不需要按标签搜索，后续可迁移为关联表。
- **[Teacher 表 JOIN 开销]** → 课程列表和热门课程都需要 JOIN teachers 表获取教师信息。通过索引 teacher_id 外键和分页控制，性能开销可接受。

## Migration Plan

1. **数据库迁移**：
   - 创建 Alembic 迁移文件：`study_rooms` 表增加 `room_type` 列（VARCHAR(20), server_default='study'）
   - 同一迁移文件中创建 `teachers` 表和 `courses` 表（courses 含 teacher_id 外键关联 teachers.id）
   - 执行 `alembic upgrade head`

2. **种子数据**：
   - 在 `seed_data.py` 中增加 3 间培训室（room_type=training）和 1 间综合室（room_type=comprehensive）
   - 增加约 5 位教师数据
   - 增加约 10 条课程数据，覆盖 primaryschool/middleschool/civil_service/skills 分类，部分设置 `is_hot=true`，部分关联教师

3. **后端代码部署**：
   - 部署模型、schema、service、route 变更
   - 注册新路由到 `main.py`
   - 运行测试验证

4. **前端代码部署**：
   - 创建培训页面和 API 模块
   - 注册页面路由到 `pages.json`
   - 构建验证

5. **回滚**：
   - `alembic downgrade -1` 回滚数据库迁移（删除 room_type 列、courses 表、teachers 表）
   - `git revert` 回滚代码变更

## UI Implementation Reference

页面实现参考 `prototype/training.html` 高保真原型图，保持以下设计要素一致：

- **配色**：primary #4F6EF7，背景 #F5F6FA，卡片白色 rounded-2xl shadow-sm
- **导航**：顶部 NAV BAR "培训课程"，搜索栏，分类 TAB 栏（横向滚动）
- **培训室卡片**：封面图 + 信息区（名称、营业状态、评分、距离、地址、设施标签、热门推荐课程展开按钮）
- **课程卡片**：封面图 + 信息区（名称、状态标签、教师信息、所属培训室、评分、报名人数、价格、预约按钮）
- **底部导航**：5 个 TAB（首页、预约、培训、订单、我的），"培训"高亮
- **动画**：卡片入场 fadeInUp 动画，展开/收起 max-height 过渡

```
页面加载序列图：

Client (br-app)          Server (br-server)
    │                          │
    │── GET /api/v1/training/rooms ──▶│
    │                          │
    │                          │── 查询 room_type in
    │                          │   (training, comprehensive)
    │                          │   AND status=open
    │                          │── 子查询每间培训室的
    │                          │   hot_courses (is_hot=true, LIMIT 3)
    │                          │── JOIN teachers 获取教师信息
    │                          │
    │◀── 200 { items, total } ──│
    │                          │
    │ (用户切换分类TAB)          │
    │                          │
    │── GET /api/v1/training/courses?category=xxx ──▶│
    │                          │
    │                          │── 查询 courses
    │                          │   WHERE category=xxx
    │                          │   AND status=active
    │                          │── JOIN study_rooms 获取 room_name
    │                          │── JOIN teachers 获取教师信息
    │                          │
    │◀── 200 { items, total } ──│
    │                          │
```
