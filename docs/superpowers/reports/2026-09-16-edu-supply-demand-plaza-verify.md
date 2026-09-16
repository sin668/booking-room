# 验证报告：edu-supply-demand-plaza

- 日期：2026-09-16
- Change：edu-supply-demand-plaza（Comet tweak 预设）
- 验证模式：full（存在 4 个 delta spec capability，按 comet-verify 分流规则显式设置 verify_mode=full）
- 审查范围输入：本次改动 diff（br-server / br-app / br-admin 三端）、tasks.md、proposal.md、design.md、4 份 delta spec、验证命令输出
- review_mode：off（按 build 阶段既定策略跳过自动 code review；构建/测试/安全检查不跳过）

## 摘要记分卡

| 维度 | 结果 |
| --- | --- |
| 完整性（Completeness） | tasks.md 全部 build 交付项勾选 `[x]`；4 个 capability（edu-listing-api / edu-listing-admin-api / edu-listing-ui / edu-listing-admin-ui）均有实现 |
| 正确性（Correctness） | delta spec 全部 Requirement / Scenario 有实现证据；后端 31 测试通过；br-admin、br-app 构建通过 |
| 一致性（Coherence） | 实现与 design.md 决策一致；无 delta spec 与 design 漂移 |

## 完整性

1. tasks.md 第 1–4 节及 5.1–5.3 全部 `[x]`；5.4/5.5（归档与提交）为 comet verify→archive 阶段职责，已转为非勾选说明项，不作为 build 交付。
2. `comet classic openspec -- validate edu-supply-demand-plaza` 输出：`Change 'edu-supply-demand-plaza' is valid`。
3. 改动文件与 tasks.md / proposal.md Impact 一致，全部落在任务描述范围内：
   - br-server 新增 `app/domain/edu_listing_status.py`、`app/models/edu_listing.py`、`app/schemas/{edu_listing,admin_edu_listing}.py`、`app/services/{edu_listing_service,admin_edu_listing_service}.py`、`app/api/routes/{edu_listing,admin_edu_listing}.py`、alembic 迁移 `d7f3a9c1e5b2`、3 个测试文件；改 `models/__init__.py`、`alembic/env.py`、`main.py`、`seed_admin.py`、`seed_data.py`、`admin_menu_service.py`、`admin_certification.py`。
   - br-app 新增 `pages/edu-market/{index,publish,detail}.vue`、`api/eduMarket.js`、`static/tab/edu{,-active}.png`；改 `pages.json`（tabBar 第 4 项替换订单）+ 5 处指向订单的导航调用。
   - br-admin 新增 `api/eduMarket/index.ts`、`views/edu-market/list/{index.vue,EduListingAuditModal.vue}`、`views/training/certification-audit/CertificationReviewModal.vue`；改 `api/certification.ts`、`views/business/shared/options.ts`、重构 `views/training/certification-audit/index.vue`。
   - 说明：工作区另有 `.graphify/*`、`br-app/logo.png`、`br-admin/pnpm-lock.yaml` 改动，均为本 change 之外的既有噪声（会话起始快照已存在），不属于本次交付。

## 正确性

### Requirement 实现映射

| Requirement | 证据 |
| --- | --- |
| edu-listing-api / 数据模型 | `app/models/edu_listing.py` 独立 `edu_listings` 表，无 teachers/courses/study_rooms 外键；listing_type CheckConstraint；status 默认 pending；图片 JSON ≤3（schema 校验）|
| edu-listing-api / 综合广场列表 | `edu_listing_service.list_edu_listings` 仅 `status==approved`、教学混排、支持 listing_type/subject/city/sort 筛选；route 用 `get_optional_current_user_id` 允许游客；响应 `{items,total,page,page_size}` |
| edu-listing-api / 详情 | `get_detail` 浏览数 +1（flush）、404、附带发布者认证状态（with_certification=True）|
| edu-listing-api / 发布认证前置 | `_ensure_certified` 按 REQUIRED_CERTIFICATION（tutor→education、training→teacher、demand→real_name）校验 `status.in_(['approved','verified'])`，不通过抛 400；未登录由 `get_current_user_id` 返回 401 |
| edu-listing-api / 我发布的 | `list_mine` 全状态、创建时间倒序分页 |
| edu-listing-admin-api / 审核列表 | `admin_edu_listing_service.list_edu_listings` 支持 keyword(标题 ilike)/type/status 筛选分页，每条携带发布者昵称 + 认证摘要（with_certification=True）；route `require_admin_permission("edu:listing:view")` |
| edu-listing-admin-api / 通过·拒绝·下架 | `update_status` 幂等流转 approved/rejected/offline，拒绝必填理由（422），reviewed_at=booking_now()、reviewed_by=admin_id；route `require_admin_permission("edu:listing:audit")` 后端强制权限 |
| edu-listing-ui / 单一瀑布流广场 | `pages/edu-market/index.vue` JS 双列累计高度拆分（不用 column-count）、onReachBottom 无限加载 + hasMore + listRequestId 防竞态、类型徽标/价格/发布者/认证标识 |
| edu-listing-ui / 发布与认证引导 | `publish.vue` 类型选择 + 表单 + ≤3 图上传（scope common）+ isCertApproved/missingCert 认证前置拦截与「去认证」引导 |
| edu-listing-ui / 详情页 | `detail.vue` hero + 信息 + 发布者卡片 + 描述/标签/可授课时间 + 浏览数 + 底部操作栏 |
| edu-listing-ui / tabBar 替换订单 | `pages.json` 第 4 项由 orders 改为 edu-market；confirm/course-booking 的 switchTab→redirectTo、profile/index 的入口→navigateTo、notifications isTabPage 更新；订单页保留为普通页面 |
| edu-listing-admin-ui / 供需审核页 | `views/edu-market/list/index.vue` BasicForm(关键词/类型/状态) + BasicTable(:request) + TableAction；列含 标题/类型/价格/地区/发布者/**认证状态**/审核状态/发布时间/操作；审核 Modal 通过/拒绝/下架，拒绝必填理由，v-permission `edu:listing:audit` |
| edu-listing-admin-ui / 认证审核页对齐 | `certification-audit/index.vue` 重构为 lang=ts + BasicForm(status_filter/type_filter/keyword) + BasicTable(:request)；`api/certification.ts` 接 normalizePageParams+toBasicTableResult；后端 `admin_certification.py` 新增 keyword（join User nickname/phone/school ilike）；审核行为抽到 CertificationReviewModal.vue 保持不变 |

### Scenario 覆盖

- 后端 API/admin-api 全部 Scenario 由 `tests/test_edu_listing_service.py`、`test_api_edu_listing.py`、`test_api_admin_edu_listing.py` 覆盖：31 passed（认证前置、教学混排、仅 approved 可见、浏览数自增、404、审核状态流转、拒绝必填理由、reviewed_at naive、无权限 403）。
- UI Scenario：构建通过 + 代码路径审查（瀑布流混排/触底加载/无更多文案/类型筛选重置、发布认证拦截与引导、详情浏览数、tabBar 入口与订单页 navigateTo 可达、admin 标准搜索区筛选/行内通过/拒绝需理由/菜单权限、认证 keyword 生效/标准控件渲染/审核不回归）。
- 交互式 UI 点击验证未在本文环境执行，需在真实运行环境人工确认（见 tasks 5.3）。

### 构建与安全

- 后端测试：`python -m pytest tests/test_edu_listing_service.py tests/test_api_edu_listing.py tests/test_api_admin_edu_listing.py` → 31 passed（verify 阶段新鲜执行）。
- alembic 单一 head：`alembic heads` → `d7f3a9c1e5b2 (head)`（design.md 风险项已核验）。
- br-app 构建：`npm run build:mp-weixin`（br-app/，exit 0），证据经 `comet check run edu-supply-demand-plaza build --local -- npm run build:mp-weixin` 记录。
- br-admin 构建：`pnpm build`（br-admin/，exit 0，built in 8.65s，CertificationReviewModal / EduListingAuditModal chunk 均产出）。
- 安全检查：无硬编码密钥；SQL 全部 SQLAlchemy 参数化（keyword 用绑定 ilike pattern，无注入）；权限后端 `require_admin_permission` 强制 + 前端 v-permission 双重；Vue 文本转义无 XSS；无新增不安全操作。

## 一致性

- 实现遵循 design.md 全部决策：单表 + listing_type、状态机复用 review 模式（含 offline）、认证前置在 service 层、C 端列表游客可访问、分页契约统一、br-app JS 双列瀑布流 + 防竞态、tabBar 替换订单、br-admin BasicForm/BasicTable + 裸 n-modal 显式 emits、认证 keyword 后端模糊匹配、菜单四步注册。
- bug-fixed.md 陷阱核查：BUG-15/29（时间统一 booking_now()，测试断言 reviewed_at naive）、BUG-16/26（无 ORM relationship，批量 select 内存组装）、BUG-18（两个审核 Modal 均裸 n-modal + 显式 defineEmits）、BUG-19/24（菜单目录用基路径 /edu-market、叶子用 list；seed 已注册）、BUG-23（用到的 n-* 组件均在 plugins/naive.ts 注册）、BUG-25（alova ADMIN_NATIVE_META）、BUG-14（br-app onMounted 从 'vue'）、BUG-20（模板无裸 < >）。
- 无 Superpowers Design Doc（tweak 预设 build_mode=direct 跳过，plan=null），design.md 一致性检查通过，无 delta spec 与 design doc 漂移。

## 问题清单

- CRITICAL：无
- IMPORTANT：1 项，已修复 —— admin-ui delta spec Requirement「列表 MUST 展示…认证状态」初版遗漏认证状态列（徽标仅在审核 Modal）。verify-fail 回到 build，在 `edu-market/list/index.vue` 新增「认证状态」列（学历/教师资格 NTag，数据来自后端 with_certification=True），重跑 br-admin 构建 exit 0，重新验证通过。
- WARNING：无
- SUGGESTION：admin-ui Requirement 文字列出「通过/拒绝/下架/详情」四个行操作，实现采用与全站 reviews 页一致的单一「审核」入口打开 Modal（Modal 内含详情展示 + 通过/拒绝/下架），功能等价且符合用户「复用其他页面控件」的要求，未额外拆出独立「详情」按钮。

## 最终评估

第 1 轮发现 1 个 IMPORTANT 缺口（认证状态列缺失），已按 comet-verify Step 1b 自动回到 build 修复并重新验证。当前全部检查通过，无遗留 CRITICAL / IMPORTANT / WARNING 问题。验证结论：**PASS**，可进入归档前最终确认。
