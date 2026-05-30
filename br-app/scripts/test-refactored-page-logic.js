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
