# 三项目重构工作总结

日期：2026-05-30

## 总览

本轮重构覆盖 `br-server`、`br-app`、`br-admin` 三个项目，目标是在不改变既有业务行为的前提下，把核心业务规则、页面编排、接口适配和展示配置从臃肿模块中拆出，形成更清晰、可测试、可复用的业务边界。

截至本文档生成时：

- `br-server` 重构分支 `codex/br-server-clean-architecture-refactor` 已确认合入 `main`，当前与 `main` 指向同一提交 `fa21099`。
- `br-app` 页面逻辑重构提交已确认存在于 `main` 历史中，包含格式化器、页面服务、关注门店服务和支付轮询服务等提交。
- `br-admin` 重构分支 `codex/br-admin-business-refactor` 已通过 merge commit `d2114a6` 合入 `main`。
- 合并后的总体验证按用户要求安排在文档提交和推送 GitHub 之后执行。

## 一、`br-server` Clean Architecture 重构

### 重构目标

`br-server` 的目标是把预约、钱包、支付、核销等核心业务规则从服务层中提取出来，逐步形成领域层、仓储层和应用用例层。重构原则是保持 FastAPI 路由、响应模型、数据库结构和对外 API 行为不变，以新增测试和既有测试保护行为。

### 主要结构调整

新增领域层：

- `br-server/app/domain/booking_rules.py`
- `br-server/app/domain/wallet_rules.py`
- `br-server/app/domain/payment_rules.py`
- `br-server/app/domain/verification_rules.py`

新增仓储层：

- `br-server/app/repositories/booking_repository.py`
- `br-server/app/repositories/wallet_repository.py`

新增应用层门面：

- `br-server/app/application/booking_use_cases.py`

新增或补充测试：

- `br-server/tests/test_booking_rules.py`
- `br-server/tests/test_wallet_rules.py`
- `br-server/tests/test_payment_rules.py`
- `br-server/tests/test_verification_rules.py`
- `br-server/tests/test_booking_repository.py`
- `br-server/tests/test_wallet_repository.py`
- `br-server/tests/test_booking_use_cases.py`

### 关键改动

预约规则提取：

- 将预约时长计算、预约是否开始、已支付预约是否可取消、预约是否应自动完成等逻辑提取到 `booking_rules.py`。
- `booking_service.py` 保持原有服务函数作为兼容入口，但内部委托给领域规则函数。
- 对预约冲突查询引入 `BookingRepository`，把 SQL 查询边界从服务编排中分离出来。

钱包规则提取：

- 将钱包流水标题、收入/支出方向、管理端钱包流水基础状态、完成时间推导提取到 `wallet_rules.py`。
- 将钱包流水写入封装到 `WalletRepository`，降低 `WalletService` 中直接构造模型和 flush 的重复度。

支付规则提取：

- 将金额转分、待支付交易状态、失败交易状态、支付查询延迟序列等规则提取到 `payment_rules.py`。
- `booking_payment_service.py` 继续承担服务编排和外部支付状态处理，底层判断逻辑改用领域规则函数。

核销 token 规则提取：

- 将紧凑核销 token 的创建、签名、解码、过期判断和异常类型提取到 `verification_rules.py`。
- `booking_verification_service.py` 保留服务层异常映射和兼容 payload，减少对路由层的影响。

应用用例门面：

- 新增 `BookingUseCases`，以兼容方式暴露既有预约服务函数，为后续逐步迁移路由调用入口留出边界。

### 收益

- 服务层从“业务规则 + 数据访问 + 编排”混合状态，转向更明确的分层。
- 纯领域规则可以脱离数据库和 FastAPI 独立测试。
- 仓储层让关键 SQL 读写边界更容易定位和替换。
- 用例门面为后续更完整的 Clean Architecture 迁移提供过渡点。

### 需要关注的后续事项

- 当前应用层仍是兼容门面，路由层尚未全面切换到用例对象。
- 仓储层只覆盖预约冲突和钱包流水写入两个高价值边界，后续可继续迁移更多数据库访问。
- 合并推送后需要重新运行后端全量测试，确认当前环境依赖安装后的测试结果。

## 二、`br-app` 页面逻辑重构

### 重构目标

`br-app` 的目标是减少移动端页面文件中的重复逻辑，让页面更聚焦于展示和事件编排，把格式化、关注门店、本地存储、支付轮询、预约与钱包 API 编排拆到独立模块。

### 主要结构调整

新增常量和格式化器：

- `br-app/src/constants/booking.js`
- `br-app/src/constants/wallet.js`
- `br-app/src/utils/formatters.js`

新增服务模块：

- `br-app/src/services/followedRooms.js`
- `br-app/src/services/paymentPolling.js`
- `br-app/src/services/bookingPageService.js`
- `br-app/src/services/walletPageService.js`

兼容层调整：

- `br-app/src/utils/followedRooms.js` 改为重新导出 `services/followedRooms.js`，避免一次性改动所有老引用。

测试入口：

- `br-app/scripts/test-refactored-page-logic.js`
- `br-app/package.json` 新增 `test:refactor`，并把它纳入 `test:scripts`。

### 关键改动

共享格式化器：

- 抽取金额、充值金额、短时间、日期、门店起价、预约状态、钱包状态、座位分区、预约时长等格式化函数。
- 页面中原本重复的 `formatMoney`、`formatTime`、状态文案映射等逻辑改为引用共享函数。

关注门店服务：

- 抽取关注门店本地存储 key、门店数据归一化、关注/取消关注、关注摘要生成。
- 首页、个人页、预约详情页改为使用 service 层 API。

支付轮询服务：

- 抽取通用 `pollPaymentStatus`，同时支持预约支付和钱包充值支付。
- 统一处理成功状态、失败终止状态、超时状态和错误对象。
- 预约确认页和充值页保留用户交互流程，底层轮询改为共享服务。

页面服务：

- `bookingPageService.js` 统一封装预约页相关 API 编排，包括创建预约、查询支付状态、获取房间、座位、优惠券和钱包余额。
- `walletPageService.js` 统一封装钱包余额、交易列表、充值订单、支付确认和兑换码相关 API。
- 预约确认页、预约详情页、订单页、钱包流水页、充值页改为引用 page service。

### 收益

- 页面文件中的重复格式化和 API 编排明显减少。
- 支付轮询逻辑在预约支付和充值支付之间复用，避免状态处理分叉。
- 关注门店逻辑形成单一来源，后续调整本地存储结构更可控。
- Node 脚本测试覆盖纯函数和 service smoke test，给页面逻辑重构提供轻量回归保护。

### 需要关注的后续事项

- `bookingPageService` 和 `walletPageService` 目前仍是页面服务层，并未引入复杂状态管理。
- 移动端构建依赖 uni-app 工具链，合并推送后需要重新运行 `npm run test:scripts` 和 `npm run build:h5`。

## 三、`br-admin` 业务层重构

### 重构目标

`br-admin` 的目标是只重构管理端业务 API、业务 view、业务 store，区分 Naive UI Admin 模板框架代码和业务页面代码。页面保留展示与事件编排，把 API contract、分页适配、表格列配置、搜索表单 schema、业务字典和选项缓存抽到共享模块。

### 主要结构调整

新增 API contract：

- `br-admin/src/api/contracts/admin.ts`

新增业务共享 view 模块：

- `br-admin/src/views/business/shared/options.ts`
- `br-admin/src/views/business/shared/formatters.ts`
- `br-admin/src/views/business/shared/tableBuilders.ts`
- `br-admin/src/views/business/shared/formSchemaBuilders.ts`

新增业务选项 store：

- `br-admin/src/store/modules/adminBusiness.ts`

新增页面 builders：

- `br-admin/src/views/booking/list/builders.ts`
- `br-admin/src/views/room/list/builders.ts`
- `br-admin/src/views/activity/list/builders.ts`
- `br-admin/src/views/wallet/transactions.builders.ts`

新增测试入口：

- `br-admin/scripts/test-admin-business-refactor.ts`
- `br-admin/package.json` 新增 `test:business-refactor` 和 `lint` 别名。

构建辅助恢复：

- 补充 `br-admin/build/**` 下最小 Vite 构建辅助文件，恢复 `vite.config.ts` 和 `src/utils/env.ts` 所依赖的本地构建入口。

### 关键改动

API contracts：

- 新增 `ADMIN_NATIVE_META`，统一 Alova native response meta。
- 新增 `compactQuery`、`normalizePageParams`，统一空值清理和 `pageSize` 到 `page_size` 的适配。
- 新增 `toBasicTableResult`，统一后端分页响应到 `BasicTable` 所需结构的转换。
- 业务 API 文件改用共享 contracts，减少重复分页适配和 meta 配置。

共享 options 与 formatters：

- 统一预约状态、自习室状态、活动状态、座位分区、钱包交易类型、钱包状态等选项与 tag 映射。
- 统一金额、日期、日期时间、支付方式和 tag 配置格式化。

表格列 builders：

- 新增 `createTextColumn`、`createMoneyColumn`、`createDateTimeColumn`、`createTagColumn`。
- 页面列定义中重复的金额渲染、状态 tag 渲染、时间渲染下沉到共享 builder。

表单 schema builders：

- 新增关键字、状态、房间选择、日期范围 schema builder。
- 新增 `normalizeDateRange`，统一日期范围到 `date_start`、`date_end` 的查询参数转换。

业务选项 store：

- `adminBusiness` store 负责加载和缓存房间下拉选项。
- 预约列表页使用 store 加载房间选项，并通过 builder 生成搜索 schema。

页面 builders：

- 预约列表、房间列表、活动列表、钱包交易页的搜索配置、统计卡片、表格列配置下沉到页面 builder。
- 页面保留加载、弹窗确认、导出、刷新、路由跳转等事件编排。
- `room/list/columns.ts` 和 `activity/list/columns.ts` 改为从 builder 生成列，兼容既有引用。

Lint 自动格式化说明：

- `pnpm lint` 使用 `eslint --fix`，在满足最终 lint 门禁时自动格式化了少量非业务文件，包括登录页和账号设置页。
- 这些变更为 Prettier 格式化，不包含业务逻辑调整。

### 收益

- 管理端业务 API 的分页和 BasicTable 适配从页面和接口实现中抽离。
- 列配置、状态 tag、金额/日期格式化和搜索 schema 可以通过脚本测试覆盖。
- 页面复杂度降低，后续新增业务列表页可以复用共享 builder 模式。
- `adminBusiness` store 让跨页面业务选项具备缓存边界，避免页面各自拉取。

### 需要关注的后续事项

- `pnpm lint` 自动修复范围较广，后续可以考虑把模板遗留 Prettier 问题单独整理，减少业务重构 PR 的噪音。
- 当前 builders 覆盖了核心业务列表页，后续可继续推广到更多业务页，但不建议扩大到模板示例页。
- 合并推送后需要重新执行 `pnpm test:business-refactor`、`pnpm build`、`pnpm lint`。

## 四、分支合并状态

### 已确认

- `codex/br-server-clean-architecture-refactor` 已合并到 `main`。
- `br-app` 页面逻辑重构提交已在 `main` 中。
- `codex/br-admin-business-refactor` 已合并到 `main`。

### 当前 `main` 相对远端状态

在本文档生成前，`main` 已领先 `origin/main`，待提交本文档后统一推送到 GitHub。

## 五、合并后待执行验证计划

按用户要求，本文档会先随全部重构提交一起推送到 GitHub，然后再执行总体验证。计划执行的验证命令如下：

### `br-server`

```powershell
cd br-server
python -m pytest
```

说明：本地最初缺少 `pytest`，已按 `pyproject.toml` 执行 `python -m pip install -e ".[dev]"` 安装后端 dev 依赖。推送后会重新运行全量测试。

### `br-app`

```powershell
cd br-app
npm run test:scripts
npm run build:h5
```

### `br-admin`

```powershell
cd br-admin
pnpm test:business-refactor
pnpm build
pnpm lint
```

## 六、风险与回滚建议

### 主要风险

- `br-server` 的领域规则虽然有独立测试，但仍需全量测试确认服务接入层没有遗漏边界。
- `br-app` 的 page service 抽取保持页面交互不变，但移动端实际平台行为仍建议在 H5 构建后进行关键路径手测。
- `br-admin` 的 `pnpm lint --fix` 带来了少量格式化噪音，Review 时应区分业务逻辑改动和格式化改动。

### 回滚建议

- 若后端规则出现行为偏差，优先回滚对应领域规则接入提交，而不是删除整个领域层。
- 若移动端页面出现回归，优先检查 page service 的参数透传和支付轮询状态映射。
- 若管理端列表页出现展示问题，优先检查对应页面 builder 的列 key、render 函数和 schema field 是否与原页面一致。

## 七、后续建议

- 为三个项目建立统一的“重构验证清单”，每次跨项目重构都记录测试命令、构建命令、警告和环境前置条件。
- `br-server` 下一阶段可以逐步把更多服务函数迁移到应用用例层。
- `br-app` 可以继续沉淀面向页面的 service，但避免把页面状态全部搬进 service，保持页面交互可读性。
- `br-admin` 可以继续把业务页配置 builder 化，但模板框架和示例页应保持稳定，避免业务重构污染基础框架。
