## 1. 后端 API

### 1.1 新增管理端钱包 Schema

**文件：** `br-server/app/schemas/wallet.py`（在文件末尾追加）

新增以下 Schema 类：

- `AdminWalletTransactionResponse`：管理端交易流水响应，包含 `user_id`、`user_nickname`、`user_phone`（用户端 `WalletTransactionResponse` 不含用户信息）
- `AdminWalletTransactionListResponse`：管理端分页列表响应，复用 `items`/`total`/`page`/`page_size`/`has_more` 结构
- `AdminWalletStatisticsResponse`：统计响应，字段包括 `total_recharge`、`total_consume`、`total_refund`、`net_income`、`active_users`、`total_transactions`

**参考模式：** 现有 `WalletTransactionResponse`（第 61-74 行）、`WalletTransactionListResponse`（第 76-81 行）

- [x] 实现

### 1.2 新增 `wallet_service` 管理端方法

**文件：** `br-server/app/services/wallet_service.py`（在 `WalletService` 类内追加方法）

新增两个方法：

**`admin_list_transactions(db, page, page_size, type, status, user_id, date_start, date_end)`**
- 参数：`db: AsyncSession`, `page: int`, `page_size: int`, 可选筛选参数 `type/status/user_id/date_start/date_end`
- 逻辑：构建 `WHERE` 条件链（复用现有 `list_transactions` 第 125-127 行的条件构建模式），JOIN `users` 表获取 `nickname`/`phone`
- 返回：`AdminWalletTransactionListResponse`
- 注意：方法为静态方法或类方法（与现有 `list_transactions` 实例方法不同，因为管理端方法不依赖 `self._redis`/`self._config`），建议参照 `booking_service.admin_list_bookings` 的模式

**`admin_get_statistics(db, date_start, date_end)`**
- 参数：`db: AsyncSession`, 可选 `date_start`/`date_end`
- 逻辑：使用 `func.sum` + `func.count` 聚合查询 `wallet_transactions` 表，按 `type` 分组统计充值/消费/退款金额，`func.count(distinct(user_id))` 统计活跃用户数
- 返回：`AdminWalletStatisticsResponse`

- [x] 实现

### 1.3 新增 `admin_wallet.py` 路由

**文件：** `br-server/app/api/routes/admin_wallet.py`（新建）

路由定义，参照 `admin_booking.py`（45 行）的模式：

```python
router = APIRouter(prefix="/api/v1/admin/wallet", tags=["admin-wallet"])
```

**端点：**

- `GET ""` → 交易流水列表（`/transactions`）
  - 参数：`page`, `page_size`, `type`, `status`, `user_id`, `date_start`, `date_end`
  - 权限：`wallet:view`
  - 返回：`AdminWalletTransactionListResponse`

- `GET "/statistics"` → 财务统计
  - 参数：可选 `date_start`, `date_end`
  - 权限：`wallet:view`
  - 返回：`AdminWalletStatisticsResponse`

- [x] 实现

### 1.4 新增 CSV 导出接口

**文件：** `br-server/app/api/routes/admin_wallet.py`（在 1.3 的路由文件中追加）

**端点：** `GET "/transactions/export"`

- 参数：同交易流水列表的筛选参数（`type`, `status`, `user_id`, `date_start`, `date_end`），不含分页参数
- 权限：`wallet:export`
- 逻辑：
  1. 先查询符合条件的总条数，超过 10000 条返回 400
  2. 使用 `csv.writer` + `io.StringIO` 生成 CSV 内容
  3. CSV 列：交易时间、用户ID、用户昵称、手机号、交易类型、金额、余额、状态、支付方式
  4. 通过 `StreamingResponse` 返回（`from starlette.responses import StreamingResponse`）
  5. 设置 `Content-Type: text/csv; charset=utf-8-sig`（BOM 头确保 Excel 中文兼容）
  6. 设置 `Content-Disposition: attachment; filename="wallet_transactions_{date}.csv"`
- 项目中无现有 CSV 导出实现，需新增 `import csv, io` 及 `StreamingResponse`

- [x] 实现

### 1.5 在路由注册文件中挂载 admin_wallet 路由

**文件：** `br-server/app/main.py`

- 第 31 行后新增导入：`from app.api.routes.admin_wallet import router as admin_wallet_router`
- 第 89 行后（`wallet_router` 附近）新增挂载：`app.include_router(admin_wallet_router)`

- [x] 实现

### 1.6 在 RBAC 权限配置中添加权限标识

**方式：** 通过管理后台「菜单权限」页面手动添加（数据库操作，非代码变更）

需要添加的权限标识：
- `wallet:view` — 查看钱包流水和统计
- `wallet:export` — 导出交易流水 CSV

**操作步骤：**
1. 以超级管理员登录 br-admin
2. 进入「系统设置 → 菜单权限」
3. 新增「钱包管理」菜单（父级），path: `/wallet`，icon: 选一个钱包相关图标
4. 新增「钱包流水」子菜单，path: `transactions`，permission_code: `wallet:view`
5. 将 `wallet:export` 权限分配给需要的角色（或在子菜单上额外配置）

> 注意：此步骤依赖前端路由页面（Task 2.2）完成后才有意义，可在最后统一操作。

- [x] 实现（手动 DB/admin UI 操作，已在 docs/api.md 记录为 RBAC 操作说明）

---

## 2. 管理端前端

### 2.1 新增钱包 API 模块

**文件：** `br-admin/src/api/wallet/index.ts`（新建目录 `src/api/wallet/` + `index.ts`）

参照 `src/api/system/user.ts` 的模式：

**TypeScript 类型定义：**
- `WalletTransactionItem`：交易流水项（id, user_id, user_nickname, user_phone, type, amount, balance_after, status, payment_method, created_at）
- `WalletStatistics`：统计响应（total_recharge, total_consume, total_refund, net_income, active_users, total_transactions）
- `WalletListParams`：查询参数（page, pageSize, type, status, user_id, date_start, date_end）

**API 函数：**
- `getWalletList(params)` → `GET /v1/admin/wallet/transactions`，适配 BasicTable 分页结构（参照 `getUserList` 第 155-172 行的 `nativeMeta` + 响应适配模式）
- `getWalletStatistics(params?)` → `GET /v1/admin/wallet/statistics`
- `exportWalletTransactions(params)` → `GET /v1/admin/wallet/transactions/export`，返回 blob 并触发浏览器下载（使用 `responseType: 'blob'` 或手动处理）

- [x] 实现

### 2.2 新增钱包管理路由和菜单配置

**文件：** `br-admin/src/router/modules/wallet.ts`（新建）

参照 `src/router/modules/booking.ts`（6 个路由文件）的模式：

```typescript
{
  path: '/wallet',
  name: 'Wallet',
  redirect: '/wallet/transactions',
  component: Layout,
  meta: { title: '钱包管理', icon: renderIcon(WalletOutlined), sort: 5 },
  children: [
    {
      path: 'transactions',
      name: 'wallet_transactions',
      meta: { title: '钱包流水' },
      component: () => import('@/views/wallet/transactions.vue'),
    },
  ],
}
```

**依赖：** 需安装图标 `@vicons/antd` 中的 `WalletOutlined`

- [x] 实现

### 2.3 实现交易流水列表页（含统计卡片 + 表格 + 筛选 + 导出）

**文件：** `br-admin/src/views/wallet/transactions.vue`（新建）

将 spec 中「财务统计概览」和「钱包流水列表」合并为单页面，统计卡片在顶部。

**页面结构：**

1. **统计卡片区域**（页面顶部）
   - 使用 `n-grid cols="1 s:2 m:4"` + `n-card` 实现 4 张卡片
   - 卡片：总充值（绿色）、总消费（橙色）、总退款（红色）、净收入（蓝色）
   - 每张卡片显示金额数值（`¥` 前缀，保留两位小数）和标签
   - 数据来源：`getWalletStatistics` 接口
   - 初始加载时请求一次，筛选时间范围变化时重新请求

2. **筛选区域**（参照 `src/views/system/user/index.vue` 第 7-32 行的模式）
   - 交易类型：`n-select`，选项：全部 / 充值 / 消费 / 退款
   - 状态：`n-select`，选项：全部 / 待处理 / 已完成 / 失败 / 已取消
   - 时间范围：`n-date-picker type="daterange"`，起止日期
   - 搜索按钮

3. **表格区域**（使用 `BasicTable`，参照 `src/views/system/user/index.vue` 第 33-58 行）
   - 列定义（`columns` 数组）：
     - 交易时间：`created_at`，格式化显示
     - 用户：`user_nickname` / `user_phone`（昵称为主，手机号为辅）
     - 交易类型：`type`，使用 `n-tag` 不同颜色区分（充值=success, 消费=warning, 退款=error）
     - 金额：`amount`，充值为绿色正数 `+¥xx`，消费/退款为红色 `-¥xx`
     - 余额：`balance_after`，`¥xx`
     - 状态：`status`，使用 `n-tag`
     - 支付方式：`payment_method`

4. **导出按钮**
   - 位于筛选区域右侧或表格上方
   - 使用 `v-permission="{ action: ['wallet:export'] }"` 控制显示
   - 点击后调用 `exportWalletTransactions`，传入当前筛选参数
   - 导出中显示 loading 状态

5. **筛选联动逻辑**
   - 时间范围变化 → 同时重新请求统计数据和列表数据
   - 其他筛选条件变化 → 仅重新请求列表数据
   - `loadDataTable` 函数将筛选参数合并到 BasicTable 的分页参数中

- [x] 实现

### 2.4 统计卡片与筛选条件联动

此任务已在 2.3 中一并实现（作为页面的一部分），标记为独立任务以便验证：

- [x] 验证：修改时间范围筛选后，统计卡片数值同步更新（代码层面：`handleDateRangeChange` 同时调用统计和表格刷新）

### 2.5 端到端验证

- [ ] 启动 br-server，确认 `/api/v1/admin/wallet/transactions` 和 `/api/v1/admin/wallet/statistics` 接口正常返回
- [ ] 启动 br-admin，使用gstack browser技能确认「钱包管理 → 钱包流水」菜单可见，页面正常加载
- [ ] 验证筛选功能：类型、状态、时间范围筛选正常工作
- [ ] 验证统计联动：修改时间范围后卡片数值更新
- [ ] 验证 CSV 导出：点击导出按钮可下载 CSV 文件
- [ ] 验证权限控制：无 `wallet:view` 权限的用户返回 403；无 `wallet:export` 权限时导出按钮不显示

### 3 集成与收尾

- [x] 3.1 API 文档更新（docs/api.md 补充新增的相关接口）
- [ ] 3.2 代码审查与重构（确保 Clean Architecture 分层、消除重复代码）
- [ ] 3.3 全量测试通过（单元测试 + 集成测试，覆盖率 > 80%）
