## Why

平台需要新增一个独立的「教培供需」板块：老师/机构发布家教与培训班供给，学员发布求教需求，双方在同一个广场以瀑布流形式撮合。该板块与现有老师、课程、自习室等业务完全独立，不复用其数据模型。同时，现有 br-admin「认证审核」页面用手写卡片 + 裸 `n-data-table` 实现，与全站标准列表页（`BasicForm` 搜索区 + `BasicTable`）风格割裂、搜索关键词形同虚设、统计卡为假数据，需要一并对齐。

## What Changes

- 新增「教培供需」独立后端能力：新表 `edu_listings`（`listing_type` = `tutor` 家教 / `training` 培训班 / `demand` 求教；审核状态 `pending`/`approved`/`rejected`/`offline`），与 teachers/courses 无任何外键关联。
- 新增 C 端 API：综合广场分页列表（教+学混排，支持类型/科目/城市/排序筛选）、详情、发布（发布家教需学历认证、发布培训班需教师资格，复用现有 `user_identity_verifications` 的 `approved`/`verified` 等价判断）、我发布的列表。
- 新增 Admin API：供需信息审核列表（关键词/类型/状态筛选 + 分页）、通过/拒绝/下架。
- br-app 新增综合广场页（**单一广场**，2 列瀑布流，`onReachBottom` 无限加载，教与学需求混排）、发布页、详情页；底部 tabBar 用「教培供需」**替换「订单」Tab**（订单页降级为普通页面，修正指向订单的 `switchTab` 调用）。
- br-admin 新增「教培供需信息审核」页面，使用标准 `BasicForm` 搜索区 + `BasicTable` 列表 + `TableAction` 行操作。
- br-admin「认证审核」页面（`/training/certification-audit`）重构为与全站一致的标准搜索区 + `BasicTable`；后端 `GET /api/v1/admin/certifications` **新增 `keyword` 搜索参数**（按用户昵称/手机号/学校模糊匹配）。

## Capabilities

### New Capabilities
- `edu-listing-api`: 教培供需 C 端后端能力——`edu_listings` 数据模型、综合广场分页列表、详情、带认证前置校验的发布、我发布的列表。
- `edu-listing-admin-api`: 教培供需后台审核 API——审核列表（关键词/类型/状态筛选）、通过/拒绝/下架。
- `edu-listing-ui`: br-app 教培供需综合广场（瀑布流无限加载）、发布页、详情页与 tabBar 调整。
- `edu-listing-admin-ui`: br-admin 教培供需信息审核页面（标准搜索区 + 表格 + 行操作），以及认证审核页面对齐标准列表页控件。

### Modified Capabilities
<!-- 认证审核此前无对应 spec，本次关键词搜索与页面对齐作为实现层改动记录在 design/tasks，不构成 spec 级 delta。 -->

## Impact

- **br-server**: 新增 `app/models/edu_listing.py`、`app/domain/edu_listing_status.py`、`app/schemas/edu_listing.py` + `admin_edu_listing.py`、`app/services/edu_listing_service.py` + `admin_edu_listing_service.py`、`app/api/routes/edu_listing.py` + `admin_edu_listing.py`；改 `app/models/__init__.py`、`alembic/env.py`、`app/main.py`（注册 router）、`app/services/seed_data.py`（演示数据）、`app/services/seed_admin.py`（菜单/权限）、`app/services/admin_menu_service.py`（组件白名单）；新增一条 alembic 迁移（`down_revision = '195bfc67f12a'`）。改 `app/api/routes/admin_certification.py`（keyword 参数）。
- **br-admin**: 新增 `src/views/edu-market/list/index.vue` + builders、`src/api/eduMarket/index.ts`；重构 `src/views/training/certification-audit/index.vue`；改 `src/api/certification.ts`（keyword + `toBasicTableResult`）、`src/router/icons.ts`（新图标）。
- **br-app**: 新增 `src/pages/edu-market/{index,publish,detail}.vue`、`src/api/eduMarket.js`、`src/static/tab/edu*.png`；改 `src/pages.json`（页面注册 + tabBar 替换订单）、修正指向订单的 `switchTab`。
- **图片上传**: 复用现有 `common` scope（5MB），不新增 `UPLOAD_SCOPES`，零后端改动。
- **数据库**: 新增 `edu_listings` 表；不修改既有表结构（认证仅新增查询参数）。
- **回滚方案**: 后端 `alembic downgrade -1` 删除 `edu_listings` 表；重跑 `seed_admin` 前先移除新增 `MenuSeed`/`BUTTON_SEEDS` 条目（或手动删除对应 `admin_menus` 行）；前端还原 `pages.json`、tabBar 与 `switchTab` 调用、删除新增页面/API/视图文件；认证 keyword 为向后兼容的可选参数，移除即可。各端改动相互独立，可分模块回退。
