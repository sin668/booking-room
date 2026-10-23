const assert = require('assert')
const fs = require('fs')
const path = require('path')

const src = fs.readFileSync(
  path.resolve(__dirname, '..', 'src/TUIKit/components/TUIChat/index.vue'),
  'utf8',
)

// 引擎的自动已读只看 currentConversationID，页面隐藏时必须释放会话，否则对端秒收到已读上报
assert.ok(
  /import \{ onLoad, onShow, onHide, onUnload \} from '@dcloudio\/uni-app'/.test(src),
  "聊天页未引入 onShow/onHide 页面生命周期",
)

const hide = src.match(/onHide\(\(\) => \{[\s\S]*?\n\}\)/)
assert.ok(hide, '未找到 onHide 钩子')
assert.ok(/releasedOnHide = true/.test(hide[0]) && /reset\(\)/.test(hide[0]), 'onHide 未释放当前会话')
assert.ok(/if \(releasedOnHide\) return/.test(hide[0]), 'onHide 缺少重复触发保护')

const show = src.match(/onShow\(\(\) => \{[\s\S]*?\n\}\)/)
assert.ok(show, '未找到 onShow 钩子')
assert.ok(/if \(!releasedOnHide\) return/.test(show[0]), 'onShow 首次进入就重复绑定会话')
assert.ok(
  /initChat\(\{ conversationID: pageConversationID\.value \}\)/.test(show[0]),
  'onShow 未把会话重新绑回原 conversationID',
)

// 重新绑定必须用 onLoad 入参里的会话 ID，不能靠 store（切会话时可能仍是旧值）
const load = src.match(/onLoad\(\(options\) => \{[\s\S]*?\n\}\)/)
assert.ok(load, '未找到 onLoad 钩子')
assert.ok(
  /pageConversationID\.value = \(options && options\.conversationID\) \|\| ''/.test(load[0]),
  'onLoad 未记录本次打开的会话 ID',
)

// 离开页面仍然要释放（否则会话列表红点会被引擎抹成 0）
const unload = src.match(/onUnload\(\(\) => \{[\s\S]*?\n\}\)/)
assert.ok(unload && /reset\(\)/.test(unload[0]), 'onUnload 未释放当前会话')

console.log('chat read-on-visible checks passed')
