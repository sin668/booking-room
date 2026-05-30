# br-app 页面逻辑重构实施计划

> **给 agentic workers 的要求：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 逐项执行本计划。执行进度使用 checkbox（`- [ ]`）跟踪。

**目标：** 重构 `br-app` 中过大的页面文件，让页面只保留展示逻辑和事件编排，把共享的 API 调用、价格/时间/状态格式化、关注门店、支付轮询逻辑拆到独立模块。

**架构：** 先抽取纯函数格式化器和常量，随后把存储与 API 编排封装到 page service 和可复用服务中。页面模板和样式尽量不动，除非绑定名必须调整，从而保证每个任务的行为影响面都较小并且容易验证。

**技术栈：** Vue 3、uni-app、现有 `src/api/*` 模块、Node 脚本测试、`npm run build:h5`。

---

## 文件结构

- 新建 `br-app/src/constants/booking.js`：预约状态文案、座位分区文案、预约页签等常量。
- 新建 `br-app/src/constants/wallet.js`：钱包交易状态文案、充值金额边界、支付轮询状态常量。
- 新建 `br-app/src/utils/formatters.js`：金额、充值金额、日期、时间、时长、门店起价、预约状态、钱包状态等纯格式化函数。
- 新建 `br-app/src/services/followedRooms.js`：封装关注门店的本地存储、门店数据归一化、关注摘要。
- 修改 `br-app/src/utils/followedRooms.js`：作为兼容层重新导出 service，避免一次性改动所有老引用导致风险扩大。
- 新建 `br-app/src/services/paymentPolling.js`：共享预约支付和钱包充值的异步轮询逻辑。
- 新建 `br-app/src/services/bookingPageService.js`：预约相关页面使用的 API 编排层。
- 新建 `br-app/src/services/walletPageService.js`：钱包和充值页面使用的 API 编排层。
- 新建 `br-app/scripts/test-refactored-page-logic.js`：针对抽取出的纯函数和 service 的 Node 脚本测试。
- 修改 `br-app/package.json`：新增 `test:refactor` 与 `test:scripts`。
- 修改以下页面，只替换逻辑导入和调用，模板/样式非必要不动：
  - `br-app/src/pages/index/index.vue`
  - `br-app/src/pages/profile/index.vue`
  - `br-app/src/pages/booking/detail.vue`
  - `br-app/src/pages/booking/confirm.vue`
  - `br-app/src/pages/orders/index.vue`
  - `br-app/src/pages/wallet/transactions.vue`
  - `br-app/src/pages/recharge/index.vue`

## Task 1：共享格式化器与常量

**文件：**
- 新建：`br-app/src/constants/booking.js`
- 新建：`br-app/src/constants/wallet.js`
- 新建：`br-app/src/utils/formatters.js`
- 新建：`br-app/scripts/test-refactored-page-logic.js`
- 修改：`br-app/package.json`

- [x] **Step 1：先写失败的格式化器测试**

新增 `br-app/scripts/test-refactored-page-logic.js`。测试脚本使用 Node `vm` 加载 ES module 风格源码，并验证：

```js
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
```

`package.json` 增加：

```json
"test:refactor": "node scripts/test-refactored-page-logic.js",
"test:scripts": "npm run test:profile-links && npm run test:wechat-appid && npm run test:refactor"
```

- [x] **Step 2：运行测试并确认失败**

运行：`cd br-app && npm run test:refactor`

预期：失败，提示 `src/utils/formatters.js` 不存在。

- [x] **Step 3：实现常量和格式化器**

`booking.js` 导出 `BOOKING_TABS`、`BOOKING_STATUS_LABELS`、`SEAT_ZONE_LABELS`。

`wallet.js` 导出 `WALLET_TRANSACTION_STATUS_LABELS`、`RECHARGE_DEFAULT_AMOUNT`、`RECHARGE_MIN_AMOUNT`、`RECHARGE_MAX_AMOUNT`、`PAYMENT_POLL_INTERVAL`、`PAYMENT_POLL_MAX_ATTEMPTS`、`PAYMENT_TERMINAL_FAILURE_STATUSES`。

`formatters.js` 导出：

```js
formatMoney(value)
formatAmount(value)
formatShortTime(value)
formatDateSlash(value)
formatRoomMinPrice(room)
formatBookingStatus(status)
formatWalletStatus(status)
formatSeatZone(zone)
formatHourDuration(startTime, endTime)
```

- [x] **Step 4：运行测试并确认通过**

运行：`cd br-app && npm run test:refactor`

预期：通过，输出 `br-app refactored page logic tests passed`。

- [x] **Step 5：提交**

已提交：

```bash
git commit -m "refactor: add app formatter constants"
```

## Task 2：关注门店服务

**文件：**
- 新建：`br-app/src/services/followedRooms.js`
- 修改：`br-app/src/utils/followedRooms.js`
- 修改：`br-app/src/pages/index/index.vue`
- 修改：`br-app/src/pages/profile/index.vue`
- 修改：`br-app/src/pages/booking/detail.vue`
- 修改：`br-app/scripts/test-refactored-page-logic.js`

- [x] **Step 1：先写失败的关注门店服务测试**

在 `test-refactored-page-logic.js` 中新增 `testFollowedRooms()`，用 fake `uni` storage 验证归一化、关注、取消关注、摘要：

```js
service.followRoom({ id: '7', name: '南门店', minPrice: 8, cityName: '茂名' })
assert.equal(service.isRoomFollowed(7), true)
assert.equal(service.getFollowedRooms()[0].min_price, 8)
assert.equal(service.getFollowedRoomsSummary(service.getFollowedRooms()), '南门店')
service.followRoom({ room_id: 8, name: '东门店' })
assert.equal(service.getFollowedRoomsSummary(service.getFollowedRooms()), '东门店等2家')
service.unfollowRoom(7)
assert.deepEqual(service.getFollowedRooms().map((room) => room.id), [8])
```

- [x] **Step 2：运行测试并确认失败**

运行：`cd br-app && npm run test:refactor`

预期：失败，提示 `src/services/followedRooms.js` 不存在。

- [x] **Step 3：实现 service 与兼容 re-export**

新建 `br-app/src/services/followedRooms.js`，导出：

```js
FOLLOWED_ROOMS_STORAGE_KEY
normalizeRoom(room)
getFollowedRooms()
isRoomFollowed(roomId)
followRoom(room)
unfollowRoom(roomId)
getFollowedRoomsSummary(rooms)
```

修改 `br-app/src/utils/followedRooms.js` 为从 `@/services/followedRooms` 重新导出同名 API。

- [x] **Step 4：把页面导入切到 service**

更新：

```js
import { getFollowedRooms } from '@/services/followedRooms'
import { followRoom, isRoomFollowed, unfollowRoom } from '@/services/followedRooms'
import { getFollowedRooms, getFollowedRoomsSummary } from '@/services/followedRooms'
```

`profile/index.vue` 中关注摘要改为：

```js
followedRoomsSummary() {
  return getFollowedRoomsSummary(this.followedRooms)
}
```

- [x] **Step 5：运行测试和构建**

运行：

```bash
cd br-app
npm run test:refactor
npm run build:h5
```

预期：全部通过。

- [x] **Step 6：提交**

```bash
git add br-app/scripts/test-refactored-page-logic.js br-app/src/services/followedRooms.js br-app/src/utils/followedRooms.js br-app/src/pages/index/index.vue br-app/src/pages/profile/index.vue br-app/src/pages/booking/detail.vue
git commit -m "refactor: extract followed room service"
```

## Task 3：共享支付轮询

**文件：**
- 新建：`br-app/src/services/paymentPolling.js`
- 修改：`br-app/src/pages/booking/confirm.vue`
- 修改：`br-app/src/pages/recharge/index.vue`
- 修改：`br-app/scripts/test-refactored-page-logic.js`

- [x] **Step 1：先写失败的支付轮询测试**

在测试脚本中新增 `testPaymentPolling()`，验证成功状态返回原结果，失败状态抛出带 `paymentStatus` 的错误：

```js
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
```

- [x] **Step 2：运行测试并确认失败**

运行：`cd br-app && npm run test:refactor`

预期：失败，提示 `src/services/paymentPolling.js` 不存在。

- [x] **Step 3：实现支付轮询 service**

新建 `br-app/src/services/paymentPolling.js`，导出：

```js
createPaymentStatusError(status)
getPaymentStatus(response)
waitForPaymentPoll(ms)
pollPaymentStatus({ fetchStatus, isSuccess, failureStatuses, maxAttempts, wait })
```

轮询规则：
- `payment_status`、`paymentStatus`、`status` 都可作为状态来源。
- `isSuccess(status, result)` 为真时返回原始结果。
- `failed`、`cancelled`、`closed` 直接抛出 `paymentStatus` 错误。
- 超过最大次数抛出 `paymentStatus === 'timeout'`。

- [x] **Step 4：替换预约确认页轮询**

`booking/confirm.vue` 改为从 `@/services/paymentPolling` 导入：

```js
createPaymentStatusError
pollPaymentStatus
waitForPaymentPoll
```

本地 `pollBookingPaymentStatus` 委托给共享 `pollPaymentStatus`。

- [x] **Step 5：替换充值页轮询**

`recharge/index.vue` 改为从 `@/services/paymentPolling` 导入同样的三个 API。本地 `pollRechargeOrder` 委托给共享 `pollPaymentStatus`。

- [x] **Step 6：运行测试和构建**

运行：

```bash
cd br-app
npm run test:refactor
npm run build:h5
```

预期：全部通过。

- [x] **Step 7：提交**

```bash
git add br-app/scripts/test-refactored-page-logic.js br-app/src/services/paymentPolling.js br-app/src/pages/booking/confirm.vue br-app/src/pages/recharge/index.vue
git commit -m "refactor: share payment polling logic"
```

## Task 4：预约和钱包 Page Service

**文件：**
- 新建：`br-app/src/services/bookingPageService.js`
- 新建：`br-app/src/services/walletPageService.js`
- 修改：`br-app/src/pages/booking/confirm.vue`
- 修改：`br-app/src/pages/booking/detail.vue`
- 修改：`br-app/src/pages/orders/index.vue`
- 修改：`br-app/src/pages/wallet/transactions.vue`
- 修改：`br-app/src/pages/recharge/index.vue`

- [x] **Step 1：先写失败的 page service smoke test**

在测试脚本中注入 fake API，验证以下函数存在并可被加载：

```js
bookingService.fetchBookingsPage
bookingService.cancelBookingOrder
bookingService.createBookingOrder
bookingService.fetchBookingPaymentStatus
bookingService.fetchBookingRoom
bookingService.fetchBookingSeats
bookingService.fetchBookingCoupons
bookingService.fetchWalletBalance

walletService.fetchWalletBalance
walletService.fetchWalletTransactionsPage
walletService.createRechargePaymentOrder
walletService.fetchRechargePaymentOrder
walletService.confirmRechargePayment
walletService.redeemRechargePromoCode
```

- [x] **Step 2：运行测试并确认失败**

运行：`cd br-app && npm run test:refactor`

预期：失败，提示 `src/services/bookingPageService.js` 不存在。

- [x] **Step 3：实现预约 page service**

新建 `br-app/src/services/bookingPageService.js`，封装并导出：

```js
fetchBookingsPage(params)
cancelBookingOrder(id)
createBookingOrder(payload)
fetchBookingPaymentStatus(bookingId)
fetchBookingRoom(roomId)
fetchBookingSeats(roomId, params)
fetchBookingCoupons(payload)
fetchWalletBalance()
```

- [x] **Step 4：实现钱包 page service**

新建 `br-app/src/services/walletPageService.js`，封装并导出：

```js
fetchWalletBalance()
fetchWalletTransactionsPage(params)
createRechargePaymentOrder(payload)
fetchRechargePaymentOrder(orderId)
confirmRechargePayment(orderId)
redeemRechargePromoCode(code)
```

- [x] **Step 5：页面 API 导入改为 page service**

逐页替换：

```js
// booking/confirm.vue
createBookingOrder
fetchBookingCoupons
fetchBookingPaymentStatus
fetchBookingRoom
fetchBookingSeats
fetchWalletBalance

// booking/detail.vue
fetchBookingRoom

// orders/index.vue
cancelBookingOrder
fetchBookingsPage

// wallet/transactions.vue
fetchWalletBalance
fetchWalletTransactionsPage

// recharge/index.vue
confirmRechargePayment
createRechargePaymentOrder
fetchRechargePaymentOrder
fetchWalletBalance
redeemRechargePromoCode
```

- [x] **Step 6：运行测试和构建**

运行：

```bash
cd br-app
npm run test:refactor
npm run build:h5
```

预期：全部通过。

- [x] **Step 7：提交**

```bash
git add br-app/scripts/test-refactored-page-logic.js br-app/src/services/bookingPageService.js br-app/src/services/walletPageService.js br-app/src/pages/booking/confirm.vue br-app/src/pages/booking/detail.vue br-app/src/pages/orders/index.vue br-app/src/pages/wallet/transactions.vue br-app/src/pages/recharge/index.vue
git commit -m "refactor: add app page services"
```

## Task 5：把共享格式化器接入过大页面

**文件：**
- 修改：`br-app/src/pages/index/index.vue`
- 修改：`br-app/src/pages/profile/index.vue`
- 修改：`br-app/src/pages/orders/index.vue`
- 修改：`br-app/src/pages/wallet/transactions.vue`
- 修改：`br-app/src/pages/recharge/index.vue`
- 修改：`br-app/src/pages/booking/confirm.vue`

- [x] **Step 1：替换页面内重复格式化方法**

按页面实际需要导入：

```js
import {
  formatAmount,
  formatBookingStatus,
  formatHourDuration,
  formatMoney,
  formatRoomMinPrice,
  formatShortTime,
  formatWalletStatus,
} from '@/utils/formatters'
```

替换页面内重复方法：

```js
formatMoney,
formatAmount,
formatTime: formatShortTime,
statusLabel: formatBookingStatus,
statusText: formatWalletStatus,
roomPriceText: formatRoomMinPrice,
```

`orders/index.vue` 的时长展示改为：

```js
durationText(order) {
  return formatHourDuration(order.start_time, order.end_time)
}
```

- [x] **Step 2：运行 refactor 测试**

运行：`cd br-app && npm run test:refactor`

预期：通过。

- [x] **Step 3：运行现有脚本测试**

运行：`cd br-app && npm run test:scripts`

预期：profile links、WeChat AppID、refactor tests 全部通过。

- [x] **Step 4：运行 H5 构建**

运行：`cd br-app && npm run build:h5`

预期：构建无 Vite/uni-app 错误。

- [x] **Step 5：提交**

```bash
git add br-app/src/pages/index/index.vue br-app/src/pages/profile/index.vue br-app/src/pages/orders/index.vue br-app/src/pages/wallet/transactions.vue br-app/src/pages/recharge/index.vue br-app/src/pages/booking/confirm.vue
git commit -m "refactor: use shared app formatters"
```

## 最终验证

- [x] 运行：`cd br-app && npm run test:scripts`
- [x] 运行：`cd br-app && npm run build:h5`
- [x] 运行：`git status --short`
- [x] 确认只包含预期的 `br-app` 和计划文档相关变更。

## 自检

- 需求覆盖：常量、格式化器、关注/取消关注门店、支付轮询、页面 API 编排均有独立任务覆盖。
- 占位符扫描：文档中没有 TBD、TODO、fill in later 等占位说明。
- 类型一致性：计划中定义的 formatter、service、polling 函数名与后续页面导入名保持一致。
