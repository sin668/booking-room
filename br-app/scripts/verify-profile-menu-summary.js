const assert = require('assert')
const fs = require('fs')
const path = require('path')

const source = fs.readFileSync(path.resolve(__dirname, '../src/pages/profile/index.vue'), 'utf8')

const MENU_ROWS = [...source.matchAll(/<view class="menu-item"[\s\S]*?\n {8}<\/view>/g)].map((m) => m[0])

function menuRow(label) {
  const row = MENU_ROWS.find((item) => item.includes(`>${label}</text>`))
  assert.ok(row, `未找到「${label}」菜单行`)
  return row
}

// 三处右侧文案：评价条数、未读条数、充值引导
assert.ok(
  menuRow('我的评价').includes('<text class="menu-item-meta">{{ reviewSummary }}</text>'),
  '「我的评价」缺少右侧条数文案',
)
const messageRow = menuRow('我的消息')
assert.ok(messageRow.includes('@tap="navigateTo(\'/pages/notifications/index\')"'), '「我的消息」未绑定消息通知页跳转')
assert.ok(messageRow.includes('{{ unreadMessageSummary }}'), '「我的消息」缺少右侧未读文案')
assert.ok(/class="icon icon-bell/.test(messageRow), '「我的消息」缺少铃铛图标')
assert.ok(menuRow('钱包充值').includes('充值钱包'), '「钱包充值」缺少右侧引导文案')

// 数量为 0 时留空，不得显示「0条评论」「0条未读」
for (const [name, unit] of [['reviewSummary', '条评论'], ['unreadMessageSummary', '条未读']]) {
  const body = source.match(new RegExp(`${name}\\(\\)\\s*\\{([\\s\\S]*?)\\n {4}\\}`))
  assert.ok(body, `未找到 computed ${name}`)
  assert.ok(/> 0 \?/.test(body[1]), `${name} 缺少数量为 0 的留空判断`)
  assert.ok(body[1].includes(unit), `${name} 文案单位应为 ${unit}`)
}

/** 统计顶层元素个数；解构里的空洞 `[a, , b]` 与数组的尾随逗号都要算对 */
function countTopLevelItems(text) {
  const body = text.replace(/,\s*$/, '')
  if (body.trim() === '') return 0
  let depth = 0
  let commas = 0
  for (const ch of body) {
    if ('([{'.includes(ch)) depth += 1
    else if (')]}'.includes(ch)) depth -= 1
    else if (ch === ',' && depth === 0) commas += 1
  }
  return commas + 1
}

const statsMatch = source.match(/const \[([^\]]*)\] = await Promise\.allSettled\(\[([\s\S]*?)\n\s*\]\)/)
assert.ok(statsMatch, '未找到 loadProfileStats 的 Promise.allSettled')
const slots = countTopLevelItems(statsMatch[1])
const promises = countTopLevelItems(statsMatch[2])
assert.strictEqual(slots, promises, `Promise.allSettled 解构槽位数(${slots})与请求数(${promises})不一致`)
assert.ok(/getReviewList\(\{[^}]*mine: true[^}]*\}\)/.test(statsMatch[2]), '未并发请求「我的评价」列表')
assert.ok(statsMatch[2].includes('getNotificationUnreadSummary()'), '未并发请求未读消息汇总')

// 取数口径：评价用后端 total，未读用后端 total_unread，均不得由前端推算
assert.ok(/this\.reviewCount =[\s\S]*?reviewResult\.value\?\.total/.test(source), 'reviewCount 应取接口 total')
assert.ok(/this\.unreadMessageCount =[\s\S]*?unreadResult\.value\?\.total_unread/.test(source), 'unreadMessageCount 应取接口 total_unread')

console.log('profile 菜单统计文案验证通过')
