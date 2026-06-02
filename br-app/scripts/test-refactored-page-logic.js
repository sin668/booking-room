const assert = require('assert')
const fs = require('fs')
const path = require('path')
const vm = require('vm')

const appRoot = path.resolve(__dirname, '..')

function loadModule(relativePath, injected = {}, cache = {}) {
  const filename = path.join(appRoot, relativePath)
  if (cache[filename]) return cache[filename]

  let source = fs.readFileSync(filename, 'utf8')
  const exportedNames = []
  source = source.replace(/import\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"];?/g, (_match, names, request) => {
    return `const { ${names.trim()} } = __resolveImport(${JSON.stringify(request)})`
  })
  source = source.replace(/export\s+const\s+([A-Za-z0-9_$]+)\s*=/g, (_match, name) => {
    exportedNames.push(name)
    return `const ${name} =`
  })
  source = source.replace(/export\s+function\s+([A-Za-z0-9_$]+)\s*\(/g, (_match, name) => {
    exportedNames.push(name)
    return `function ${name}(`
  })
  source = source.replace(/export\s+async\s+function\s+([A-Za-z0-9_$]+)\s*\(/g, (_match, name) => {
    exportedNames.push(name)
    return `async function ${name}(`
  })
  source = source.replace(/export\s+\{([^}]+)\}/g, (_match, names) => {
    names.split(',').forEach((name) => {
      const trimmed = name.trim()
      if (trimmed) exportedNames.push(trimmed)
    })
    return ''
  })
  source += `\n${[...new Set(exportedNames)].map((name) => `exports.${name} = ${name}`).join('\n')}`

  const exports = {}
  cache[filename] = exports

  function resolveImport(request) {
    if (injected[request]) return injected[request]
    if (request.startsWith('@/')) {
      return loadModule(`src/${request.slice(2)}.js`, injected, cache)
    }
    throw new Error(`Unsupported test import: ${request}`)
  }

  const sandbox = {
    exports,
    console,
    setTimeout,
    clearTimeout,
    uni: global.uni,
    __resolveImport: resolveImport,
  }
  vm.runInNewContext(source, sandbox, { filename })
  return exports
}

function testFormatters() {
  const {
    formatMoney,
    formatAmount,
    formatShortTime,
    formatDateTime,
    formatDateSlash,
    formatRoomMinPrice,
    formatBookingStatus,
    formatWalletStatus,
    formatHourDuration,
    formatHourCount,
  } = loadModule('src/utils/formatters.js')

  assert.equal(formatMoney(12), '12.00')
  assert.equal(formatMoney(''), '0.00')
  assert.equal(formatAmount(12.5), '12.5')
  assert.equal(formatAmount('12.00'), '12')
  assert.equal(formatShortTime('2026-05-30T09:05:00'), '09:05')
  assert.equal(formatShortTime('09:30:00'), '09:30')
  assert.equal(formatDateTime('2026-05-30T09:05:00'), '2026-05-30 09:05')
  assert.equal(formatDateSlash('2026-05-30'), '2026/05/30')
  assert.equal(formatRoomMinPrice({ min_price: 8 }), '¥8起')
  assert.equal(formatRoomMinPrice({ min_price: 0 }), '')
  assert.equal(formatBookingStatus('confirmed'), '已预约')
  assert.equal(formatBookingStatus('unknown'), 'unknown')
  assert.equal(formatWalletStatus('completed'), '已完成')
  assert.equal(formatHourDuration('09:00', '11:30'), '2.5小时')
  assert.equal(formatHourCount('09:00', '11:30'), '2.5')
}

async function testFollowedRooms() {
  const storage = {}
  global.uni = {
    getStorageSync(key) {
      return storage[key]
    },
    setStorageSync(key, value) {
      storage[key] = value
    },
  }

  const service = loadModule('src/services/followedRooms.js', {
    '@/api/roomFollows': {
      persistFollowRoom: async (roomId) => ({ id: roomId, name: `持久化${roomId}`, min_price: 8 }),
      fetchPersistedFollowedRooms: async () => ({ items: [{ id: 9, name: '已入库自习室' }] }),
      persistUnfollowRoom: async () => ({}),
    },
  })
  await service.followRoom({ id: '7', name: '南门自习室', minPrice: 8, cityName: '茂名' })
  assert.equal(service.isRoomFollowed(7), true)
  assert.equal(service.getFollowedRooms()[0].min_price, 8)
  assert.equal(service.getFollowedRoomsSummary(service.getFollowedRooms()), '持久化7')
  await service.followRoom({ room_id: 8, name: '东门自习室' })
  assert.equal(service.getFollowedRoomsSummary(service.getFollowedRooms()), '持久化8等2家')
  await service.unfollowRoom(7)
  assert.deepEqual(service.getFollowedRooms().map((room) => room.id), [8])
  const syncedRooms = await service.syncFollowedRooms()
  assert.deepEqual(syncedRooms.map((room) => room.id), [9])
  delete global.uni
}

async function testPaymentPolling() {
  const service = loadModule('src/services/paymentPolling.js')

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
  assert.equal(typeof bookingService.createBookingOrder, 'function')
  assert.equal(typeof bookingService.fetchBookingPaymentStatus, 'function')
  assert.equal(typeof bookingService.fetchBookingRoom, 'function')
  assert.equal(typeof bookingService.fetchBookingSeats, 'function')
  assert.equal(typeof bookingService.fetchBookingCoupons, 'function')
  assert.equal(typeof bookingService.fetchWalletBalance, 'function')

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
  assert.equal(typeof walletService.fetchWalletBalance, 'function')
  assert.equal(typeof walletService.fetchWalletTransactionsPage, 'function')
  assert.equal(typeof walletService.createRechargePaymentOrder, 'function')
  assert.equal(typeof walletService.fetchRechargePaymentOrder, 'function')
  assert.equal(typeof walletService.confirmRechargePayment, 'function')
  assert.equal(typeof walletService.redeemRechargePromoCode, 'function')
}

async function main() {
  testFormatters()
  await testFollowedRooms()
  await testPaymentPolling()
  testPageServices()
  console.log('br-app refactored page logic tests passed')
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
