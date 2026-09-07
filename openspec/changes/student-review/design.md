> **升级判定记录**：本 change 命中 4 个质变信号（跨模块协调、新增 capability、DB schema 变更、新增 public API）与文件数 tripwire，已在 open→build 前暂停交由用户决策。用户选择**继续 tweak 轻量流程**，理由：本文档已决策完备（12 项技术决策含备选否决理由、风险缓解表、迁移计划、bug-fixed.md 逐条规避清单），tasks.md 已按依赖排序且每条可验证，升级 full 会重复产出 Design Doc 与 plan。

## Context

动机见 `proposal.md` - Why。以下是影响实现路径的现状约束：

- `courses.rating`、`teachers.rating` 是既有的 `Numeric(3, 1)` 列，全仓**没有任何聚合回写逻辑**，只有 `seed_data.py` 写入的静态值。`courses` / `teachers` **都没有** `review_count` 列，但 `br-app/src/pages/training/course-detail.vue` L193-197 已经在引用 `course.review_count`（当前恒为 `undefined`）。
- `Course` 模型**没有 `teacher_id`**，师生关联只存在于 `course_schedules.teacher_id`；但 `Booking` 表**同时有** `course_id` 与 `teacher_id`（后者注释明确写"对应 course_schedules.teacher_id"）。
- `br-app/src/pages/teacher/profile.vue` L154-178 与 `br-app/src/pages/training/course-detail.vue` L186-220 **已内置「学员评价」静态区块**，DOM 结构与 scss 类名（`.review-item` / `.review-header` / `.review-stars` / `.review-summary` / `.review-more-btn`）全部齐备，只是数据是硬编码假数据。
- br-app **零 UI 组件库**（`package.json` 只有 `@dcloudio/*` + `pinia` + `vue`），**不存在 `src/components/` 目录**，全站 UI 都是手写 `<view>` + scss + rpx。`openspec` 的 `project_context` 里写的"uView 2.0 / Vuex / TailwindCSS"与实际代码不符，以代码为准。
- br-admin 是 `permissionMode: 'BACK'`，左侧菜单完全来自 `admin_menus` 表；`plugins/naive.ts` 用 `create()` 手工按需注册 59 个组件，**没有** `unplugin-vue-components` 自动导入（`components.d.ts` 是陈旧残留）。已注册组件中**缺 `NRate` 与 `NImageGroup`**。
- C 端上传路由 `POST /api/v1/upload/image` 硬编码 `if scope != "avatar": raise 422`，且 `UPLOAD_SCOPES` 中无 `review`。
- 测试环境是 SQLite in-memory，`tests/conftest.py` 在建表前把所有 `ARRAY` 列类型统一替换成 `JSON`（SQLite 不支持 `ARRAY`）。PostgreSQL 专有的 `jsonb_array_elements_text` 之类的 JSON 展开函数在测试环境不可用。
- Alembic 当前唯一 head 是 `b4e7a1c9d3f6`。

## Goals / Non-Goals

**Goals:**

- 一张表、一个 C 端列表接口覆盖课程 / 老师 / 我的三个入口，避免三套并行实现。
- 评分从"种子数据编出来的"变成"审核通过后算出来的"，且聚合写入是并发安全的。
- 最大化复用既有资产：br-app 的既有静态评价区块与分页范式、br-admin 的 `api/contracts/admin.ts` 与 `views/business/shared/*` builders、naive-ui 已装组件、原生 `uni.previewImage` / `uni.chooseImage`。
- 把 `bug-fixed.md` 里 29 条已记录的坑逐条变成本次实现的显式约束。

**Non-Goals:**

- 不做多维度评分、追评、点赞、举报、标签云统计、评价时限（理由见 proposal「明确不做」）。
- 不为 br-app 引入任何 UI 组件库，不新建 `src/components/` 公用组件目录。
- 不为 br-admin 新建 `views/training/reviews/builders.ts` / `options.ts`——列定义与表单 schema 直接内联在 `index.vue` 中，复用 `views/business/shared/` 的既有 builders。
- 不改动 `courses.rating` / `teachers.rating` 的列类型，不改 `Booking` 表结构。

## Decisions

### D1：单表 + 冗余维度列，一个列表接口打三个入口

`reviews` 表同时存 `booking_id`（必填、唯一）、`course_id`（可空、索引）、`teacher_id`（可空、索引）。C 端只暴露一个 `GET /api/v1/reviews`，用 `course_id` / `teacher_id` / `mine` 三个 query 参数区分入口。

- **为什么冗余**：`Course` 没有 `teacher_id`，若不冗余，按老师过滤要 join `bookings`；按课程过滤也要 join。冗余后两个维度都是单表索引查询。写入时从 `Booking` 直接抄，不存在同步问题（订单的课程与老师不会变）。
- **备选（否决）**：不冗余、查询时 join `bookings`。省 2 列但每个查询多一次 join，且 `mine` + `course_id` 组合过滤时 SQL 明显更绕。
- **备选（否决）**：为课程评价与老师评价建两张表。会出现"一条评价算一次还是两次"的语义争议，且聚合回写要写两遍。

### D2：`rating` 用 `Integer`(1-5)，不用 `Numeric`

星级分布统计需要 `GROUP BY rating`。整数分组直接出 5 个桶；`Numeric(3,1)` 分组会出现 4.5 星这类桶，分布条没法画。回写 `courses.rating`（`Numeric(3,1)`）时用 `round(avg, 1)` 转换即可。

### D3：`reviews.user_id` 用 `uuid.UUID` + 外键，不抄 `bookings` 的 `String(36)`

仓库里 `user_id` 有两种惯例：老表（`bookings` / `coupons` / `wallet`）用 `String(36)`，新表（`room_follows` / `notifications` / `user_identity_verification`）用 `uuid.UUID` + `ForeignKey("users.id", ondelete="CASCADE")`。选新惯例，理由：

- `users.id` 本身是 UUID，用 `String(36)` 每次比较都要 `str(user_id)` 转换（`bookings` 现在就这么绕）。
- `get_current_user_id` 依赖返回的就是 `uuid.UUID`，直接可用。
- 照抄 `room_follows` 的写法，是仓库最新的、已被验证的模式。

与 `bookings.user_id` 的比较发生在"校验订单归属"处，那里只需 `booking.user_id != str(user_id)` 一次，成本可忽略。

### D4：聚合回写用「全量重算」而非「增量累加」，且只在审核状态变更时触发

```
async def refresh_rating_aggregates(db, *, course_id=None, teacher_id=None) -> None
```

一条 SQL 算出某课程下所有 `approved` 评价的 `AVG(rating)` 与 `COUNT(*)`，直接 `UPDATE courses SET rating=..., review_count=...`；老师同理。无评价时写 0，不跳过。

- **为什么全量重算**：增量累加（`rating = (rating * n + new) / (n + 1)`）在两个管理员并发审核同一课程的两条评价时会丢更新；全量重算是幂等的，最后一次写入必然正确，天然并发安全，且不需要行锁。
- **为什么只在审核时触发**：新评价默认 `pending`，不参与聚合，所以发表时不需要重算。调用点只有后台审核服务一处。
- **`review_count` 加列而不是读时子查询**：课程列表页一次返回 N 个课程，读时子查询是 N 次 `COUNT`；写时更新是一次 `UPDATE`。加 2 列换掉一个 N+1。

### D5：一单一评靠 DB `UNIQUE(booking_id)`，不写应用层判重

应用层"先查后插"在并发下有竞态，且要额外一次查询。唯一约束由数据库强制，服务层捕获 `IntegrityError` 转成 HTTP 400「该订单已评价」。发表页进入时用 `GET /api/v1/reviews?booking_id=x&mine=true` 预判一次，纯为 UX（提前展示已评状态），不是正确性依赖。

> 这也让"按订单查我的评价"复用列表接口，省掉一个专用端点。

### D6：状态词表独立成 `app/domain/review_status.py`

```python
class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
```

不放进 `booking_status.py`（那是预约域的词表，混进去会重演 BUG-28「状态词表同键双义」），也不放 `models/review.py`（schemas 与两个 service 都要 import，从 models 反向依赖不干净）。文件约 15 行，与 `booking_status.py` 同构。

### D7：匿名脱敏在 service 层完成，不在前端

`mine=true` 时不脱敏（本人看自己的评价），其余公开查询把昵称替换为"匿名用户"、头像置空。后台查询永不脱敏。放 service 层是因为脱敏规则与"可见性规则"是同一件事，拆到前端会出现 C 端与后台两套实现。

### D8：br-admin 复用既有公用件，不新建文件

- API 层：`api/review/index.ts` 用 `ADMIN_NATIVE_META` + `normalizePageParams` + `compactQuery` + `toBasicTableResult`，与 `api/teacher/` 等完全同构。
- 列表页：`views/training/reviews/index.vue` 照抄 `views/activity/list/index.vue` 骨架（`n-flex` > `n-card` > `BasicForm` + `n-card` > `BasicTable`），列定义用 `views/business/shared/tableBuilders.ts` 的 `createTextColumn` / `createDateTimeColumn` / `createTagColumn`，搜索表单用 `formSchemaBuilders.ts` 的 `createKeywordSchema` / `createStatusSchema`。
- 弹窗：`ReviewAuditModal.vue` 照抄 `views/training/teachers/TeacherScheduleModal.vue` 的裸 `n-modal preset="card"` + `props.show` + `watch(props.show)` 骨架，**不用** `basicModal` / `useModal`（业务页面 100% 不用它，且 `useModal` 的 `emit('register')` 正是 BUG-18 的来源）。
- 星级用 `NRate`（`readonly`），图片用 `NImage` + `NImageGroup`，二者都由已安装的 naive-ui 2.43.1 提供 → 只需在 `plugins/naive.ts` 的 import 块与 `create({ components: [...] })` **两处同时**补注册。

### D9：br-app 不引库，星级用文本字符，预览用原生 API

- 星级：`★`(U+2605) 实心 + `☆`(U+2606) 空心，`v-for` 按 `rating` 渲染。既有 `course-detail.vue` L209-213 已经是这个套路，只是没画空心星。不为此引入 uview / uni-ui。
- 图片预览：`uni.previewImage({ urls, current })`，替代原型的自写 lightbox（原型里那个 `<img src="">` 空 src 缺陷一并消失）。
- 选图：`uni.chooseImage({ count: 9 - 已选数, sizeType: ['compressed'] })`，照抄 `settings/index.vue` 的头像上传（含取消判定 `isChooseImageCancel`）。
- 分页：照抄 `orders/index.vue` 的 `<scroll-view refresher-enabled @scrolltolower>` 范式（Options API），`PAGE_SIZE = 20`。
- 开关：原生 `<switch>`；文本域：原生 `<textarea maxlength="500">` + 自己算字数。
- 标签池：前端常量数组（好评标签 / 差评标签两组，随星级正负切换），**不建表、不做管理端配置**。

### D10：既有静态评价区块「换数据不换皮」

`teacher/profile.vue` L154-178 与 `course-detail.vue` L186-220 的 DOM 与 scss 全部保留，只把 `data()` 里硬编码的 `reviews` 数组改为接口填充，并给「查看全部评价」/「查看全部」加 `@tap` 跳转。

注意 `teacher/profile.vue` 的 `<style lang="scss">` **没有 `scoped`**（L353），新增类名会全局生效 → 只复用既有类名，若必须新增则加 `review-` 前缀。新建的两个评价页统一加 `scoped`。

### D11：后台菜单图标沿用已注册的 `SchoolOutline`

`router/icons.ts` 的 `constantRouterIcon` 是**字符串查表**，查不到返回 `null` → 图标空白（BUG-19 问题 1）。`StarOutlined` 在 `@vicons/antd` 存在但未注册。两个选择：注册新图标（改 2 处）或沿用已注册的 `SchoolOutline`。选后者——菜单挂在「培训管理」下，与父目录同图标视觉上合理，且零风险。

菜单种子照抄 `MenuSeed("training.teachers", ...)` 那一行，`parent="training"`，`path="reviews"`（**相对路径**，父目录 `training` 存的是基路径 `/training`，生成器拼出 `/training/reviews`）。同时把 `/training/reviews/index` 加进 `admin_menu_service.py` 的 `COMPONENT_WHITELIST`（注意：`/training/teachers/index` 与 `/training/teachers/edit/index` 现在都**不在**白名单里，因为 seed 直接写库绕过了校验；该缺失会导致后续在菜单管理界面编辑这两个菜单时报 422，但属既有问题，且只补其一会形成半修，故留待独立 change。本次只补 `/training/reviews/index`。）

按钮权限 2 条：`:audit` / `:reply`（`view` 由菜单行自身持有，见下方修正）。**不做 `:delete`**——驳回已能下架违规内容。

> 实现期修正：原计划把审核拆成 `:approve` 与 `:reject` 两个权限码，但审核接口只有一个 `PATCH /{id}/status`（body 决定目标状态）。若该端点只校验 `:approve`，仅持有 `:reject` 的管理员将无法驳回，形成权限漏洞；若在端点内按 body 分流校验，则等于手写一套 `require_admin_permission`。通过/驳回本就是同一种「审核」能力，拆开属推测性粒度（YAGNI），故合并为单一 `:audit`，与 spec「MUST 由后端强制执行审核权限」的单数表述一致。将来确需区分时再拆码并分裂端点。

> 实现期修正二：原计划再加一条 `training:reviews:view` 按钮权限，实测会造成真实缺陷。`_get_or_create_menu` 按 `permission_code` 查找已有行，而 `_seed_menus` 已先创建了持有同码的菜单行；随后 `_seed_buttons` 会把该行 `type` 改为 `button` 并清空 `path`/`name`/`component`/`icon`，且 `parent_id` 指向它自己——侧边栏「评价审核」菜单会直接消失。`permissions_for` 本来就收集**所有** type 的 `permission_code`，菜单行已足以授予 `view`，按钮属冗余。既有惯例也印证了这一点：`training.courses` 菜单持有 `training:courses:view`，其 BUTTON_SEEDS 只有 create/update/delete/status/schedule。故只加 `:audit` 与 `:reply` 两条。

### D12：上传 scope 的三处最小改动

1. `UPLOAD_SCOPES` 加 `"review"`
2. `SCOPE_SIZE_LIMITS` 加 `"review": 5 * MB`
3. `app/api/routes/upload.py` 的 `if scope != "avatar"` 改为 `if scope not in ("avatar", "review")`

`generate_object_key` 会自动产出 `images/review/YYYY/MM/DD/{uuid}.{ext}`，无需改动。

## Risks / Trade-offs

| 风险 | 缓解 |
|---|---|
| **JSON 列在 SQLite 测试环境的行为差异**（`images` / `tags`） | `conftest.py` 已把 `ARRAY` 统一替换成 `JSON`，但本次直接用 `JSON` 类型（照抄 `teachers.qualifications`），不经替换路径。测试中断言 `[]` 而非 `None`，schema 层用 `field_validator(mode="before")` 把 `None` 归一成 `[]`。 |
| **评分聚合覆盖 seed 数据** | 首次审核通过后 `courses.rating` 会从 seed 的 4.8 变成真实均值（可能只有 1 条评价 → 5.0 或 3.0）。这是预期行为（proposal 已声明）。回滚方案中已给出重跑 `seed_data` 的恢复路径。 |
| **新评价默认 `pending` → C 端列表初期为空** | 这是审核制的必然结果，spec 已明确要求空状态。上线后需要管理员先审一批。**不做自动通过**——用户明确要"评价审核"。 |
| **`course-detail.vue` 现有 `review_count` 引用** | 加列后自动修复；schema 未返回该字段前，前端展示为空白而非崩溃（Vue 模板对 `undefined` 容错）。 |
| **`teacher/profile.vue` 无 `scoped` 导致样式全局污染** | 只复用既有 `.review-*` 类名；新增类名一律加 `review-` 前缀。 |
| **br-app 无 lint / 无 type-check / 无单测** | 唯一可靠验证是 `npm run build:mp-weixin`（小程序编译器对模板最严格，BUG-20 的非法字符只在此暴露）。构建通过 ≠ 运行正确，需配合手动核对页面。 |
| **br-admin 无 type-check 门禁** | 验证靠 `pnpm lint` + `pnpm build` + 浏览器 console 查警告（BUG-12 的 `ReferenceError` 与 BUG-23 的未注册组件都只在 console 暴露）。 |
| **动态菜单需重新登录才生效** | 迁移与 seed 步骤中显式写明；否则管理员会以为功能没上线。 |
| **并发审核同一课程的多条评价** | D4 的全量重算天然幂等，无需行锁。 |

## Migration Plan

1. `cd br-server && alembic upgrade head` —— 建 `reviews` 表 + 给 `courses` / `teachers` 加 `review_count` 列（默认 0，非空）。
2. `cd br-server && python -m app.services.seed_admin` —— 幂等 upsert「评价审核」菜单与 4 条按钮权限。
3. 后台管理员**退出并重新登录**，刷新动态路由与权限缓存。
4. br-admin：`pnpm build`；br-app：`npm run build:mp-weixin`。
5. **回滚**：见 `proposal.md` - 回滚方案（`alembic downgrade -1` + 手工删除菜单行 + `git revert`）。

## bug-fixed.md 规避清单（本次实现的硬约束）

| BUG | 本次如何规避 |
|---|---|
| **BUG-12** `actions is not defined` | `views/training/reviews/index.vue` 的 `actionColumn.render` 中 `TableAction` 的 `actions` 一律写成 **inline 字面量数组**，绝不引用外部变量；无下拉操作时写 `actions: []`。 |
| **BUG-13** `page_size=100` → 422 | C 端列表接口 `page_size` 声明 `Query(20, ge=1, le=50)`；br-app `PAGE_SIZE = 20`；**不为了"一次拉全部评价"传大值**。老师简介 / 课程详情的前 3 条评价用 `page_size=3` 走列表接口，不新建专用端点。 |
| **BUG-14** `onMounted` 导入源 | 新建的两个评价页用 **Options API**（与 `orders/index.vue`、`teacher/profile.vue` 一致），`onLoad` / `onShow` 直接写成组件选项，**不 import**。若某处必须用 `<script setup>`，则 `onMounted`/`ref`/`computed` 从 `vue` 导入，`onLoad`/`onReachBottom` 从 `@dcloudio/uni-app` 导入，二者分行。 |
| **BUG-15 / BUG-29** naive/aware datetime 混用 | `reviewed_at` / `reply_at` 一律用 `app/utils/timezone.py` 的 `booking_now()` 写入（返回 naive 的 Asia/Shanghai）。**禁止** `datetime.now()` / `datetime.utcnow()` / `datetime.now(UTC)`。本次不做评价时限判定，进一步缩小时间比较的暴露面。 |
| **BUG-16 / BUG-26** `MissingGreenlet` | `Review` 模型**不写任何 `relationship()`**。列表返回的课程名 / 老师名 / 用户昵称头像用 `select(...).where(fk.in_(ids))` 批量查 + dict map 组装。所有接口 `response_model` 是纯 Pydantic schema，**绝不返回 ORM 对象**。service 内只 `await db.flush()` + `await db.refresh(obj)`，commit 交给 `get_db`。 |
| **BUG-17 / BUG-19 / BUG-24** 动态路由路径与图标 | 父目录 `training` 的 `path` 保持既有基路径 `/training`；新菜单 `path="reviews"`（相对）；`component="/training/reviews/index"`；图标用**已注册**的 `SchoolOutline`，不引入 `StarOutlined`。 |
| **BUG-18** 弹窗 `emit('register')` | `ReviewAuditModal.vue` 用裸 `n-modal` + `props.show` + `emit('update:show')` + `emit('success')`，`defineEmits` **只声明这两个**，不声明也不触发 `register`。 |
| **BUG-20** 模板 HTML 实体 | br-app 评价页模板中**禁止** `&lt;` `&gt;` `&amp;`。需要的符号用 Unicode：`★` `☆` `‹`(U+2039) `›`(U+203A) `✓`。 |
| **BUG-22** 路由尾部斜杠 | 后端一律 `@router.get("")` / `@router.post("")`，不写 `"/"`；br-app `api/review.js` 的 URL 不带尾斜杠（对齐 `teacher.js` / `training.js`，不学 `bookings.js` 的 `/bookings/`）。 |
| **BUG-23** Naive UI 组件未注册 | 用到的每个 naive 组件先对照 `plugins/naive.ts` 的 59 个已注册项；本次需**新增注册 `NRate` 与 `NImageGroup`**，且必须在 import 块与 `create({ components })` **两处同时**补齐。 |
| **BUG-25** Alova GET 缓存 | 全局 `cacheFor: null` 已生效，不需额外处理；**不使用 `force: true`**（Alova v3.3.4 中是静默 no-op）。审核成功后调 `actionRef.value?.reload()` 刷新表格。 |
| **BUG-27 / BUG-28** 状态死分支与词表双义 | 状态词表单一来源 `app/domain/review_status.py`（D6）；前端状态标签配置用 `views/business/shared/options.ts` 的 `getTagConfig` 机制，三个状态各一个分支，**不留兜底死分支**。 |

**额外自查（本次考古新发现，非 bug-fixed.md 条目）：**

- `BasicTable` 用 `ref="actionRef"` + `:request` prop，**没有 `useTable`**；`actionColumn.fixed` 必须写 `'right' as const`。
- `loadDataTable` 中必须做 `queryParams.page_size = queryParams.pageSize; delete queryParams.pageSize`（后台 componentSetting 的 apiSetting 契约是 `{page, pageSize}` 入参、`{list, pageCount, itemCount, page}` 出参）。
- br-app 的 `request.js` **不做统一错误 toast**，每个接口调用必须自己 `try/catch` + `uni.showToast({ icon: 'none' })`，错误信息取 `error?.detail || error?.message`。
- br-app `<image>` 必须写 `mode="aspectFill"`；事件用 `@tap` 而非 `@click`；跳非 tabBar 页用 `uni.navigateTo`。
- 自定义导航栏页面必须用 `uni.getSystemInfoSync().statusBarHeight` 撑高顶部；底部固定栏用 `padding-bottom: calc(... + env(safe-area-inset-bottom))` 且滚动内容底部加占位。
- `uni.scss` 全局变量自动注入，**不要手动 `@import`**；主色 `$primary: #4F6EF7`，与原型一致。
