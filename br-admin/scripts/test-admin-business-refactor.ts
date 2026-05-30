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
