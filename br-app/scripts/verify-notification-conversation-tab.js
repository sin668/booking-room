const assert = require('assert')
const fs = require('fs')
const path = require('path')

const pagePath = path.resolve(__dirname, '../src/pages/notifications/index.vue')
const typesPath = path.resolve(__dirname, '../src/utils/notificationTypes.js')
const page = fs.readFileSync(pagePath, 'utf8')
const types = fs.readFileSync(typesPath, 'utf8')

// 1. 四类通知短标签
for (const [key, label] of [['booking', '预约'], ['activity', '活动'], ['report', '报告'], ['arrival', '到店']]) {
  const block = types.match(new RegExp(`key: '${key}',\\s*label: '([^']+)'`))
  assert.ok(block, `notificationTypes.js 缺少 ${key} 的 label`)
  assert.strictEqual(block[1], label, `${key} 标签应为「${label}」，实际「${block[1]}」`)
}
assert.ok(!/label: '预约提醒'|label: '活动通知'|label: '学习报告'|label: '到店提醒'/.test(types), '短标签未完全替换')
// 设置页偏好文案仍用全称，不受本次精简影响
assert.ok(/settingLabel: '预约提醒'/.test(types), 'settingLabel 全称应保留供设置页使用')

// 2. TAB 顺序：会话紧跟全部之后
const tabArray = page.match(/const tabs = \[([\s\S]*?)\n\]/)
assert.ok(tabArray, '未找到 tabs 定义')
assert.ok(
  /value: 'all'[\s\S]*?CONVERSATION_TAB/.test(tabArray[1]),
  '「会话」TAB 必须紧跟在「全部」之后',
)
assert.ok(/CONVERSATION_TAB = 'conversation'/.test(page), '未定义 CONVERSATION_TAB 常量')

// 3. 选中会话 TAB 时不得请求通知列表
const typeParam = page.match(/if \(currentType\.value !== 'all'([\s\S]*?)\)\s*\{\s*params\.type/)
assert.ok(typeParam, '未找到通知列表 type 参数判断')
assert.ok(
  /CONVERSATION_TAB/.test(typeParam[1]),
  '会话 TAB 是视图切换，不得把 conversation 作为通知类型请求后端',
)
assert.ok(
  /if \(type === CONVERSATION_TAB\) \{\s*\n\s*loadConversations\(\)/.test(page),
  '切换到会话 TAB 应加载会话列表而非通知列表',
)
assert.ok(
  /async function markAllRead\(\) \{\s*\n\s*if \(isConversationTab\.value\) return/.test(page),
  '会话 TAB 下不得把 conversation 作为通知类型批量标记已读',
)

// 4. 会话行：单行截断 + 未读徽标口径
assert.ok(/class="conv-summary"/.test(page), '缺少最新一条消息摘要节点')
for (const cls of ['conv-name', 'conv-summary']) {
  const rule = page.match(new RegExp(`\\.${cls} \\{([\\s\\S]*?)\\}`))
  assert.ok(rule, `缺少 .${cls} 样式`)
  assert.ok(/text-overflow: ellipsis/.test(rule[1]), `.${cls} 应单行截断加省略号`)
  assert.ok(/white-space: nowrap/.test(rule[1]), `.${cls} 不应换行`)
}
assert.ok(/v-if="item\.unreadCount > 0"/.test(page), '未读数为 0 时不应渲染徽标')
assert.ok(/unreadCount > 99 \? '99\+'/.test(page), '未读数超过 99 应显示 99+')

// 5. 点击会话复用既有 TUIChat 页面
assert.ok(
  /navigateTo\(\{\s*\n?\s*url: `\/TUIKit\/components\/TUIChat\/index\?conversationID=\$\{item\.conversationID\}`/.test(page),
  '点击会话应跳转已有 TUIChat 页面并带上 conversationID',
)

// 6. 订阅必须成对释放，且列表节点不得使用 backwards 动画（小程序端会不可见）
assert.ok(/TUIStore\.watch\(StoreName\.CONV/.test(page), '未订阅 TUIStore 会话列表')
assert.ok(
  /onUnmounted\(\(\) => \{[\s\S]*?TUIStore\.unwatch\(StoreName\.CONV/.test(page),
  '页面卸载时必须 unwatch 会话列表',
)
assert.ok(!/animation:[^;]*backwards/.test(page), '会话列表动画不得使用 backwards，否则小程序端不可见')

console.log('消息通知页「会话」TAB 验证通过')
