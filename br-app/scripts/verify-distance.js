const assert = require('assert')
const fs = require('fs')
const path = require('path')
const vm = require('vm')

const sourcePath = path.resolve(__dirname, '../src/utils/distance.js')
const source = fs
  .readFileSync(sourcePath, 'utf8')
  .replace(/export\s+function\s+/g, 'function ')

const sandbox = { module: { exports: {} }, console }
vm.createContext(sandbox)
vm.runInContext(
  `${source}\nmodule.exports = { haversineDistance, formatDistance }`,
  sandbox
)
const { haversineDistance, formatDistance } = sandbox.module.exports

const zero = haversineDistance(39.9042, 116.4074, 39.9042, 116.4074)
assert.strictEqual(zero, 0, '同一点距离应为 0')

const beijingToShanghai = haversineDistance(39.9042, 116.4074, 31.2304, 121.4737)
assert.ok(
  beijingToShanghai > 1030000 && beijingToShanghai < 1100000,
  `北京到上海直线距离应约 1067km，实际 ${beijingToShanghai}`
)

assert.strictEqual(haversineDistance(null, 116.4, 39.9, 116.4), null, '空坐标应返回 null')
assert.strictEqual(haversineDistance('abc', 116.4, 39.9, 116.4), null, '非法坐标应返回 null')

assert.strictEqual(formatDistance(500), '距您约500m')
assert.strictEqual(formatDistance(1200), '距您约1.2km')
assert.strictEqual(formatDistance(null), '')
assert.strictEqual(formatDistance(-1), '')

console.log('distance self-check passed')
