## Why

课程与老师的评分目前是 `seed_data.py` 写死的静态数字：`courses.rating`、`teachers.rating` 全仓没有任何聚合回写逻辑，`course-detail.vue` 已经在引用后端根本不返回的 `course.review_count`。br-app 的 `teacher/profile.vue` 与 `training/course-detail.vue` 各自内置了一块硬编码假数据的「学员评价」区块（Unsplash 假头像 + 写死文案），学员上完课后没有任何途径表达反馈，机构也没有任何审核入口。

原型 `prototype/review-submit.html`、`review-list.html`、`admin-reviews.html` 已经把三端交互定稿，本次把它落成真实功能，让评分从"编出来的"变成"算出来的"。

## What Changes

- **新增 `reviews` 表**：一条评价挂靠一个 `booking`（DB 层 `UNIQUE(booking_id)` 保证一单一评，不写应用层去重），冗余 `course_id` / `teacher_id` 以支撑两个维度的过滤查询；`images` / `tags` 用 JSON 列（照抄 `teachers.qualifications` 范式）。
- **新增评价状态词表** `app/domain/review_status.py`：`pending` / `approved` / `rejected`，作为唯一事实源（遵循 BUG-28 的教训）。
- **C 端 API**：`GET /api/v1/reviews`（一个接口 + query 参数同时覆盖课程维度、老师维度、"我的评价"三个入口）、`GET /api/v1/reviews/summary`（均分 / 总数 / 好评率 / 星级分布）、`POST /api/v1/reviews`（发表）。
- **后台审核 API**：`GET /api/v1/admin/reviews`、`PATCH .../{id}/status`（通过 / 驳回 + 驳回理由）、`PATCH .../{id}/reply`（机构回复）。
- **评分聚合回写**：审核状态变更时按 `approved` 评价重算并回写 `courses.rating` / `teachers.rating`；同时新增 `courses.review_count` / `teachers.review_count` 两列（写时更新，避免列表页 N 次 COUNT 子查询，并修复 `course-detail.vue` 已有的 undefined 引用）。
- **可见性规则**：C 端公开列表只返回 `approved`；`mine=true` 时返回本人全部状态的评价（含 `pending` / `rejected`，让用户看到审核状态与驳回理由）；后台返回全部并可按状态筛选。
- **br-app 新增 2 个页面**：`pages/review/list.vue`、`pages/review/submit.vue`。
- **br-app 改造 4 个既有页面**：`teacher/profile.vue` 与 `training/course-detail.vue` 的既有静态评价区块换成真实数据并加「查看全部评价」跳转；`profile/index.vue` 新增「我的评价」菜单项；`orders/index.vue` 为 `completed` 订单新增「去评价」按钮。
- **br-admin 新增评价审核页** `views/training/reviews/index.vue` + `ReviewAuditModal.vue`，并在 `plugins/naive.ts` 补注册 `NRate` / `NImageGroup`（BUG-23 防线）。
- **后台动态菜单**：`seed_admin.py` 新增 `training.reviews` 菜单 + 4 条按钮权限（view / approve / reject / reply），`admin_menu_service.py` 的 `COMPONENT_WHITELIST` 补 `/training/reviews/index`。
- **文件上传新增 `review` scope**（5MB 上限），C 端上传路由的 scope 白名单从硬编码 `!= "avatar"` 放宽为 `("avatar", "review")`。

### 明确不做（本次范围外）

- **AI 预审**、**积分 / 奖励**：用户明确要求暂不实现。
- **多维度评分**（教学质量 / 课程内容 / 老师态度 / 上课环境 / 性价比）：原型有此装饰性展示，但需要 5 个字段 + JSON 聚合（PostgreSQL 的 `jsonb` 展开在 SQLite 测试环境不可用）+ 5 套 UI 星条；单一综合 `rating` 已满足"星级打分和评价"的核心诉求。
- **追评**、**点赞 / 有用数与"最有用"排序**、**举报**、**后台删除评价**：均需额外表或自关联；"驳回"已能覆盖违规内容下架。
- **高频标签云统计**：需要对 JSON 数组做展开计数，SQLite 测试环境不兼容；标签仍可被选择并在评价卡片上展示，只是不做跨评价的聚合词云。
- **评价时限**（如"完成后 7 天内可评"）：原型与需求均未提出，且引入时限就要引入时区比较，会扩大 BUG-15 / BUG-29 的复发面。

## Capabilities

### New Capabilities

- `student-review-api`: 评价数据模型、状态词表、C 端评价查询 / 概览 / 发表接口、后台审核接口、评分聚合回写、评价可见性规则。
- `student-review-ui`: br-app 小程序端的评价列表页（课程 / 老师 / 我的三种过滤维度）、发表评价页，以及老师简介、课程详情、我的、订单四个入口。
- `student-review-admin-ui`: br-admin 评价审核列表页、审核弹窗（通过 / 驳回 / 机构回复）、动态菜单与按钮权限。

### Modified Capabilities

- `file-upload`: C 端上传接口的 scope 白名单新增 `review`，并为其定义 5MB 大小上限。

## Impact

**br-server**
- 新增：`app/domain/review_status.py`、`app/models/review.py`、`app/schemas/review.py`、`app/schemas/admin_review.py`、`app/services/review_service.py`、`app/services/admin_review_service.py`、`app/api/routes/review.py`、`app/api/routes/admin_review.py`、`alembic/versions/*_create_reviews_table.py`（`down_revision = b4e7a1c9d3f6`）、`tests/test_api_review.py`、`tests/test_api_admin_review.py`
- 修改：`app/main.py`（2 行 `include_router`）、`app/services/upload_service.py`（`UPLOAD_SCOPES` + `SCOPE_SIZE_LIMITS`）、`app/api/routes/upload.py`（scope 白名单）、`app/services/seed_admin.py`（菜单 + 按钮种子）、`app/services/admin_menu_service.py`（白名单）
- 迁移：新建 `reviews` 表；`courses` / `teachers` 各加 `review_count` 列

**br-app**
- 新增：`src/api/review.js`、`src/pages/review/list.vue`、`src/pages/review/submit.vue`
- 修改：`src/pages.json`、`src/pages/teacher/profile.vue`、`src/pages/training/course-detail.vue`、`src/pages/profile/index.vue`、`src/pages/orders/index.vue`

**br-admin**
- 新增：`src/api/review/index.ts`、`src/views/training/reviews/index.vue`、`src/views/training/reviews/ReviewAuditModal.vue`
- 修改：`src/plugins/naive.ts`

**依赖**：无新增第三方依赖。br-app 零 UI 组件库的现状保持不变（不为此引入 uview / uni-ui）；br-admin 复用已安装的 naive-ui 2.43.1；br-server 复用已安装的 SQLAlchemy / FastAPI / Pydantic。

**运维**：上线后需执行一次 `cd br-server && python -m app.services.seed_admin`（幂等 upsert）写入新菜单，管理员需重新登录才能看到「评价审核」入口。

## 回滚方案

1. **代码回滚**：本次改动收敛在单个 commit（或少数几个 `tweak:` commit），`git revert` 即可整体撤销。
2. **数据库回滚**：`cd br-server && alembic downgrade -1`，删除 `reviews` 表与 `courses.review_count` / `teachers.review_count` 两列。`courses.rating` / `teachers.rating` 是既有列，聚合回写会覆盖其原 seed 值；如需恢复原值，重跑 `python -m app.services.seed_data`。
3. **菜单回滚**：`seed_admin.py` 是按 `permission_code` upsert 的幂等脚本，revert 代码不会自动删除已写入的菜单行。需手工执行：
   ```sql
   DELETE FROM admin_menus WHERE key = 'training.reviews'
      OR parent_id = (SELECT id FROM admin_menus WHERE key = 'training.reviews');
   ```
   或直接在后台「系统设置 > 菜单管理」删除「评价审核」及其按钮。
4. **降级运行**：若只回滚前端，br-app 的老师简介 / 课程详情评价区块会因接口 404 而走 `catch` 分支显示空状态，页面不崩溃；br-admin 的菜单项会因组件缺失被 `generator.ts` 静默跳过（只 `console.warn`），不影响其它菜单。
5. **上传 scope 回滚**：`review` scope 是纯增量，移除后已上传的评价图片 URL 仍可访问（OSS 对象不随代码回滚删除）。
