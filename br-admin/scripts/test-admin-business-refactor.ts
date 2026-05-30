import assert from 'node:assert/strict';

import {
  ADMIN_NATIVE_META,
  compactQuery,
  normalizePageParams,
  toBasicTableResult,
} from '../src/api/contracts/admin';
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
import {
  createDateRangeSchema,
  createKeywordSchema,
  createRoomSelectSchema,
  createStatusSchema,
  normalizeDateRange,
} from '../src/views/business/shared/formSchemaBuilders';
import { buildBookingSearchSchemas, buildBookingTableColumns } from '../src/views/booking/list/builders';
import { buildRoomSearchSchemas, buildRoomTableColumns } from '../src/views/room/list/builders';
import {
  buildActivitySearchSchemas,
  buildActivityTableColumns,
} from '../src/views/activity/list/builders';
import {
  buildWalletFilterOptions,
  buildWalletStatCards,
  buildWalletTransactionColumns,
} from '../src/views/wallet/transactions.builders';

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

function testPageBuilders() {
  assert.equal(buildBookingSearchSchemas([]).length, 3);
  assert.equal(
    buildBookingTableColumns().some((column) => column.key === 'status'),
    true
  );
  assert.equal(buildRoomSearchSchemas().length, 2);
  assert.equal(
    buildRoomTableColumns().some((column) => column.key === 'min_price'),
    true
  );
  assert.equal(buildActivitySearchSchemas().length, 2);
  assert.equal(
    buildActivityTableColumns().some((column) => column.key === 'is_active'),
    true
  );
}

testPageBuilders();

function testWalletBuilders() {
  const options = buildWalletFilterOptions();
  assert.equal(
    options.typeOptions.some((item) => item.value === 'recharge'),
    true
  );
  assert.equal(
    options.statusOptions.some((item) => item.value === 'completed'),
    true
  );
  assert.equal(
    buildWalletStatCards({
      total_recharge: 1,
      total_consume: 2,
      total_refund: 3,
      net_income: 4,
      active_users: 0,
      total_transactions: 0,
    }).length,
    4
  );
  assert.equal(
    buildWalletTransactionColumns().some((column) => column.key === 'payment_method'),
    true
  );
}

testWalletBuilders();
console.log('br-admin business refactor tests passed');
