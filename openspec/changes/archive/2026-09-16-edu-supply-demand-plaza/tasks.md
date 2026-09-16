# Tasks

## 1. br-server 后端：教培供需能力

- [x] 1.1 新增 `app/domain/edu_listing_status.py`：`EduListingStatus(str, Enum)` = pending/approved/rejected/offline + `AUDIT_TARGET_STATUSES`（仿 `review_status.py`）
- [x] 1.2 新增 `app/models/edu_listing.py`：`EduListing`（int PK、user_id UUID FK→users、listing_type String(20)+CheckConstraint、title、subject、teaching_mode、price Numeric(10,2)、price_unit、area、description Text、images JSON、status String(20) index、reject_reason、view_count int default 0、available_times JSON、reviewed_by/reviewed_at、created_at/updated_at；`__table_args__` 加 (listing_type,status,created_at) 索引）；在 `app/models/__init__.py` 与 `alembic/env.py` 注册
- [x] 1.3 新增 `app/schemas/edu_listing.py`（C 端：EduListingCreate/Item/ListResponse/MineListResponse，图片≤3 校验、listing_type pattern）与 `app/schemas/admin_edu_listing.py`（AdminEduListingItem 继承 + 审核元数据、EduListingStatusUpdate 含 reject 必填理由校验、AdminEduListingListResponse）
- [x] 1.4 新增 `app/services/edu_listing_service.py`：list（仅 approved、混排、筛选排序分页、游客可访问）、get_detail（浏览数+1、组装发布者昵称/头像/认证状态）、create（按 listing_type 认证前置校验，复用 status.in_(['approved','verified'])）、list_mine（全状态）；不自行 commit，用 booking_now()
- [x] 1.5 新增 `app/services/admin_edu_listing_service.py`：admin_list（keyword/listing_type/status 筛选分页 + 发布者信息）、update_status（通过/拒绝/下架，幂等、拒绝必填理由、reviewed_at=booking_now()、reviewed_by=admin_id）
- [x] 1.6 新增 `app/api/routes/edu_listing.py`（prefix `/api/v1/edu-listings`：GET ""、GET /mine、GET /{id}、POST ""）与 `app/api/routes/admin_edu_listing.py`（prefix `/api/v1/admin/edu-listings`：GET ""、PATCH /{id}/status，`require_admin_permission`）；集合路径用 ""，无尾斜杠
- [x] 1.7 在 `app/main.py` import + `include_router` 注册两个新 router
- [x] 1.8 新增 alembic 迁移创建 `edu_listings`（`down_revision='195bfc67f12a'`，建表+索引+CheckConstraint+COMMENT ON），`alembic upgrade head` + `alembic heads` 核验单一 head
- [x] 1.9 `app/services/seed_data.py` 新增演示供需数据（家教/培训班/求教各若干，含 approved 与 pending），幂等 upsert
- [x] 1.10 后端测试：`tests/test_edu_listing_service.py`、`tests/test_api_edu_listing.py`、`tests/test_api_admin_edu_listing.py`（覆盖认证前置、混排、仅 approved 可见、浏览数自增、审核状态流转、拒绝必填理由、reviewed_at naive）

## 2. br-server 后端：认证 keyword + 菜单 seed

- [x] 2.1 `app/api/routes/admin_certification.py` 列表接口新增可选 `keyword` 参数（join User 后 nickname/phone/school ilike 模糊匹配），向后兼容
- [x] 2.2 `app/services/seed_admin.py` 新增「教培供需」目录 MenuSeed（基路径）+「信息审核」菜单 MenuSeed（叶子段，permission `edu:listing:view`，component `/edu-market/list/index`）+ BUTTON_SEEDS（`edu:listing:audit`，注意不复用菜单自身 view 权限码）
- [x] 2.3 `app/services/admin_menu_service.py` 的 `COMPONENT_WHITELIST` 加入 `/edu-market/list/index`
- [x] 2.4 运行 `python -m app.services.seed_admin` 与 `python -m app.services.seed_data`，核验菜单与演示数据

## 3. br-app：教培供需 C 端

- [x] 3.1 新增 `src/api/eduMarket.js`（getEduListings/getEduListingDetail/getMyEduListings/createEduListing，走 `@/utils/request`，`/api/v1/edu-listings`）
- [x] 3.2 新增 `src/pages/edu-market/index.vue`：单一综合广场，2 列瀑布流（JS 拆左右列，不用 column-count），`onReachBottom` 无限加载 + `hasMore` + `listRequestId` 防竞态，类型/科目/城市筛选 + 排序，卡片区分家教/培训班/求教徽标，scoped SCSS + uni.scss 变量 + fadeInUp delay 封顶；custom navigationStyle
- [x] 3.3 新增 `src/pages/edu-market/publish.vue`：类型选择 + 表单 + 多图上传（≤3，scope `common`，抄 review/submit.vue）+ 认证前置校验与引导（抄 certification/index.vue isApproved 逻辑），ensureLogin
- [x] 3.4 新增 `src/pages/edu-market/detail.vue`：详情页（hero 图 + 信息 + 发布者卡片 + 描述/标签/可授课时间 + 底部操作栏），抄 booking/detail.vue 的 nav-overlay + statusBarHeight 骨架
- [x] 3.5 `src/pages.json` 注册三个新页面；tabBar 第 4 项由 `pages/orders/index` 改为 `pages/edu-market/index`（text 教培供需），新增 `src/static/tab/edu.png` + `edu-active.png`
- [x] 3.6 全局 grep 指向 `/pages/orders/index` 的 `uni.switchTab`，改为 `uni.navigateTo`（订单页降级为普通页面）
- [x] 3.7 br-app H5 构建验证无报错（激活 node 环境后 `npm run build:h5` 或项目既定构建命令）

## 4. br-admin：供需审核页 + 认证审核页重构

- [x] 4.1 新增 `src/api/eduMarket/index.ts`（类型定义 + getAdminEduListings 用 normalizePageParams/toBasicTableResult + reviewEduListing PATCH，ADMIN_NATIVE_META）
- [x] 4.2 `src/views/business/shared/options.ts` 新增 `EDU_LISTING_TYPE_OPTIONS/TAGS`、`EDU_LISTING_STATUS_OPTIONS/TAGS`
- [x] 4.3 新增 `src/views/edu-market/list/index.vue` + `EduListingAuditModal.vue`：n-flex → BasicForm 搜索区(关键词/类型/状态) → BasicTable(:request, actionColumn 审核 via TableAction)；审核 Modal（裸 n-modal 显式 emits，通过/拒绝/下架，拒绝必填理由，v-permission edu:listing:audit）；抄 training/reviews/index.vue + ReviewAuditModal.vue，列构造复用 shared/tableBuilders
- [x] 4.4 `src/router/icons.ts` 注册教培供需菜单所需图标（AppstoreOutlined/SchoolOutline 已存在，核验无需新增）
- [x] 4.5 重构 `src/views/training/certification-audit/index.vue`：改 `lang="ts"`，用 BasicForm 搜索区(状态/类型/关键词) + BasicTable(:request) 替换手写筛选与裸 n-data-table，审核走 TableAction，移除假统计卡，审核逻辑抽到 `CertificationReviewModal.vue`（裸 n-modal 显式 emits，拒绝必填理由，v-permission training:certification:audit:action）
- [x] 4.6 `src/api/certification.ts`：`getCertifications` 接 normalizePageParams + toBasicTableResult，新增 keyword 参数类型；保留 `reviewCertification` 契约
- [x] 4.7 确认审核/重构页用到的 `n-*` 组件均已在 `src/plugins/naive.ts` 注册（NModal/NFlex/NAvatar/NTag/NDescriptions(Item)/NImage(Group)/NAlert/NDivider/NInput/NButton/NRadio(Group)/NCard 全部在册）
- [x] 4.8 br-admin 构建验证（激活 node 环境后 `pnpm build`），无类型/构建错误（CertificationReviewModal / EduListingAuditModal chunk 均产出，built in 9.10s）

## 5. 验证与提交

- [x] 5.1 运行后端测试套件（新增 edu_listing 测试 + 既有认证测试）全绿（31 passed）
- [x] 5.2 br-admin、br-app 构建通过（br-admin built in 9.10s；br-app H5 见 3.7）
- [x] 5.3 人工核验：本环境完成构建 + 自动化测试核验；交互式 UI 点击验证（广场无限加载/发布认证拦截/详情浏览数/admin 审核/认证 keyword/tabBar 入口）需在真实运行环境人工确认

> 归档与提交由 comet verify → archive 阶段负责（非 build 交付项，故不作为 build 阶段勾选项）：
> - verify_mode=full（存在 4 份 delta spec），走 comet-verify 完整校验
> - 归档后提交 GitHub main（commit message 遵循 `feat:` 中文风格；不创建分支/worktree）
