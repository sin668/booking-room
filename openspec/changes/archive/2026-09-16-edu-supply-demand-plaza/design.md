## Context

动机见 proposal.md - Why。当前状态与约束：

- br-server 分层为 `api/routes → services → models → schemas`，router 在 `app/main.py` 手工注册（无聚合文件），`redirect_slashes=False` + 中间件 strip 尾斜杠，集合路径用 `""`。新式 service 不自行 commit，靠 `get_db` 统一提交（参考 `review_service`）。审核状态机最佳模板是 `review` 模块（`app/domain/review_status.py` + `admin_review_service.update_status`）。
- 业务实体主键用 `Integer autoincrement`；图片 URL 列 `String(512)`，多图用 `JSON`（测试环境把 PG ARRAY 转 JSON，故禁用 ARRAY）；枚举用 `String(20)` + 可选 `CheckConstraint`，不用 PG ENUM。写库时间用 `app/utils/timezone.booking_now()`（naive Asia/Shanghai），禁用 `datetime.utcnow()`（BUG-15/29）。
- 认证：`user_identity_verifications` 单表三类型（real_name/education/teacher），`approved` 与 `verified` 等价（见 `certification.py:143-148`）。
- 当前 alembic head = `195bfc67f12a`。
- br-admin 标准列表页 = `n-flex vertical` → `BasicForm`(useForm schemas) card → `BasicTable`(`:request`, `actionColumn`, `TableAction`) card；API 走 alova + `ADMIN_NATIVE_META` + `normalizePageParams` + `toBasicTableResult`；共享 builders 在 `src/views/business/shared/`。动态菜单四步约定：view 文件 `index.vue` + `seed_admin.py` 的 `MenuSeed`/`BUTTON_SEEDS` + `admin_menu_service.COMPONENT_WHITELIST` + `router/icons.ts` 图标。`certification-audit/index.vue` 现为手写卡片 + 裸 `n-data-table`、无 TS、keyword 死搜索、统计卡假数据。
- br-app 无 Tailwind（纯 scoped SCSS + `uni.scss` 变量 + rpx），无 components 目录、无瀑布流组件。`onReachBottom` 需文档流（不可包在固定高 scroll-view）。tabBar 已满 5 个。`column-count` 在小程序不可靠 → 用 JS 拆左右两列。上传参数是 `scope`，`common` scope 已存在（5MB）。

## Goals / Non-Goals

**Goals:**
- 教培供需作为完全独立的新能力落地（后端表/API + br-app 单广场 + br-admin 审核页），最大化复用 `review` 审核模板、`study_room` CRUD 模板、br-admin `BasicTable` 模板、br-app `training/index.vue` 无限加载模板。
- 认证审核页对齐全站标准列表控件，keyword 搜索真实生效。

**Non-Goals:**
- 不做教/学两个独立广场（按用户要求合并为单一广场）。
- 不实现详情页的「立即联系/咨询」IM、关注/收藏的服务端持久化（仅前端入口占位，复用本地或后续迭代）；不做数据统计看板（admin 原型中的统计卡不在本次范围）。
- 不新增上传 scope（复用 `common`）。
- 不改动既有老师/课程/自习室逻辑。

## Decisions

- **单表 + 类型字段**：`edu_listings` 单表用 `listing_type`(tutor/training/demand) 区分教与学，而非分表。综合广场天然混排，筛选靠 `listing_type`。备选「教/学分表」被否决：查询需 union、复杂且无收益。
- **状态机复用 review 模式**：新增 `app/domain/edu_listing_status.py`，状态 `pending/approved/rejected/offline`（比 review 多 `offline` 下架）。审核 service 幂等、拒绝必填理由、时间用 `booking_now()`。
- **认证前置校验在 service 层**：发布时按 `listing_type` 查对应 `verification_type` 的 `status.in_(['approved','verified'])`，不通过抛 `ValueError`→route 转 400。复用 certification.py 既有查询写法，不新建认证模型。
- **C 端列表游客可访问**：用 `get_optional_current_user_id`（广场公开），`mine` 与发布用 `get_current_user_id`。
- **分页契约统一** `{items,total,page,page_size}`；C 端默认 10、上限 50；admin 默认 20、上限 100（沿用既有口径）。
- **br-app 瀑布流**：computed 按累计高度/索引奇偶拆 `leftColumn`/`rightColumn` 两个 flex 列渲染，不用 `column-count`；`onReachBottom`(文档流) + `hasMore` + `listRequestId` 防竞态（抄 notifications/training 模式）。入场动画 `delay-${index%4}` 封顶。
- **tabBar 替换订单**：`pages.json` tabBar 第 4 项由 `pages/orders/index` 改为 `pages/edu-market/index`（教培供需），新增 `static/tab/edu*.png`；全局排查指向 `/pages/orders/index` 的 `switchTab` 改为 `navigateTo`。
- **br-admin 审核页**：新建 `src/views/edu-market/list/index.vue` + `builders.ts`，抄 `training/reviews/index.vue` 骨架；行操作通过/拒绝/下架/详情，拒绝走审核 Modal（裸 `n-modal`，显式 emits，避免 BUG-18）。API `src/api/eduMarket/index.ts` 用 `normalizePageParams`+`toBasicTableResult`。
- **认证审核重构**：`certification-audit/index.vue` 改 `lang="ts"` + `BasicForm`/`BasicTable`；后端 `admin_certification.py` 列表接口新增可选 `keyword`（join User 后按 nickname/phone/school `ilike`）；前端 `getCertifications` 接 `normalizePageParams`+`toBasicTableResult`，保留 `reviewCertification` 契约不变。统计卡改为移除或用列表 total 派生（不造假数据）。
- **菜单注册**：新增「教培供需」目录 + 「信息审核」菜单（permission `edu:listing:view`，按钮 `edu:listing:audit`），组件 `/edu-market/list/index` 加入 `COMPONENT_WHITELIST`，图标在 `icons.ts` 注册（复用已存在的 antd 图标如 `AppstoreOutlined`，避免 BUG-19 缺图标）。

## Risks / Trade-offs

- [移除订单 Tab 破坏既有 `switchTab`] → 全局 grep `switchTab` 指向 orders 的调用并改 `navigateTo`；构建后人工核验订单页仍可达。
- [新模型漏注册导致 alembic autogenerate 检测不到] → 同步改 `app/models/__init__.py` 与 `alembic/env.py`；迁移后 `alembic heads` 确认单一 head。
- [async 序列化 MissingGreenlet（BUG-16/26）] → 列表 join 用批量 select 组装或 `lazy="selectin"`，不在 session 外触发懒加载；详情自增浏览数后 `flush` 再构建响应。
- [naive/aware 时间混用（BUG-15/29）] → 一律 `booking_now()`；测试断言 `reviewed_at.tzinfo is None`。
- [菜单 path 拼接错误（BUG-19/24）] → 目录用基路径、菜单用叶子段；seed 后核验路由生成。
- [小程序 `column-count` 失效] → 用 JS 双列方案，不用多列 CSS。
- [Naive UI 组件未全局注册（BUG-23）] → 审核页/重构页用到的 `n-*` 组件确认已在 `plugins/naive.ts` 注册。

## Migration Plan

1. 后端：加模型/domain/schema/service/route → 注册 `models/__init__.py`、`alembic/env.py`、`main.py` → `alembic revision --autogenerate -m "create_edu_listings_table"`（`down_revision='195bfc67f12a'`）核对 → `alembic upgrade head`。
2. seed：`seed_admin.py` 加菜单/按钮、`admin_menu_service.py` 加白名单 → `python -m app.services.seed_admin`；`seed_data.py` 加演示供需数据 → `python -m app.services.seed_data`。
3. 认证 keyword：改 `admin_certification.py` 列表接口（向后兼容可选参数）。
4. 前端：br-app 新页面 + tabBar + switchTab 修正；br-admin 新审核页 + 认证页重构 + icons。
5. 测试：`pytest tests/test_api_edu_listing.py tests/test_api_admin_edu_listing.py tests/test_edu_listing_service.py` + 既有认证测试；br-admin `pnpm build`；br-app H5 构建。
6. 回滚：`alembic downgrade -1`；移除 seed 菜单条目并重跑/手删 `admin_menus` 行；还原前端文件与 `pages.json`/tabBar/switchTab；认证 keyword 为可选参数，删除即回退。各端独立可分模块回退。
