# br-app Page Logic Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor oversized `br-app` pages so page files keep presentation and event orchestration while shared API, formatting, follow-room, and payment-polling logic lives in focused modules.

**Architecture:** Extract pure formatting/constants first, then wrap storage/API behavior behind page services and composables. Keep existing page templates and styles intact unless a binding must change, so each task has a small behavioral surface and can be validated independently.

**Tech Stack:** Vue 3 options/composition APIs, uni-app, existing `src/api/*` modules, Node script tests, `npm run build:h5`.

---

## File Structure

- Create `br-app/src/constants/booking.js`: booking status labels, seat-zone labels, and booking tab metadata shared by booking/order pages.
- Create `br-app/src/constants/wallet.js`: wallet transaction labels, recharge bounds, and polling status constants.
- Create `br-app/src/utils/formatters.js`: pure money, amount, date, time, duration, room-price, booking-status, and wallet-status formatters.
- Create `br-app/src/services/followedRooms.js`: storage-backed follow-room service that normalizes room shape and centralizes summaries.
- Modify `br-app/src/utils/followedRooms.js`: compatibility re-export so existing imports keep working during the refactor.
- Create `br-app/src/services/paymentPolling.js`: shared async polling helpers for booking payment and wallet recharge status.
- Create `br-app/src/services/bookingPageService.js`: page-facing booking API orchestration for rooms, bookings, wallet balance, coupons, and cancellation.
- Create `br-app/src/services/walletPageService.js`: page-facing wallet/recharge API orchestration.
- Create `br-app/scripts/test-refactored-page-logic.js`: Node script test harness for extracted pure/service modules.
- Modify `br-app/package.json`: add `test:refactor` and `test:scripts`.
- Modify these pages to import extracted logic without changing templates/styles unless bindings require it:
  - `br-app/src/pages/index/index.vue`
  - `br-app/src/pages/profile/index.vue`
  - `br-app/src/pages/booking/detail.vue`
  - `br-app/src/pages/booking/confirm.vue`
  - `br-app/src/pages/orders/index.vue`
  - `br-app/src/pages/wallet/transactions.vue`
  - `br-app/src/pages/recharge/index.vue`

## Task 1: Shared Formatters and Constants

**Files:**
- Create: `br-app/src/constants/booking.js`
- Create: `br-app/src/constants/wallet.js`
- Create: `br-app/src/utils/formatters.js`
- Create: `br-app/scripts/test-refactored-page-logic.js`
- Modify: `br-app/package.json`

- [ ] **Step 1: Write the failing formatter tests**

Add `br-app/scripts/test-refactored-page-logic.js` with a loader that evaluates ES-module source in Node and tests these exported functions:

```js
const assert = require('assert')
const fs = require('fs')
const path = require('path')
const vm = require('vm')

const appRoot = path.resolve(__dirname, '..')

function loadModule(relativePath, injected = {}) {
  const filename = path.join(appRoot, relativePath)
  let source = fs.readFileSync(filename, 'utf8')
  source = source.replace(/import\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"];?/g, (_match, names, request) => {
    return `const { ${names.trim()} } = __imports[${JSON.stringify(request)}]`
  })
  source = source.replace(/export\s+const\s+([A-Za-z0-9_$]+)\s*=/g, 'exports.$1 =')
  source = source.replace(/export\s+function\s+([A-Za-z0-9_$]+)\s*\(/g, 'exports.$1 = function $1(')
  source = source.replace(/export\s+\{([^}]+)\}/g, (_match, names) => {
    return names.split(',').map((name) => {
      const trimmed = name.trim()
      return `exports.${trimmed} = ${trimmed}`
    }).join('\n')
  })

  const sandbox = {
    exports: {},
    console,
    setTimeout,
    clearTimeout,
    __imports: injected,
  }
  vm.runInNewContext(source, sandbox, { filename })
  return sandbox.exports
}

function testFormatters() {
  const {
    formatMoney,
    formatAmount,
    formatShortTime,
    formatDateSlash,
    formatRoomMinPrice,
    formatBookingStatus,
    formatWalletStatus,
    formatHourDuration,
  } = loadModule('src/utils/formatters.js')

  assert.equal(formatMoney(12), '12.00')
  assert.equal(formatMoney(''), '0.00')
  assert.equal(formatAmount(12.5), '12.5')
  assert.equal(formatAmount('12.00'), '12')
  assert.equal(formatShortTime('2026-05-30T09:05:00'), '09:05')
  assert.equal(formatShortTime('09:30:00'), '09:30')
  assert.equal(formatDateSlash('2026-05-30'), '2026/05/30')
  assert.equal(formatRoomMinPrice({ min_price: 8 }), '¥8起')
  assert.equal(formatRoomMinPrice({ min_price: 0 }), '')
  assert.equal(formatBookingStatus('confirmed'), '已预约')
  assert.equal(formatBookingStatus('unknown'), 'unknown')
  assert.equal(formatWalletStatus('completed'), '已完成')
  assert.equal(formatHourDuration('09:00', '11:30'), '2.5小时')
}

testFormatters()
console.log('br-app refactored page logic tests passed')
```

Add the script entries:

```json
"test:refactor": "node scripts/test-refactored-page-logic.js",
"test:scripts": "npm run test:profile-links && npm run test:wechat-appid && npm run test:refactor"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd br-app && npm run test:refactor`

Expected: FAIL with `ENOENT` for `src/utils/formatters.js`.

- [ ] **Step 3: Implement constants and formatters**

Create `br-app/src/constants/booking.js`:

```js
export const BOOKING_TABS = [
  { label: '全部', value: 'all' },
  { label: '待开始', value: 'confirmed' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
]

export const BOOKING_STATUS_LABELS = {
  pending: '待支付',
  confirmed: '已预约',
  completed: '已完成',
  cancelled: '已取消',
}

export const SEAT_ZONE_LABELS = {
  quiet: '静音区',
  keyboard: '键盘区',
  vip: 'VIP区',
}
```

Create `br-app/src/constants/wallet.js`:

```js
export const WALLET_TRANSACTION_STATUS_LABELS = {
  completed: '已完成',
  pending: '处理中',
  failed: '失败',
}

export const RECHARGE_DEFAULT_AMOUNT = 50
export const RECHARGE_MIN_AMOUNT = 1
export const RECHARGE_MAX_AMOUNT = 9999

export const PAYMENT_POLL_INTERVAL = 2000
export const PAYMENT_POLL_MAX_ATTEMPTS = 10
export const PAYMENT_TERMINAL_FAILURE_STATUSES = ['failed', 'cancelled', 'closed']
```

Create `br-app/src/utils/formatters.js`:

```js
import { BOOKING_STATUS_LABELS, SEAT_ZONE_LABELS } from '@/constants/booking'
import { WALLET_TRANSACTION_STATUS_LABELS } from '@/constants/wallet'

function toFiniteNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

export function formatMoney(value) {
  return toFiniteNumber(value).toFixed(2)
}

export function formatAmount(value) {
  const amount = toFiniteNumber(value)
  return Number.isInteger(amount) ? String(amount) : amount.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
}

export function formatShortTime(value) {
  if (!value) return ''
  if (typeof value === 'string' && /^\d{1,2}:\d{2}/.test(value)) return value.slice(0, 5)
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

export function formatDateSlash(value) {
  if (!value) return ''
  return String(value).slice(0, 10).replace(/-/g, '/')
}

export function formatRoomMinPrice(room) {
  const price = Number(room?.min_price ?? room?.minPrice)
  if (!Number.isFinite(price) || price <= 0) return ''
  return `¥${formatAmount(price)}起`
}

export function formatBookingStatus(status) {
  return BOOKING_STATUS_LABELS[status] || status || ''
}

export function formatWalletStatus(status) {
  return WALLET_TRANSACTION_STATUS_LABELS[status] || '处理中'
}

export function formatSeatZone(zone) {
  return SEAT_ZONE_LABELS[zone] || zone || ''
}

export function formatHourDuration(startTime, endTime) {
  const parse = (time) => {
    const [hours = 0, minutes = 0] = String(time || '').split(':').map(Number)
    return hours + minutes / 60
  }
  const duration = Math.max(0, parse(endTime) - parse(startTime))
  return `${formatAmount(duration)}小时`
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd br-app && npm run test:refactor`

Expected: PASS with `br-app refactored page logic tests passed`.

- [ ] **Step 5: Commit**

Run:

```bash
git add br-app/package.json br-app/scripts/test-refactored-page-logic.js br-app/src/constants/booking.js br-app/src/constants/wallet.js br-app/src/utils/formatters.js
git commit -m "refactor: add app formatter constants"
```

## Task 2: Followed Room Page Service

**Files:**
- Create: `br-app/src/services/followedRooms.js`
- Modify: `br-app/src/utils/followedRooms.js`
- Modify: `br-app/src/pages/index/index.vue`
- Modify: `br-app/src/pages/profile/index.vue`
- Modify: `br-app/src/pages/booking/detail.vue`
- Modify: `br-app/scripts/test-refactored-page-logic.js`

- [ ] **Step 1: Write failing followed-room service tests**

Extend `test-refactored-page-logic.js` with a `testFollowedRooms()` function that injects a fake `uni` storage API and checks normalization, summary, follow, and unfollow:

```js
function testFollowedRooms() {
  const storage = {}
  global.uni = {
    getStorageSync(key) {
      return storage[key]
    },
    setStorageSync(key, value) {
      storage[key] = value
    },
  }

  const service = loadModule('src/services/followedRooms.js')
  service.followRoom({ id: '7', name: '南门店', minPrice: 8, cityName: '茂名' })
  assert.equal(service.isRoomFollowed(7), true)
  assert.equal(service.getFollowedRooms()[0].min_price, 8)
  assert.equal(service.getFollowedRoomsSummary(service.getFollowedRooms()), '南门店')
  service.followRoom({ room_id: 8, name: '东门店' })
  assert.equal(service.getFollowedRoomsSummary(service.getFollowedRooms()), '东门店等2家')
  service.unfollowRoom(7)
  assert.deepEqual(service.getFollowedRooms().map((room) => room.id), [8])
  delete global.uni
}
```

Call `testFollowedRooms()` before the final console log.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd br-app && npm run test:refactor`

Expected: FAIL with `ENOENT` for `src/services/followedRooms.js`.

- [ ] **Step 3: Implement followed-room service and re-export**

Create `br-app/src/services/followedRooms.js` with:

```js
export const FOLLOWED_ROOMS_STORAGE_KEY = 'followed_rooms'

export function normalizeRoom(room = {}) {
  const id = room.id ?? room.room_id
  if (id === undefined || id === null || id === '') return null

  return {
    id: Number(id),
    name: room.name || '未命名自习室',
    address: room.address || '',
    cover_image: room.cover_image || room.coverImage || '',
    city_id: room.city_id ?? room.cityId ?? null,
    city_name: room.city_name || room.cityName || '',
    min_price: room.min_price ?? room.minPrice ?? '',
    status: room.status || '',
    followed_at: room.followed_at || Date.now(),
  }
}

export function getFollowedRooms() {
  const storedRooms = uni.getStorageSync(FOLLOWED_ROOMS_STORAGE_KEY)
  const rooms = Array.isArray(storedRooms) ? storedRooms : []
  return rooms.map(normalizeRoom).filter(Boolean)
}

export function isRoomFollowed(roomId) {
  const normalizedId = Number(roomId)
  return getFollowedRooms().some((room) => room.id === normalizedId)
}

export function followRoom(room) {
  const normalizedRoom = normalizeRoom(room)
  if (!normalizedRoom) return getFollowedRooms()

  const rooms = getFollowedRooms().filter((item) => item.id !== normalizedRoom.id)
  const nextRooms = [normalizedRoom, ...rooms]
  uni.setStorageSync(FOLLOWED_ROOMS_STORAGE_KEY, nextRooms)
  return nextRooms
}

export function unfollowRoom(roomId) {
  const normalizedId = Number(roomId)
  const nextRooms = getFollowedRooms().filter((room) => room.id !== normalizedId)
  uni.setStorageSync(FOLLOWED_ROOMS_STORAGE_KEY, nextRooms)
  return nextRooms
}

export function getFollowedRoomsSummary(rooms = getFollowedRooms()) {
  if (rooms.length === 0) return '暂无关注'
  if (rooms.length === 1) return rooms[0].name
  return `${rooms[0].name}等${rooms.length}家`
}
```

Replace `br-app/src/utils/followedRooms.js` with:

```js
export {
  FOLLOWED_ROOMS_STORAGE_KEY,
  followRoom,
  getFollowedRooms,
  getFollowedRoomsSummary,
  isRoomFollowed,
  normalizeRoom,
  unfollowRoom,
} from '@/services/followedRooms'
```

- [ ] **Step 4: Move page imports to service**

Update the three page imports:

```js
import { getFollowedRooms } from '@/services/followedRooms'
import { followRoom, isRoomFollowed, unfollowRoom } from '@/services/followedRooms'
import { getFollowedRooms, getFollowedRoomsSummary } from '@/services/followedRooms'
```

In `profile/index.vue`, replace the computed summary body with:

```js
followedRoomsSummary() {
  return getFollowedRoomsSummary(this.followedRooms)
}
```

- [ ] **Step 5: Run tests and build**

Run:

```bash
cd br-app
npm run test:refactor
npm run build:h5
```

Expected: both commands pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add br-app/scripts/test-refactored-page-logic.js br-app/src/services/followedRooms.js br-app/src/utils/followedRooms.js br-app/src/pages/index/index.vue br-app/src/pages/profile/index.vue br-app/src/pages/booking/detail.vue
git commit -m "refactor: extract followed room service"
```

## Task 3: Shared Payment Polling

**Files:**
- Create: `br-app/src/services/paymentPolling.js`
- Modify: `br-app/src/pages/booking/confirm.vue`
- Modify: `br-app/src/pages/recharge/index.vue`
- Modify: `br-app/scripts/test-refactored-page-logic.js`

- [ ] **Step 1: Write failing payment-polling tests**

Add `testPaymentPolling()`:

```js
async function testPaymentPolling() {
  const service = loadModule('src/services/paymentPolling.js', {
    '@/constants/wallet': {
      PAYMENT_POLL_INTERVAL: 2000,
      PAYMENT_POLL_MAX_ATTEMPTS: 10,
      PAYMENT_TERMINAL_FAILURE_STATUSES: ['failed', 'cancelled', 'closed'],
    },
  })

  const paid = await service.pollPaymentStatus({
    fetchStatus: async () => ({ payment_status: 'paid' }),
    isSuccess: (status) => status === 'paid',
    wait: async () => {},
  })
  assert.equal(paid.payment_status, 'paid')

  await assert.rejects(
    () => service.pollPaymentStatus({
      fetchStatus: async () => ({ status: 'failed' }),
      isSuccess: (status) => status === 'completed',
      wait: async () => {},
    }),
    (error) => error.paymentStatus === 'failed',
  )
}
```

Call it from an async `main()` function:

```js
async function main() {
  testFormatters()
  testFollowedRooms()
  await testPaymentPolling()
  console.log('br-app refactored page logic tests passed')
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd br-app && npm run test:refactor`

Expected: FAIL with `ENOENT` for `src/services/paymentPolling.js`.

- [ ] **Step 3: Implement payment polling**

Create `br-app/src/services/paymentPolling.js`:

```js
import {
  PAYMENT_POLL_INTERVAL,
  PAYMENT_POLL_MAX_ATTEMPTS,
  PAYMENT_TERMINAL_FAILURE_STATUSES,
} from '@/constants/wallet'

export function createPaymentStatusError(status) {
  const error = new Error(`payment ${status}`)
  error.paymentStatus = status
  return error
}

export function getPaymentStatus(response) {
  return response?.payment_status || response?.paymentStatus || response?.status
}

export function waitForPaymentPoll(ms = PAYMENT_POLL_INTERVAL) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

export async function pollPaymentStatus({
  fetchStatus,
  isSuccess,
  failureStatuses = PAYMENT_TERMINAL_FAILURE_STATUSES,
  maxAttempts = PAYMENT_POLL_MAX_ATTEMPTS,
  wait = waitForPaymentPoll,
}) {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const result = await fetchStatus()
    const status = getPaymentStatus(result)
    if (isSuccess(status, result)) return result
    if (failureStatuses.includes(status)) throw createPaymentStatusError(status)
    await wait()
  }

  throw createPaymentStatusError('timeout')
}
```

- [ ] **Step 4: Replace booking confirm polling**

In `booking/confirm.vue`, import:

```js
import { createPaymentStatusError, pollPaymentStatus, waitForPaymentPoll } from '@/services/paymentPolling'
```

Replace the local `pollBookingPaymentStatus`, `createPaymentStatusError`, and `wait` methods with:

```js
async pollBookingPaymentStatus(bookingId) {
  return pollPaymentStatus({
    fetchStatus: () => getBookingPaymentStatus(bookingId),
    isSuccess: (status) => status === 'paid',
    wait: () => waitForPaymentPoll(PAYMENT_POLL_INTERVAL),
    maxAttempts: PAYMENT_POLL_MAX_ATTEMPTS,
  })
},
createPaymentStatusError,
```

- [ ] **Step 5: Replace recharge polling**

In `recharge/index.vue`, import:

```js
import { createPaymentStatusError, pollPaymentStatus, waitForPaymentPoll } from '@/services/paymentPolling'
```

Replace local polling helpers with:

```js
async pollRechargeOrder(orderId) {
  return pollPaymentStatus({
    fetchStatus: () => getRechargeOrder(orderId),
    isSuccess: (status) => status === 'completed',
    wait: () => waitForPaymentPoll(RECHARGE_POLL_INTERVAL),
    maxAttempts: RECHARGE_POLL_MAX_ATTEMPTS,
  })
},
createPaymentStatusError,
```

- [ ] **Step 6: Run tests and build**

Run:

```bash
cd br-app
npm run test:refactor
npm run build:h5
```

Expected: both commands pass.

- [ ] **Step 7: Commit**

Run:

```bash
git add br-app/scripts/test-refactored-page-logic.js br-app/src/services/paymentPolling.js br-app/src/pages/booking/confirm.vue br-app/src/pages/recharge/index.vue
git commit -m "refactor: share payment polling logic"
```

## Task 4: Page Services for Booking and Wallet API Calls

**Files:**
- Create: `br-app/src/services/bookingPageService.js`
- Create: `br-app/src/services/walletPageService.js`
- Modify: `br-app/src/pages/booking/confirm.vue`
- Modify: `br-app/src/pages/booking/detail.vue`
- Modify: `br-app/src/pages/orders/index.vue`
- Modify: `br-app/src/pages/wallet/transactions.vue`
- Modify: `br-app/src/pages/recharge/index.vue`

- [ ] **Step 1: Write failing service smoke tests**

Extend the script to load `bookingPageService.js` and `walletPageService.js` with fake API functions and assert the page services call through:

```js
function testPageServices() {
  const bookingService = loadModule('src/services/bookingPageService.js', {
    '@/api/bookings': {
      getBookings: async (params) => ({ params, items: [] }),
      cancelBooking: async (id) => ({ id, refund_amount: '1.00' }),
      createBooking: async (payload) => ({ id: 9, ...payload }),
      getBookingPaymentStatus: async (id) => ({ id, payment_status: 'paid' }),
    },
    '@/api/coupons': { getAvailableCouponsForBooking: async (payload) => ({ payload, items: [] }) },
    '@/api/rooms': { getRoom: async (id) => ({ id }) },
    '@/api/seats': { getSeats: async (roomId, params) => [{ roomId, ...params }] },
    '@/api/wallet': { getBalance: async () => ({ balance: '8.00' }) },
  })
  assert.equal(typeof bookingService.fetchBookingsPage, 'function')
  assert.equal(typeof bookingService.cancelBookingOrder, 'function')

  const walletService = loadModule('src/services/walletPageService.js', {
    '@/api/wallet': {
      getBalance: async () => ({ balance: '8.00' }),
      getWalletTransactions: async (params) => ({ params, items: [] }),
      createRechargeOrder: async (payload) => ({ order_id: 1, ...payload }),
      getRechargeOrder: async (id) => ({ id, status: 'completed' }),
      confirmPayment: async (id) => ({ id }),
      redeemPromoCode: async (code) => ({ code }),
    },
  })
  assert.equal(typeof walletService.fetchWalletTransactionsPage, 'function')
  assert.equal(typeof walletService.createRechargePaymentOrder, 'function')
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd br-app && npm run test:refactor`

Expected: FAIL with `ENOENT` for `src/services/bookingPageService.js`.

- [ ] **Step 3: Implement booking page service**

Create `br-app/src/services/bookingPageService.js`:

```js
import {
  cancelBooking,
  createBooking,
  getBookingPaymentStatus,
  getBookings,
} from '@/api/bookings'
import { getAvailableCouponsForBooking } from '@/api/coupons'
import { getRoom } from '@/api/rooms'
import { getSeats } from '@/api/seats'
import { getBalance } from '@/api/wallet'

export function fetchBookingsPage(params) {
  return getBookings(params)
}

export function cancelBookingOrder(id) {
  return cancelBooking(id)
}

export function createBookingOrder(payload) {
  return createBooking(payload)
}

export function fetchBookingPaymentStatus(bookingId) {
  return getBookingPaymentStatus(bookingId)
}

export function fetchBookingRoom(roomId) {
  return getRoom(roomId)
}

export function fetchBookingSeats(roomId, params) {
  return getSeats(roomId, params)
}

export function fetchBookingCoupons(payload) {
  return getAvailableCouponsForBooking(payload)
}

export function fetchWalletBalance() {
  return getBalance()
}
```

- [ ] **Step 4: Implement wallet page service**

Create `br-app/src/services/walletPageService.js`:

```js
import {
  confirmPayment,
  createRechargeOrder,
  getBalance,
  getRechargeOrder,
  getWalletTransactions,
  redeemPromoCode,
} from '@/api/wallet'

export function fetchWalletBalance() {
  return getBalance()
}

export function fetchWalletTransactionsPage(params) {
  return getWalletTransactions(params)
}

export function createRechargePaymentOrder(payload) {
  return createRechargeOrder(payload)
}

export function fetchRechargePaymentOrder(orderId) {
  return getRechargeOrder(orderId)
}

export function confirmRechargePayment(orderId) {
  return confirmPayment(orderId)
}

export function redeemRechargePromoCode(code) {
  return redeemPromoCode(code)
}
```

- [ ] **Step 5: Move page API imports to services**

Use these replacements:

```js
// booking/confirm.vue
import {
  createBookingOrder,
  fetchBookingCoupons,
  fetchBookingPaymentStatus,
  fetchBookingRoom,
  fetchBookingSeats,
  fetchWalletBalance,
} from '@/services/bookingPageService'

// booking/detail.vue
import { fetchBookingRoom } from '@/services/bookingPageService'

// orders/index.vue
import { cancelBookingOrder, fetchBookingsPage } from '@/services/bookingPageService'

// wallet/transactions.vue
import { fetchWalletBalance, fetchWalletTransactionsPage } from '@/services/walletPageService'

// recharge/index.vue
import {
  confirmRechargePayment,
  createRechargePaymentOrder,
  fetchRechargePaymentOrder,
  fetchWalletBalance,
  redeemRechargePromoCode,
} from '@/services/walletPageService'
```

Replace call sites one-for-one, for example `getBookings(params)` becomes `fetchBookingsPage(params)` and `createRechargeOrder(payload)` becomes `createRechargePaymentOrder(payload)`.

- [ ] **Step 6: Run tests and build**

Run:

```bash
cd br-app
npm run test:refactor
npm run build:h5
```

Expected: both commands pass.

- [ ] **Step 7: Commit**

Run:

```bash
git add br-app/scripts/test-refactored-page-logic.js br-app/src/services/bookingPageService.js br-app/src/services/walletPageService.js br-app/src/pages/booking/confirm.vue br-app/src/pages/booking/detail.vue br-app/src/pages/orders/index.vue br-app/src/pages/wallet/transactions.vue br-app/src/pages/recharge/index.vue
git commit -m "refactor: add app page services"
```

## Task 5: Wire Shared Formatters into Oversized Pages

**Files:**
- Modify: `br-app/src/pages/index/index.vue`
- Modify: `br-app/src/pages/profile/index.vue`
- Modify: `br-app/src/pages/orders/index.vue`
- Modify: `br-app/src/pages/wallet/transactions.vue`
- Modify: `br-app/src/pages/recharge/index.vue`
- Modify: `br-app/src/pages/booking/confirm.vue`

- [ ] **Step 1: Replace local formatter implementations**

Import only the helpers each page uses:

```js
import { formatAmount, formatBookingStatus, formatHourDuration, formatMoney, formatRoomMinPrice, formatShortTime, formatWalletStatus } from '@/utils/formatters'
```

Then replace duplicated page methods:

```js
formatMoney,
formatAmount,
formatTime: formatShortTime,
statusLabel: formatBookingStatus,
statusText: formatWalletStatus,
roomPriceText: formatRoomMinPrice,
```

In `orders/index.vue`, replace duration body with:

```js
durationText(order) {
  return formatHourDuration(order.start_time, order.end_time)
}
```

- [ ] **Step 2: Run focused refactor tests**

Run: `cd br-app && npm run test:refactor`

Expected: PASS.

- [ ] **Step 3: Run existing script tests**

Run: `cd br-app && npm run test:scripts`

Expected: profile links, WeChat AppID, and refactor tests all pass.

- [ ] **Step 4: Run H5 build**

Run: `cd br-app && npm run build:h5`

Expected: build completes without Vite/uni-app errors.

- [ ] **Step 5: Commit**

Run:

```bash
git add br-app/src/pages/index/index.vue br-app/src/pages/profile/index.vue br-app/src/pages/orders/index.vue br-app/src/pages/wallet/transactions.vue br-app/src/pages/recharge/index.vue br-app/src/pages/booking/confirm.vue
git commit -m "refactor: use shared app formatters"
```

## Final Validation

- [ ] Run: `cd br-app && npm run test:scripts`
- [ ] Run: `cd br-app && npm run build:h5`
- [ ] Run: `git status --short`
- [ ] Confirm only intended `br-app` and plan files changed.

## Self-Review

- Spec coverage: constants, formatters, follow/unfollow study room logic, payment polling, and page-service API orchestration are each covered by dedicated tasks.
- Placeholder scan: no task uses TBD/TODO/fill-in language; each code-creation task includes concrete code.
- Type consistency: formatter, service, and polling function names are introduced before their page imports and reused consistently.
