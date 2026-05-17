## Why

用户完成充值后只能看到余额变化，无法在移动端查看资金变动明细，缺少对充值到账、优惠赠送和后续余额变化的可追溯入口。已有钱包充值能力已经创建 `wallet_transactions` 数据记录，现在需要补齐用户侧钱包流水前端和对应查询契约。

## What Changes

- 新增移动端钱包流水页面，用于展示当前余额、收入/支出统计和交易流水列表。
- 在个人中心或钱包入口补充“钱包流水/交易明细”导航，用户可从钱包相关区域进入流水页面。
- 新增前端钱包流水 API 封装，加载分页流水数据并支持类型筛选。
- 扩展现有钱包后端 API 规格，提供当前用户交易流水查询端点。
- 支持加载中、空状态、错误重试、分页加载完成等移动端列表状态。
- 不引入真实支付、提现、管理后台流水审核或流水导出能力。

## Capabilities

### New Capabilities

- `wallet-transactions-ui`: 用户侧钱包流水前端页面，覆盖入口导航、余额摘要、筛选、流水列表、分页、空状态和错误处理。

### Modified Capabilities

- `wallet-recharge-api`: 增加当前用户钱包流水查询 API，供移动端钱包流水页面读取 `wallet_transactions` 数据。

## Impact

- **影响模块范围**：`br-app` 移动端页面、移动端 API 封装、个人中心/钱包入口；`br-server` 钱包 API 查询端点、schema/service 文档与测试。
- **API 变更**：新增 `GET /api/v1/wallet/transactions`，按认证用户返回分页流水，支持类型筛选。
- **数据层影响**：复用现有 `wallet_transactions` 表，不新增迁移；如实现时发现缺少查询索引，仅允许补充非破坏性索引迁移。
- **依赖影响**：不新增第三方依赖，沿用 UniApp/Vue3、现有 request 工具和 FastAPI/SQLAlchemy 结构。
- **回滚方案**：移除新增流水页面路由、入口和前端 API 调用；移除后端流水查询路由/schema/service 方法及文档；若新增索引迁移，通过 Alembic downgrade 回滚索引。
