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
console.log('br-admin business refactor tests passed');
