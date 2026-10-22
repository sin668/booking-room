const assert = require('assert')
const fs = require('fs')
const path = require('path')

const read = (rel) => fs.readFileSync(path.resolve(__dirname, '..', rel), 'utf8')

const im = read('src/utils/im.js')
const list = read('src/TUIKit/components/TUIChat/message-list/index.vue')

const fn = im.match(/async function loadChatMediaMap\([\s\S]*?\n\}/)
assert.ok(fn, '未找到 loadChatMediaMap')
const body = fn[0]

// 会话历史接口必须有界：回调落库有秒级延迟需要重试，但补不齐的历史媒体不能一直轮询
assert.ok(/const MEDIA_MAP_MAX_TRIES = \d+/.test(im), '缺少 MEDIA_MAP_MAX_TRIES 重试上限')
assert.ok(/mediaMapTries >= MEDIA_MAP_MAX_TRIES/.test(body), 'loadChatMediaMap 未检查重试上限')
assert.ok(
  body.indexOf('newestMediaTime <= mediaMapNewest') < body.indexOf('mediaMapTries >= MEDIA_MAP_MAX_TRIES'),
  '数据库已覆盖最新媒体时应先返回，不该继续重试',
)
// 出现更新的媒体要重新给重试机会，否则新发的图片/语音永远拿不到 OSS 地址
assert.ok(/mediaMapTries = 0/.test(body), '未按最新媒体时间重置重试计数')
// 最短间隔只在真正发请求前更新，切会话时重置全部缓存
assert.ok(/mediaMapAt = Date\.now\(\)\s*\n\s*mediaMapTries\+\+/.test(body), '节流时间戳与重试计数未成对更新')
assert.ok(
  im.includes("if (mediaMapKey !== conversationID) {") && /mediaMapNewest = 0\s*\n\s*mediaMapTarget = 0\s*\n\s*mediaMapTries = 0/.test(body),
  '切换会话未重置媒体映射缓存',
)

// 会话 ID 必须来自消息本身：切会话时列表可能先于 currentConversationID 更新
assert.ok(
  /loadChatMediaMap\(targets\[0\]\.message\.conversationID, newestMediaTime\)/.test(im),
  'applyChatMediaUrls 未从消息自身取 conversationID',
)
assert.ok(
  /export async function applyChatMediaUrls\(messageList\)/.test(im),
  'applyChatMediaUrls 不应再接收外部传入的 conversationID',
)
assert.ok(
  /applyChatMediaUrls\(\s*messageList\.value,?\s*\)/.test(list),
  'message-list 调用仍传入可能过期的 currentConversationID',
)

console.log('chat media map checks passed')
