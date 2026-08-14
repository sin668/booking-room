const fs = require('fs')
const path = require('path')

const trainingApiPath = path.resolve(__dirname, '../src/api/training.js')
const source = fs.readFileSync(trainingApiPath, 'utf8')

// 1. Verify getTrainingRoomDetail is exported
const exportMatch = source.match(/export\s+function\s+getTrainingRoomDetail\s*\(/)
if (!exportMatch) {
  throw new Error('getTrainingRoomDetail 未导出')
}
console.log('✓ getTrainingRoomDetail 已导出')

// 2. Verify it accepts roomId parameter
const paramMatch = source.match(/export\s+function\s+getTrainingRoomDetail\s*\(\s*roomId\s*\)/)
if (!paramMatch) {
  throw new Error('getTrainingRoomDetail 缺少 roomId 参数')
}
console.log('✓ getTrainingRoomDetail 接受 roomId 参数')

// 3. Verify URL pattern - must NOT have trailing slash (BUG-22 protection)
const urlMatch = source.match(/get\(`\/api\/v1\/training\/rooms\/\$\{roomId\}`\)/)
if (!urlMatch) {
  throw new Error('getTrainingRoomDetail URL 模式不正确')
}
console.log('✓ URL 路径正确: /api/v1/training/rooms/${roomId}')

// 4. Verify NO trailing slash (BUG-22)
if (source.includes('/api/v1/training/rooms/${roomId}/')) {
  throw new Error('BUG-22: URL 使用了尾部斜杠')
}
console.log('✓ BUG-22 防护: URL 无尾部斜杠')

// 5. Verify it calls get() function
const getCallMatch = source.match(/return\s+get\(`/)
if (!getCallMatch) {
  throw new Error('getTrainingRoomDetail 未调用 get()')
}
console.log('✓ 使用 get() 方法发起请求')

console.log('\n所有验证通过')
