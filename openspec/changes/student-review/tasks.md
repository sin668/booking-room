## 1. 后端数据层（br-server）

- [x] 1.1 新建 `app/domain/review_status.py`，定义 `ReviewStatus` 枚举（`pending` / `approved` / `rejected`），与 `booking_status.py` 同构，作为状态词表唯一事实源
- [x] 1.2 新建 `app/models/review.py`，定义 `Review` 模型：`booking_id`(FK bookings.id, UNIQUE, 非空)、`user_id`(uuid.UUID, FK users.id ondelete CASCADE, index)、`course_id`(FK courses.id, 可空, index)、`teacher_id`(FK teachers.id, 可空, index)、`rating`(Integer 1-5)、`content`(String 500)、`images`(JSON 可空)、`tags`(JSON 可空)、`is_anonymous`(Boolean 默认 False)、`status`(String 20 默认 pending, index)、`reject_reason`(String 200 可空)、`reply_content`(String 500 可空)、`reply_at`(DateTime 可空)、`reviewed_by`(UUID 可空)、`reviewed_at`(DateTime 可空)、`created_at`/`updated_at`；**不写任何 `relationship()`**
- [x] 1.3 给 `app/models/course.py` 与 `app/models/teacher.py` 各新增 `review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)`
- [x] 1.4 生成 Alembic 迁移 `alembic/versions/2026_09_07_*-<rev>_create_reviews_table.py`（`down_revision = "b4e7a1c9d3f6"`）：建 `reviews` 表与全部索引、加 `UNIQUE(booking_id)`、给 `courses`/`teachers` 加 `review_count`（server_default `"0"`，非空）；实现 `downgrade()` 完整回滚
- [x] 1.5 在 `app/models/__init__.py`（或既有模型汇总处）导出 `Review`，确保 `Base.metadata` 能建出该表；执行 `alembic upgrade head` 验证迁移可正向执行，再 `alembic downgrade -1` + `upgrade head` 验证可回滚

## 2. 后端 C 端 schema 与 service

- [x] 2.1 新建 `app/schemas/review.py`：`ReviewCreate`（`booking_id`、`rating` ge=1 le=5、`content` min_length=1 max_length=500、`images` 最多 9 项、`tags` 最多 5 项、`is_anonymous`）、`ReviewItem`（含昵称/头像/星级/内容/图片/标签/发表时间/课程名/老师名/机构回复；`images` 与 `tags` 用 `field_validator(mode="before")` 把 `None` 归一为 `[]`）、`ReviewPage`（`items`/`total`/`page`/`page_size`）、`ReviewSummary`（`average`/`count`/`positive_rate`/`distribution`）；全部 `model_config = ConfigDict(from_attributes=True)`
- [x] 2.2 新建 `app/services/review_service.py`，实现 `list_reviews`（按 `course_id`/`teacher_id`/`mine`/`booking_id`/评分档位/仅看有图/排序 过滤 + 分页；`mine=False` 时只取 `approved`）、`get_summary`（只统计 `approved`，`AVG`+`COUNT`+`GROUP BY rating`，无数据时返回全 0 而非 404）、`create_review`（校验订单存在/归属/`status == BookingStatus.COMPLETED.value`/未评价，从 `Booking` 抄 `course_id` 与 `teacher_id`，捕获 `IntegrityError` 转 400「该订单已评价」）
- [x] 2.3 在 `review_service` 中实现批量关联查询：用 `select(...).where(id.in_(ids))` 一次性取回课程名、老师名、用户昵称与头像，组装 dict map 后填充 `ReviewItem`（规避 BUG-16/26 的 `MissingGreenlet`）
- [x] 2.4 在 `review_service` 中实现匿名脱敏：非 `mine` 的公开查询把 `is_anonymous=True` 的记录昵称替换为「匿名用户」、头像置空
- [x] 2.5 新建 `app/api/routes/review.py`：`GET /api/v1/reviews`（`get_optional_current_user_id`；`page_size` 用 `Query(20, ge=1, le=50)`；`mine=true` 时无登录凭证返回 401）、`GET /api/v1/reviews/summary`（`course_id` 与 `teacher_id` 至少传一个，否则 422）、`POST /api/v1/reviews`（`get_current_user_id`）；路由路径**不带尾部斜杠**（BUG-22）
- [x] 2.6 在 `app/main.py` 按既有风格 import 并 `include_router(review_router)`（不传参，prefix 写在 router 上）

## 3. 后端审核 API 与评分聚合

- [x] 3.1 新建 `app/schemas/admin_review.py`：`AdminReviewItem`（含真实昵称头像 + 匿名标记 + 订单标识 + 审核状态 + 驳回理由 + 回复 + 审核人/审核时间）、`AdminReviewPage`、`ReviewStatusUpdate`（`status` 限定 approved/rejected、`reject_reason`）、`ReviewReplyUpdate`（`reply_content` max_length=500）
- [x] 3.2 在 `app/services/review_service.py` 中新增 `refresh_rating_aggregates(db, *, course_id=None, teacher_id=None)`：全量重算 `approved` 评价的 `AVG(rating)`（`round(..., 1)`）与 `COUNT(*)`，无评价时写 0；分别 `UPDATE courses` / `UPDATE teachers`；`course_id` 或 `teacher_id` 为 `None` 时跳过对应目标但不中断另一个
- [x] 3.3 新建 `app/services/admin_review_service.py`：`list_reviews`（按状态/评分档位/关键词模糊搜索内容或昵称 + 分页，永不脱敏）、`update_status`（驳回时强制要求非空理由、通过时清空理由、写入 `reviewed_by`/`reviewed_at`（用 `booking_now()`）、幂等、成功后调 `refresh_rating_aggregates`）、`update_reply`（空白内容视为清空回复并同步清空 `reply_at`，写入时间用 `booking_now()`）
- [x] 3.4 新建 `app/api/routes/admin_review.py`：`GET /api/v1/admin/reviews`（`require_admin_permission("training:reviews:view")`）、`PATCH /api/v1/admin/reviews/{review_id}/status`（`training:reviews:audit`）、`PATCH /api/v1/admin/reviews/{review_id}/reply`（`training:reviews:reply`）；路径不带尾斜杠；`response_model` 全部为纯 Pydantic；审核与回复端点把 `require_admin_permission(...)` 作为**参数**依赖以取得 `AdminContext`，从而写入 `reviewed_by`
- [x] 3.5 在 `app/main.py` import 并 `include_router(admin_review_router)`

## 4. 后端上传 scope 与后台菜单

- [ ] 4.1 `app/services/upload_service.py`：`UPLOAD_SCOPES` 加 `"review"`，`SCOPE_SIZE_LIMITS` 加 `"review": 5 * MB`
- [ ] 4.2 `app/api/routes/upload.py`：把 `if scope != "avatar"` 改为 `if scope not in ("avatar", "review")`
- [ ] 4.3 `app/services/seed_admin.py`：在 `MENU_SEEDS` 的培训管理段新增 `MenuSeed("training.reviews", "menu", "评价审核", "training:reviews:view", "reviews", "TrainingReviews", "/training/reviews/index", None, "SchoolOutline", 50, parent="training")`；在 `BUTTON_SEEDS` 新增 3 条：`("training.reviews", "training:reviews:view", "评价审核-查看")`、`("training.reviews", "training:reviews:audit", "评价审核-审核")`、`("training.reviews", "training:reviews:reply", "评价审核-回复")`（审核不拆 approve/reject 两码，理由见 design.md D11 的实现期修正）
- [ ] 4.4 `app/services/admin_menu_service.py`：`COMPONENT_WHITELIST` 补 `"/training/reviews/index"` 与 `"/training/teachers/index"`
- [ ] 4.5 执行 `cd br-server && python -m app.services.seed_admin` 两次，验证幂等（第二次不新增记录、不报权限码冲突）

## 5. 后端测试

- [x] 5.1 新建 `tests/test_api_review.py`：自定义 `auth_client` fixture（覆盖 `get_current_user_id` 返回固定 UUID，照抄 `tests/test_api_coupon.py:18-27`）；覆盖发表成功、订单未完成被拒、评价他人订单被拒、重复评价被拒（400）、rating 越界 422、content 过长/为空 422、图片超 9 张 422、未登录 401
- [x] 5.2 在 `tests/test_api_review.py` 中补充查询与可见性用例：按课程过滤、按老师过滤、按 `booking_id` 查询本人评价、公开列表只返回 `approved`、`mine=true` 返回本人全部状态且携带驳回理由、`mine=true` 不泄露他人评价、匿名脱敏（公开列表脱敏 / 本人查询不脱敏）、未登录可读公开列表、未登录查 `mine` 返回 401
- [x] 5.3 在 `tests/test_api_review.py` 中补充筛选/排序/分页/概览用例：好评档（4-5 星）、差评档（1-2 星）、仅看有图、按评分最高排序、`page_size=100` 返回 422、分页 total 一致性、概览均分与分布计算、概览排除未审核、无评价时概览返回全 0 且 HTTP 200、概览缺维度参数返回 422
- [x] 5.4 新建 `tests/test_api_admin_review.py`：覆盖后台列表按状态筛选、关键词搜索、匿名评价返回真实身份 + 匿名标记、通过（含 `reviewed_at.tzinfo is None` 断言，防 BUG-15/29 复发）、驳回缺理由 422、驳回带理由后 C 端公开列表不再出现但「我的评价」仍出现、重复通过幂等、不存在的评价 404、无权限 403、机构回复写入/覆盖/空白清空/超长 422
- [x] 5.5 在 `tests/test_api_admin_review.py` 中补充聚合回写用例：首次通过覆盖 seed 评分、只统计 `approved`、驳回唯一一条已通过评价后归 0、老师聚合独立于课程、`teacher_id` 为空的评价不导致聚合报错
- [ ] 5.6 补充上传 scope 用例（可并入既有上传测试文件）：`review` scope 上传成功且 `object_key` 前缀为 `images/review/`、`review` 超 5MB 返回 422、C 端入口以 `common` scope 上传返回 422、未登录以 `review` scope 上传返回 401
- [ ] 5.7 运行 `cd br-server && pytest tests/test_api_review.py tests/test_api_admin_review.py -q` 全绿；再运行 `pytest -q` 确认全量回归无破坏

## 6. br-app 小程序端

- [ ] 6.1 新建 `br-app/src/api/review.js`：`getReviewList(params)`、`getReviewSummary(params)`、`createReview(data)`，照抄 `api/training.js` 风格（具名导出 + `get`/`post`，URL 不带尾斜杠）
- [ ] 6.2 `br-app/src/pages.json` 注册 `pages/review/list`（`navigationBarTitleText: "学员评价"`）与 `pages/review/submit`（`navigationBarTitleText: "发表评价"`、`navigationStyle: "custom"`）
- [ ] 6.3 新建 `br-app/src/pages/review/list.vue`（Options API + `<style lang="scss" scoped>`）：`onLoad(options)` 读取 `course_id`/`teacher_id`/`mine`/`title`；概览区（大字均分 + 总数 + 好评率 + 5 档星级分布条）；筛选 chip（全部/好评/中评/差评 + 仅看有图）与排序切换（最新/评分最高）；`<scroll-view refresher-enabled @scrolltolower>` 分页（`PAGE_SIZE = 20`）；评价卡片（头像/昵称/`★`+`☆` 星级/时间/正文/图片网格/标签/机构回复气泡）；`uni.previewImage` 预览；`mine` 模式额外展示审核状态徽标与驳回理由；空状态与「没有更多了」；每个请求自带 `try/catch` + `uni.showToast({ icon: 'none' })`；参考 `prototype/review-list.html` 的视觉，剔除点赞/追评/标签云/积分
- [ ] 6.4 新建 `br-app/src/pages/review/submit.vue`（Options API + `scoped`）：自定义导航栏（`statusBarHeight` 撑高）；订单信息卡（课程/房间名 + 老师名 + 完成时间）；5 星可点击评分 + `RATING_META` 文案（照抄原型 JS 的文案表）；标签多选（好评/差评两组常量，随星级正负切换，最多 5 个）；`<textarea maxlength="500">` + 实时字数；图片上传九宫格（`uni.chooseImage` count = 9 - 已选、`uploadImage(path, 'review')`、上传中反馈、失败不入列、单张可删）；`<switch>` 匿名开关；底部固定提交栏（`env(safe-area-inset-bottom)` + 滚动内容底部占位）；提交前校验星级与内容、提交中禁用按钮、成功后 `uni.showToast` 提示「审核通过后展示」并 `navigateBack`；后端返回「该订单已评价」时展示该错误；**页面任何位置不出现积分/奖励文案**
- [ ] 6.5 改造 `br-app/src/pages/teacher/profile.vue`：把 L210-229 硬编码的 `reviews` 改为在 `loadData()` 中调 `getReviewList({ teacher_id, page: 1, page_size: 3 })` 填充；星级从写死 5 颗改为按 `review.rating` 渲染 `★`/`☆`；区块头部条数改用概览接口的 `count`；`.review-more-btn` 加 `@tap` 跳 `/pages/review/list?teacher_id=xxx&title=老师名`；无评价时展示空状态文案；接口失败走 `catch` 降级为空状态而非白屏；**保留既有 DOM 与 scss 类名**，新增类名一律加 `review-` 前缀（该文件 style 无 scoped）
- [ ] 6.6 改造 `br-app/src/pages/training/course-detail.vue`：把 L297-300 硬编码的 `reviews` 改为调 `getReviewList({ course_id, page: 1, page_size: 3 })`；`.review-summary` 的均分与条数改用 `getReviewSummary({ course_id })` 的真实数据（修复现有 `course.review_count` 恒为 undefined）；在 `.reviews-section` 头部加「查看全部 ›」跳 `/pages/review/list?course_id=xxx&title=课程名`；无评价时展示空状态
- [ ] 6.7 改造 `br-app/src/pages/profile/index.vue`：在「学习服务」分组内（「我的关注」之后）新增「我的评价」`.menu-item`，结构与相邻项一致（图标色块 + 文案 + 右侧箭头），图标用纯 CSS 绘制并加 `review-` 前缀类名；`@tap` 时先判 `userStore.isLoggedIn`，未登录则 `uni.showToast({ title: '请先登录', icon: 'none' })` + `uni.navigateTo('/pages/login/login')`，已登录则 `uni.navigateTo('/pages/review/list?mine=1')`
- [ ] 6.8 改造 `br-app/src/pages/orders/index.vue`：在 L231-237「再来一单」旁新增 `v-if="order.status === 'completed'"` 的「去评价」`.action-btn`，点击跳 `/pages/review/submit?booking_id=xxx`；已评价的订单不再展示可提交入口（依赖 6.4 的进入时预判 + 后端 400 兜底）；确认不破坏既有按钮布局与功能
- [ ] 6.9 运行 `cd br-app && npm run build:mp-weixin` 编译通过（无模板非法字符、无 scss 变量错误、无导入错误）；再运行 `npm run test:scripts` 确认既有校验脚本未破坏

## 7. br-admin 后台

- [ ] 7.1 `br-admin/src/plugins/naive.ts`：在 import 块与 `create({ components: [...] })` **两处同时**补注册 `NRate` 与 `NImageGroup`（BUG-23 防线）
- [ ] 7.2 新建 `br-admin/src/api/review/index.ts`：`AdminReviewItem` 类型 + `getAdminReviewList(params)` / `updateAdminReviewStatus(id, data)` / `updateAdminReviewReply(id, data)`；全部带 `ADMIN_NATIVE_META`，列表用 `normalizePageParams` + `compactQuery`，返回用 `toBasicTableResult`
- [ ] 7.3 新建 `br-admin/src/views/training/reviews/index.vue`：照抄 `views/activity/list/index.vue` 骨架（`n-flex vertical` > `n-card` > `BasicForm` + `n-card` > `BasicTable`）；搜索表单用 `createKeywordSchema` + `createStatusSchema`（三个状态选项）+ 评分档位 select；列用 `createTextColumn`（昵称/课程/老师）、`NRate` readonly（星级）、内容摘要 ellipsis、图片数量、`createDateTimeColumn`（发表时间）、`createTagColumn`（审核状态）、匿名 `NTag`；`actionColumn` 用 `fixed: 'right' as const` + `TableAction` 且 `actions` 写 **inline 字面量数组**（BUG-12 防线），按权限码 `v-permission` 控制审核与回复入口；`loadDataTable` 做 `page_size = pageSize` 转换并 `delete pageSize`；审核成功后 `actionRef.value?.reload()`
- [ ] 7.4 新建 `br-admin/src/views/training/reviews/ReviewAuditModal.vue`：裸 `n-modal preset="card"` + `props.show` + `watch(() => props.show)` 打开时填充（照抄 `TeacherScheduleModal.vue`）；`defineEmits` **只声明** `update:show` 与 `success`（BUG-18 防线）；展示真实昵称头像 + 匿名标记 + `NRate` + 全文 + `NImageGroup`/`NImage` 图片预览 + 标签 + 订单/课程/老师 + 发表时间 + 当前状态 + 既有驳回理由 + 既有回复；「通过」/「驳回」两个动作，驳回时理由必填（前端拦截 + 后端 422 兜底）；机构回复 `n-input type="textarea" maxlength="500" show-count`；成功后 `emit('success')` + 关闭；失败展示后端 `detail` 且不误标为已变更
- [ ] 7.5 运行 `cd br-admin && pnpm lint` 与 `pnpm build` 均通过；启动 dev 并以管理员账号**重新登录**，确认左侧「培训管理 > 评价审核」菜单出现、图标非空白、路由解析到列表页、表格渲染出数据行、浏览器 console 无 `ReferenceError` 与「未解析的组件」警告

## 8. 联调验证与提交

- [ ] 8.1 端到端手工验证 C 端三入口：课程详情 →「查看全部」→ 列表只显示该课程评价；老师简介 →「查看全部评价」→ 列表只显示该老师评价；「我的」→「我的评价」→ 只显示本人评价且含待审核/已驳回状态与驳回理由
- [ ] 8.2 端到端手工验证发表与审核闭环：已完成订单 →「去评价」→ 打分 + 标签 + 正文 + 传图 + 匿名 → 提交成功；后台审核页看到该条 `pending` → 通过 → C 端公开列表出现该条且课程/老师均分与条数被回写；再发一条 → 后台驳回并填理由 → C 端公开列表不出现但「我的评价」出现并展示理由；重复评价同一订单被后端 400 拦截
- [ ] 8.3 验证机构回复：后台填写回复 → C 端评价卡片展示回复气泡；提交空白回复 → 回复被清空
- [ ] 8.4 确认全链路无积分/AI 预审相关文案、字段与接口；确认无多维度评分、追评、点赞、举报、标签云
- [ ] 8.5 运行 `cd br-server && pytest -q` 全量测试通过；`cd br-admin && pnpm build` 通过；`cd br-app && npm run build:mp-weixin` 通过
- [ ] 8.6 清理调研期的临时产物（后台 HTTP 服务器进程、`.graphify` 缓存类未跟踪文件按 `.gitignore` 处理），确认 `git status` 中待提交内容均为本次改动
- [ ] 8.7 在 `main` 分支提交（**不创建分支、不创建 worktree**），commit message 形如 `tweak: 学员评价功能（三端）`，并推送到 GitHub 远端
