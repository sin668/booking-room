// 引擎级行为验证：自动已读上报只取决于 currentConversationID，与聊天页是否可见无关。
// 这就是聊天页 onHide 必须释放会话的原因，也是 verify-chat-read-on-visible.js 那套源码断言的行为依据。
// 运行：node scripts/verify-chat-read-gate.mjs
import TUIChatEngine, {
  TUIChatService,
  TUIStore,
  StoreName,
} from '@tencentcloud/chat-uikit-engine-lite'
import assert from 'node:assert'

const readReports = []
const fakeChat = {
  isReady: () => true,
  on: () => {},
  off: () => {},
  setMessageRead: ({ conversationID }) => {
    readReports.push(conversationID)
    return Promise.resolve({ code: 0 })
  },
}
// 跳过 login 的整套 init，引擎只需要能拿到 chat 实例
TUIChatEngine.chat = fakeChat

const message = {
  ID: 'msg-1',
  conversationID: 'C2Cpeer1',
  flow: 'in',
  type: 'TIMTextElem',
  time: 1,
  payload: { text: 'hello' },
}

function feed() {
  readReports.length = 0
  TUIStore.update(StoreName.CHAT, 'messageList', [])
  TUIChatService.updateMessageList([message], 'received')
}

assert.strictEqual(
  TUIStore.getData(StoreName.APP, 'enableAutoMessageRead'),
  true,
  '引擎默认自动已读应为 true',
)

// 1) 会话被绑定（用户停在聊天页）→ 收到消息立刻上报已读
TUIStore.update(StoreName.CONV, 'currentConversationID', 'C2Cpeer1')
feed()
assert.deepStrictEqual(readReports, ['C2Cpeer1'], '会话绑定时引擎应自动上报已读')

// 2) 会话已释放（聊天页 onHide 的效果）→ 同一条消息到达时不能再上报已读
TUIStore.update(StoreName.CONV, 'currentConversationID', '')
feed()
assert.deepStrictEqual(readReports, [], '释放会话后引擎不应上报已读')

// 3) 停在别的会话 → 同样不该被上报
TUIStore.update(StoreName.CONV, 'currentConversationID', 'C2Cother')
feed()
assert.deepStrictEqual(readReports, [], '非当前会话的消息不应触发已读上报')

console.log('chat read gate checks passed')
// 引擎内部有常驻定时器，不主动退出进程不会结束
process.exit(0)
