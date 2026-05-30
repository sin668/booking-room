# br-admin 业务层重构实施计划

> **给 agentic workers 的要求：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 逐项执行本计划。执行进度使用 checkbox（`- [ ]`）跟踪。

**目标：** 只重构 `br-admin` 的业务 API/view/store 代码，区分模板框架代码与业务页面，减少业务页面内重复的接口契约、表格列配置和表单 schema 配置。

**架构：** 保持 Naive UI Admin 模板框架、通用组件、layout、示例页面不动；新增业务共享模块承载 API contracts、表格列 builder、表单 schema builder、业务字典/选项 store。页面继续负责展示和事件编排，业务 API 参数适配、BasicTable 分页适配、列配置和搜索表单配置下沉到可测试的纯函数。

**技术栈：** Vue 3、TypeScript、Naive UI、Pinia、Alova、现有 BasicTable/BasicForm、`esno` 脚本测试、`pnpm build`、`pnpm lint:eslint`。

---

## 范围边界

本轮只改业务代码：

- API：`br-admin/src/api/booking`、`br-admin/src/api/room`、`br-admin/src/api/seat`、`br-admin/src/api/wallet`、`br-admin/src/api/activity`、`br-admin/src/api/system/user.ts`
- View：`br-admin/src/views/booking/list`、`br-admin/src/views/room/list`、`br-admin/src/views/room/seats`、`br-admin/src/views/activity/list`、`br-admin/src/views/wallet/transactions.vue`、`br-admin/src/views/system/user`
- Store：只新增业务选项 store，不改模板框架 store 的路由、标签页、锁屏等逻辑。

明确不改：

- `br-admin/src/layout/**`
- `br-admin/src/components/**`
- `br-admin/src/views/comp/**`
- `br-admin/src/views/form/**`
- `br-admin/src/views/list/basicList/**`
- `br-admin/src/views/dashboard/**`
- `br-admin/src/views/setting/**`
- `br-admin/src/views/system/menu/**`、`br-admin/src/views/system/role/**` 等模板/系统框架页面

## 文件结构

- 新建 `br-admin/scripts/test-admin-business-refactor.ts`：TDD 脚本测试入口，使用 `esno` 直接运行 TypeScript。
- 修改 `br-admin/package.json`：新增 `test:business-refactor`，并新增 `lint` 作为 `lint:eslint` 的别名，满足最终验证命令。
- 新建 `br-admin/src/api/contracts/admin.ts`：统一 admin API native meta、分页参数规范化、BasicTable 分页结果适配。
- 修改业务 API 文件：
  - `br-admin/src/api/booking/index.ts`
  - `br-admin/src/api/room/index.ts`
  - `br-admin/src/api/seat/index.ts`
  - `br-admin/src/api/wallet/index.ts`
  - `br-admin/src/api/activity/index.ts`
  - `br-admin/src/api/system/user.ts`
- 新建 `br-admin/src/views/business/shared/options.ts`：业务状态/类型/分区选项与 Tag 映射。
- 新建 `br-admin/src/views/business/shared/formatters.ts`：金额、日期、时间、支付方式、状态 tag 配置格式化。
- 新建 `br-admin/src/views/business/shared/tableBuilders.ts`：通用 `createTagColumn`、`createMoneyColumn`、`createDateTimeColumn` 等列 builder。
- 新建 `br-admin/src/views/business/shared/formSchemaBuilders.ts`：通用关键字、状态、日期范围、房间选择 schema builder。
- 新建 `br-admin/src/store/modules/adminBusiness.ts`：业务选项 store，负责加载并缓存房间下拉选项。
- 修改业务页面：
  - `br-admin/src/views/booking/list/index.vue`
  - `br-admin/src/views/room/list/index.vue`
  - `br-admin/src/views/activity/list/index.vue`
  - `br-admin/src/views/wallet/transactions.vue`
- 新建页面 builder：
  - `br-admin/src/views/booking/list/builders.ts`
  - `br-admin/src/views/room/list/builders.ts`
  - `br-admin/src/views/activity/list/builders.ts`
  - `br-admin/src/views/wallet/transactions.builders.ts`

## Task 1：业务 API contracts

**文件：**
- 新建：`br-admin/scripts/test-admin-business-refactor.ts`
- 新建：`br-admin/src/api/contracts/admin.ts`
- 修改：`br-admin/package.json`
- 修改：`br-admin/src/api/booking/index.ts`
- 修改：`br-admin/src/api/room/index.ts`
- 修改：`br-admin/src/api/seat/index.ts`
- 修改：`br-admin/src/api/wallet/index.ts`
- 修改：`br-admin/src/api/activity/index.ts`
- 修改：`br-admin/src/api/system/user.ts`

- [x] **Step 1：先写失败的 API contract 测试**

新增 `br-admin/scripts/test-admin-business-refactor.ts`：

```ts
import assert from 'node:assert/strict';

import {
  ADMIN_NATIVE_META,
  compactQuery,
  normalizePageParams,
  toBasicTableResult,
} from '../src/api/contracts/admin';

function testApiContracts() {
  assert.equal(ADMIN_NATIVE_META.isReturnNativeResponse, true);

  assert.deepEqual(
    normalizePageParams({ page: 2, pageSize: 30, status: '', keyword: '  abc  ' }),
    { page: 2, page_size: 30, keyword: 'abc' }
  );

  assert.deepEqual(
    compactQuery({ status: '', room_id: 0, page_size: 20, enabled: false, keyword: null }),
    { room_id: 0, page_size: 20, enabled: false }
  );

  assert.deepEqual(
    toBasicTableResult({
      items: [{ id: 1 }],
      total: 41,
      page: 2,
      page_size: 20,
    }),
    {
      list: [{ id: 1 }],
      itemCount: 41,
      pageCount: 3,
      page: 2,
    }
  );
}

testApiContracts();
console.log('br-admin business refactor tests passed');
```

`package.json` 新增脚本：

```json
"test:business-refactor": "esno scripts/test-admin-business-refactor.ts",
"lint": "pnpm lint:eslint"
```

- [x] **Step 2：运行测试并确认失败**

运行：

```bash
cd br-admin
pnpm test:business-refactor
```

预期：失败，提示 `src/api/contracts/admin` 不存在。

- [x] **Step 3：实现 API contracts**

新增 `br-admin/src/api/contracts/admin.ts`：

```ts
export const ADMIN_NATIVE_META = {
  isReturnNativeResponse: true,
} as const;

export interface AdminPageParams {
  page?: number;
  pageSize?: number;
  page_size?: number;
  [key: string]: unknown;
}

export interface AdminPageResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface BasicTableResult<T> {
  list: T[];
  itemCount: number;
  pageCount: number;
  page: number;
}

export function compactQuery<T extends Record<string, unknown>>(params: T): Partial<T> {
  return Object.entries(params).reduce<Partial<T>>((result, [key, value]) => {
    if (value === undefined || value === null || value === '') return result;
    result[key as keyof T] = typeof value === 'string' ? (value.trim() as T[keyof T]) : (value as T[keyof T]);
    if (result[key as keyof T] === '') delete result[key as keyof T];
    return result;
  }, {});
}

export function normalizePageParams<T extends AdminPageParams>(params: T = {} as T): Partial<T> & {
  page_size?: number;
} {
  const page_size = params.page_size ?? params.pageSize;
  const normalized = compactQuery({
    ...params,
    page_size,
    pageSize: undefined,
  });
  return normalized as Partial<T> & { page_size?: number };
}

export function toBasicTableResult<T>(response: AdminPageResponse<T>): BasicTableResult<T> {
  return {
    list: response.items,
    itemCount: response.total,
    pageCount: Math.ceil(response.total / response.page_size) || 1,
    page: response.page,
  };
}
```

- [x] **Step 4：业务 API 改用 contracts**

替换每个业务 API 文件中的重复 meta：

```ts
import { ADMIN_NATIVE_META } from '@/api/contracts/admin';
```

调用中统一使用：

```ts
meta: ADMIN_NATIVE_META
```

`wallet/index.ts` 和 `system/user.ts` 的列表 API 改用：

```ts
const result = await Alova.Get<ResponseType>('/path', {
  params: normalizePageParams(params),
  meta: ADMIN_NATIVE_META,
});
return toBasicTableResult(result);
```

- [x] **Step 5：运行测试和构建**

运行：

```bash
cd br-admin
pnpm test:business-refactor
pnpm build
```

预期：测试通过，构建通过。

- [x] **Step 6：提交**

```bash
git add br-admin/package.json br-admin/scripts/test-admin-business-refactor.ts br-admin/src/api/contracts/admin.ts br-admin/src/api/booking/index.ts br-admin/src/api/room/index.ts br-admin/src/api/seat/index.ts br-admin/src/api/wallet/index.ts br-admin/src/api/activity/index.ts br-admin/src/api/system/user.ts
git commit -m "refactor: extract admin api contracts"
```

## Task 2：业务共享 options、formatters、table column builders

**文件：**
- 新建：`br-admin/src/views/business/shared/options.ts`
- 新建：`br-admin/src/views/business/shared/formatters.ts`
- 新建：`br-admin/src/views/business/shared/tableBuilders.ts`
- 修改：`br-admin/scripts/test-admin-business-refactor.ts`

- [x] **Step 1：先写失败的 builder 测试**

在测试脚本中追加：

```ts
import {
  BOOKING_STATUS_TAGS,
  ROOM_STATUS_OPTIONS,
  SEAT_ZONE_OPTIONS,
  WALLET_TRANSACTION_TYPE_TAGS,
} from '../src/views/business/shared/options';
import {
  formatAdminDate,
  formatAdminDateTime,
  formatAdminMoney,
  getTagConfig,
} from '../src/views/business/shared/formatters';
import {
  createDateTimeColumn,
  createMoneyColumn,
  createTextColumn,
} from '../src/views/business/shared/tableBuilders';

function testSharedViewBuilders() {
  assert.deepEqual(ROOM_STATUS_OPTIONS[0], { label: '全部', value: '' });
  assert.equal(SEAT_ZONE_OPTIONS.find((item) => item.value === 'vip')?.label, 'VIP区');
  assert.equal(WALLET_TRANSACTION_TYPE_TAGS.recharge.label, '钱包充值');
  assert.equal(getTagConfig(BOOKING_STATUS_TAGS, 'confirmed').label, '已确认');
  assert.equal(getTagConfig(BOOKING_STATUS_TAGS, 'unknown').label, 'unknown');
  assert.equal(formatAdminMoney(12), '¥12.00');
  assert.equal(formatAdminDate(1717027200000), '2024-05-30');
  assert.equal(formatAdminDateTime('2024-05-30T09:05:00'), '2024-05-30 09:05');
  assert.equal(createTextColumn('名称', 'name', 120).key, 'name');
  assert.equal(createMoneyColumn('金额', 'amount').key, 'amount');
  assert.equal(createDateTimeColumn('创建时间', 'created_at').width, 170);
}

testSharedViewBuilders();
```

- [x] **Step 2：运行测试并确认失败**

运行：`cd br-admin && pnpm test:business-refactor`

预期：失败，提示 `src/views/business/shared/options` 不存在。

- [x] **Step 3：实现共享 options**

新增 `options.ts`，导出：

```ts
export type BusinessTagType = 'success' | 'warning' | 'error' | 'info' | 'default';

export interface BusinessOption<T = string | number | boolean | null> {
  label: string;
  value: T;
}

export interface BusinessTagConfig {
  label: string;
  type: BusinessTagType;
}

export const ROOM_STATUS_OPTIONS = [
  { label: '全部', value: '' },
  { label: '营业中', value: 'open' },
  { label: '已关闭', value: 'closed' },
];

export const ACTIVITY_STATUS_OPTIONS = [
  { label: '全部', value: '' },
  { label: '已上架', value: 'true' },
  { label: '已下架', value: 'false' },
];

export const BOOKING_STATUS_OPTIONS = [
  { label: '全部', value: '' },
  { label: '已确认', value: 'confirmed' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
];

export const SEAT_ZONE_OPTIONS = [
  { label: '静音区', value: 'quiet' },
  { label: '键盘区', value: 'keyboard' },
  { label: 'VIP区', value: 'vip' },
];

export const BOOKING_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  confirmed: { label: '已确认', type: 'success' },
  completed: { label: '已完成', type: 'info' },
  cancelled: { label: '已取消', type: 'error' },
};

export const ROOM_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  open: { label: '营业中', type: 'success' },
  closed: { label: '已关闭', type: 'error' },
};

export const ACTIVITY_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  true: { label: '已上架', type: 'success' },
  false: { label: '已下架', type: 'default' },
};

export const WALLET_TRANSACTION_TYPE_TAGS: Record<string, BusinessTagConfig> = {
  recharge: { label: '钱包充值', type: 'success' },
  consume: { label: '预约消费', type: 'warning' },
  booking_refund: { label: '预约退款', type: 'success' },
  refund: { label: '钱包退款', type: 'error' },
  wallet_refund: { label: '钱包退款', type: 'error' },
};

export const WALLET_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  pending: { label: '待处理', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'error' },
  cancelled: { label: '已取消', type: 'default' },
};
```

- [x] **Step 4：实现 formatters 和 tableBuilders**

`formatters.ts` 导出 `formatAdminMoney`、`formatAdminDate`、`formatAdminDateTime`、`formatPaymentMethod`、`getTagConfig`。

`tableBuilders.ts` 导出 `createTextColumn`、`createMoneyColumn`、`createDateTimeColumn`、`createTagColumn`。

- [x] **Step 5：运行测试和构建**

运行：

```bash
cd br-admin
pnpm test:business-refactor
pnpm build
```

预期：测试和构建通过。

- [x] **Step 6：提交**

```bash
git add br-admin/scripts/test-admin-business-refactor.ts br-admin/src/views/business/shared/options.ts br-admin/src/views/business/shared/formatters.ts br-admin/src/views/business/shared/tableBuilders.ts
git commit -m "refactor: add admin business view builders"
```

## Task 3：业务 form schema builders 与业务选项 store

**文件：**
- 新建：`br-admin/src/views/business/shared/formSchemaBuilders.ts`
- 新建：`br-admin/src/store/modules/adminBusiness.ts`
- 修改：`br-admin/scripts/test-admin-business-refactor.ts`

- [x] **Step 1：先写失败的 schema/store 测试**

追加测试：

```ts
import {
  createDateRangeSchema,
  createKeywordSchema,
  createRoomSelectSchema,
  createStatusSchema,
  normalizeDateRange,
} from '../src/views/business/shared/formSchemaBuilders';

function testFormSchemaBuilders() {
  assert.equal(createKeywordSchema('keyword', '搜索名称').field, 'keyword');
  assert.equal(createStatusSchema('status', ROOM_STATUS_OPTIONS).component, 'NSelect');
  assert.equal(createRoomSelectSchema([]).field, 'room_id');
  assert.equal(createDateRangeSchema('dateRange', '预约日期').componentProps.type, 'daterange');
  assert.deepEqual(normalizeDateRange([1717027200000, 1717113600000]), {
    date_start: '2024-05-30',
    date_end: '2024-05-31',
  });
  assert.deepEqual(normalizeDateRange(null), {});
}

testFormSchemaBuilders();
```

- [x] **Step 2：运行测试并确认失败**

运行：`cd br-admin && pnpm test:business-refactor`

预期：失败，提示 `formSchemaBuilders` 不存在。

- [x] **Step 3：实现 form schema builders**

新增 `formSchemaBuilders.ts`，导出：

```ts
createKeywordSchema(field, placeholder)
createStatusSchema(field, options)
createRoomSelectSchema(options)
createDateRangeSchema(field, label)
normalizeDateRange(dateRange)
```

- [x] **Step 4：实现业务选项 store**

新增 `adminBusiness.ts`：

```ts
import { defineStore } from 'pinia';
import { store } from '@/store';
import { getRoomList } from '@/api/room';

export interface BusinessSelectOption {
  label: string;
  value: number;
}

export const useAdminBusinessStore = defineStore({
  id: 'admin-business',
  state: () => ({
    roomOptions: [] as BusinessSelectOption[],
    roomOptionsLoaded: false,
  }),
  actions: {
    async loadRoomOptions(force = false) {
      if (this.roomOptionsLoaded && !force) return this.roomOptions;
      const result = await getRoomList({ page_size: 999 });
      this.roomOptions = result.items.map((room) => ({ label: room.name, value: room.id }));
      this.roomOptionsLoaded = true;
      return this.roomOptions;
    },
  },
});

export function useAdminBusiness() {
  return useAdminBusinessStore(store);
}
```

- [x] **Step 5：运行测试和构建**

运行：

```bash
cd br-admin
pnpm test:business-refactor
pnpm build
```

预期：测试和构建通过。

- [x] **Step 6：提交**

```bash
git add br-admin/scripts/test-admin-business-refactor.ts br-admin/src/views/business/shared/formSchemaBuilders.ts br-admin/src/store/modules/adminBusiness.ts
git commit -m "refactor: add admin business schema builders"
```

## Task 4：预约/房间/活动页面接入 builders

**文件：**
- 新建：`br-admin/src/views/booking/list/builders.ts`
- 新建：`br-admin/src/views/room/list/builders.ts`
- 新建：`br-admin/src/views/activity/list/builders.ts`
- 修改：`br-admin/src/views/booking/list/index.vue`
- 修改：`br-admin/src/views/room/list/index.vue`
- 修改：`br-admin/src/views/room/list/columns.ts`
- 修改：`br-admin/src/views/activity/list/index.vue`
- 修改：`br-admin/src/views/activity/list/columns.ts`
- 修改：`br-admin/scripts/test-admin-business-refactor.ts`

- [ ] **Step 1：先写失败的页面 builder 测试**

追加测试：

```ts
import { buildBookingSearchSchemas, buildBookingTableColumns } from '../src/views/booking/list/builders';
import { buildRoomSearchSchemas, buildRoomTableColumns } from '../src/views/room/list/builders';
import { buildActivitySearchSchemas, buildActivityTableColumns } from '../src/views/activity/list/builders';

function testPageBuilders() {
  assert.equal(buildBookingSearchSchemas([]).length, 3);
  assert.equal(buildBookingTableColumns().some((column) => column.key === 'status'), true);
  assert.equal(buildRoomSearchSchemas().length, 2);
  assert.equal(buildRoomTableColumns().some((column) => column.key === 'min_price'), true);
  assert.equal(buildActivitySearchSchemas().length, 2);
  assert.equal(buildActivityTableColumns().some((column) => column.key === 'is_active'), true);
}

testPageBuilders();
```

- [ ] **Step 2：运行测试并确认失败**

运行：`cd br-admin && pnpm test:business-refactor`

预期：失败，提示 `views/booking/list/builders` 不存在。

- [ ] **Step 3：实现三个页面 builder**

每个 builder 文件只导出搜索 schema 和表格列：

```ts
export function buildBookingSearchSchemas(roomOptions) { ... }
export function buildBookingTableColumns() { ... }
export function buildRoomSearchSchemas() { ... }
export function buildRoomTableColumns() { ... }
export function buildActivitySearchSchemas() { ... }
export function buildActivityTableColumns() { ... }
```

表格列中复用共享 builder，不再在 `.vue` 中内联状态 tag、金额、日期列配置。

- [ ] **Step 4：页面接入 builders**

`booking/list/index.vue`：
- 删除内联 `schemas` 和 `columns`
- 使用 `useAdminBusiness()` 加载房间选项
- `schemas` 由 `buildBookingSearchSchemas(roomOptions)` 生成
- `columns` 由 `buildBookingTableColumns()` 生成

`room/list/index.vue`：
- 删除内联 `schemas`
- 使用 `buildRoomSearchSchemas()`
- `columns.ts` 改为 re-export `buildRoomTableColumns()`

`activity/list/index.vue`：
- 删除内联 `schemas`
- 使用 `buildActivitySearchSchemas()`
- `columns.ts` 改为 re-export `buildActivityTableColumns()`

- [ ] **Step 5：运行测试、构建、lint**

运行：

```bash
cd br-admin
pnpm test:business-refactor
pnpm build
pnpm lint
```

预期：三条命令通过。`pnpm lint` 是 `lint:eslint` 别名，可能会自动修复格式；如有自动修改，检查并纳入提交。

- [ ] **Step 6：提交**

```bash
git add br-admin/scripts/test-admin-business-refactor.ts br-admin/src/views/booking/list/builders.ts br-admin/src/views/room/list/builders.ts br-admin/src/views/activity/list/builders.ts br-admin/src/views/booking/list/index.vue br-admin/src/views/room/list/index.vue br-admin/src/views/room/list/columns.ts br-admin/src/views/activity/list/index.vue br-admin/src/views/activity/list/columns.ts
git commit -m "refactor: extract admin page builders"
```

## Task 5：钱包交易页接入 builders

**文件：**
- 新建：`br-admin/src/views/wallet/transactions.builders.ts`
- 修改：`br-admin/src/views/wallet/transactions.vue`
- 修改：`br-admin/scripts/test-admin-business-refactor.ts`

- [ ] **Step 1：先写失败的钱包 builder 测试**

追加测试：

```ts
import {
  buildWalletFilterOptions,
  buildWalletStatCards,
  buildWalletTransactionColumns,
} from '../src/views/wallet/transactions.builders';

function testWalletBuilders() {
  const options = buildWalletFilterOptions();
  assert.equal(options.typeOptions.some((item) => item.value === 'recharge'), true);
  assert.equal(options.statusOptions.some((item) => item.value === 'completed'), true);
  assert.equal(buildWalletStatCards({ total_recharge: 1, total_consume: 2, total_refund: 3, net_income: 4 }).length, 4);
  assert.equal(buildWalletTransactionColumns().some((column) => column.key === 'payment_method'), true);
}

testWalletBuilders();
```

- [ ] **Step 2：运行测试并确认失败**

运行：`cd br-admin && pnpm test:business-refactor`

预期：失败，提示 `transactions.builders` 不存在。

- [ ] **Step 3：实现钱包 builder**

新增 `transactions.builders.ts`，导出：

```ts
buildWalletFilterOptions()
buildWalletStatCards(statistics)
buildWalletTransactionColumns()
```

- [ ] **Step 4：钱包页面接入 builder**

`transactions.vue`：
- 删除内联 `typeOptions`、`statusOptions`、`transactionTypeMap`、`statusMap`、`paymentMethodMap`
- `statCards` 改为 `computed(() => buildWalletStatCards(statistics))`
- `columns` 改为 `buildWalletTransactionColumns()`
- 保留页面事件编排：筛选、导出、加载统计、刷新表格。

- [ ] **Step 5：运行测试、构建、lint**

运行：

```bash
cd br-admin
pnpm test:business-refactor
pnpm build
pnpm lint
```

预期：全部通过。

- [ ] **Step 6：提交**

```bash
git add br-admin/scripts/test-admin-business-refactor.ts br-admin/src/views/wallet/transactions.builders.ts br-admin/src/views/wallet/transactions.vue
git commit -m "refactor: extract wallet transaction builders"
```

## 最终验证

- [ ] 运行：`cd br-admin && pnpm test:business-refactor`
- [ ] 运行：`cd br-admin && pnpm build`
- [ ] 运行：`cd br-admin && pnpm lint`
- [ ] 运行：`git status --short --branch`
- [ ] 确认本轮只改 `br-admin` 业务 API/view/store 和中文计划文档，没有改模板框架代码。

## 自检

- 需求覆盖：API contracts、table column builders、form schema builders、业务 store 均有独立任务。
- 范围控制：计划明确排除模板框架、layout、通用 components、示例页和系统框架页。
- TDD：每个任务先添加脚本测试，确认失败后再实现，最后执行构建和 lint。
- 验证命令：最终按用户要求执行 `pnpm build` 和 `pnpm lint`，并额外保留 `pnpm test:business-refactor` 作为本轮重构的 TDD 回归测试。
