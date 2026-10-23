// 引擎级行为验证：数据库行重建出的消息能否被 TUIKit 直接渲染，以及深历史注入的三条契约
// —— 按 ID 去重、时间升序、不触发已读上报（unshift 分支不会 setMessageRead）。
// 运行：node scripts/verify-im-history-merge.mjs
import assert from 'node:assert'
import engine, { TUIChatService, TUIStore, StoreName } from '@tencentcloud/chat-uikit-engine-lite'
import { buildImHistoryMessages } from '../src/utils/im-history.js'

const readReports = []
// 跳过整套 login，引擎只需要能拿到 chat 实例
engine.chat = {
  isReady: () => true,
  on: () => {},
  off: () => {},
  setMessageRead: ({ conversationID }) => {
    readReports.push(conversationID)
    return Promise.resolve({ code: 0 })
  },
}

const CONVERSATION = 'C2Cpeer1'
const MY_IM = 'u-self'
const PEER_IM = 'u-peer'

const rows = [
  {
    msg_key: 'k-1',
    element_type: 'text',
    content: '早',
    im_from_account: PEER_IM,
    im_to_account: MY_IM,
    msg_time: 100,
    msg_seq: 3,
    is_revoked: false,
    is_read: false,
    elements: [{ MsgType: 'TIMTextElem', MsgContent: { Text: '早' } }],
  },
  {
    msg_key: 'k-2',
    element_type: 'image',
    media_url: 'https://im/original.jpg',
    oss_url: 'https://oss.example.com/original.jpg',
    im_from_account: MY_IM,
    im_to_account: PEER_IM,
    msg_time: 200,
    msg_seq: 7,
    is_revoked: true,
    revoke_time: 1700000000000,
    is_read: true,
    elements: [
      {
        MsgType: 'TIMImageElem',
        MsgContent: { ImageInfoArray: [{ Type: 1, URL: 'https://im/original.jpg', width: 100, height: 200 }] },
      },
    ],
  },
  {
    msg_key: 'k-3',
    element_type: 'sound',
    content: '3',
    media_url: 'https://im/a.mp3',
    im_from_account: PEER_IM,
    im_to_account: MY_IM,
    msg_time: 200,
    msg_seq: 9,
    is_read: true,
    elements: [{ MsgType: 'TIMSoundElem', MsgContent: { Url: 'https://im/a.mp3', Second: 3 } }],
  },
  {
    msg_key: 'k-4',
    element_type: 'custom',
    im_from_account: MY_IM,
    im_to_account: PEER_IM,
    msg_time: 300,
    msg_seq: 11,
    cloud_custom_data: '{"messageReply":{"messageId":"k-1"}}',
    elements: [{ MsgType: 'TIMCustomElem', MsgContent: { Data: '', Desc: '订单', Extension: 'order' } }],
  },
  // 未知类型不能重建：消息列表的 v-else 分支会把它们渲染成「撤回了一条消息」
  { msg_key: 'k-5', element_type: 'video', msg_time: 400, im_from_account: MY_IM },
  { msg_key: 'k-6', element_type: 'other', msg_time: 500, im_from_account: MY_IM },
]

const messages = buildImHistoryMessages(rows, {
  conversationID: CONVERSATION,
  myIMID: MY_IM,
  needReadReceipt: true,
  userInfo: {
    [MY_IM]: { nick: '我', avatar: 'https://oss/me.png' },
    [PEER_IM]: { nick: '对方', avatar: 'https://oss/peer.png' },
  },
})

// 1) 未知类型跳过，其余按 SDK 消息结构重建
assert.deepStrictEqual(
  messages.map(m => m.ID),
  ['k-1', 'k-2', 'k-3', 'k-4'],
  '重建结果应跳过不可识别的元素类型',
)
assert.strictEqual(messages[0].type, engine.TYPES.MSG_TEXT)
assert.strictEqual(messages[1].type, engine.TYPES.MSG_IMAGE)
assert.strictEqual(messages[2].type, engine.TYPES.MSG_AUDIO)
assert.strictEqual(messages[3].type, engine.TYPES.MSG_CUSTOM)

// 2) 收发方向、时间、序号取自数据库行，媒体优先走转存后的 OSS 地址
assert.strictEqual(messages[0].flow, 'in')
assert.strictEqual(messages[0].from, PEER_IM)
assert.strictEqual(messages[0].nick, '对方')
assert.strictEqual(messages[0].avatar, 'https://oss/peer.png')
assert.strictEqual(messages[1].flow, 'out')
assert.strictEqual(messages[1].status, 'success', '历史消息一律是发送成功')
assert.strictEqual(messages[1].payload.imageInfoArray[0].url, 'https://oss.example.com/original.jpg')
assert.strictEqual(messages[1].payload.imageInfoArray[0].width, 100)
// 没有转存成功时保持 IM 原地址，不阻塞渲染
assert.strictEqual(messages[2].payload.url, 'https://im/a.mp3')
assert.strictEqual(messages[2].payload.second, 3)
assert.strictEqual(messages[2].time, 200)
assert.strictEqual(messages[2].sequence, 9)

// 3) 撤回、引用与已读回执按落库状态还原
assert.strictEqual(messages[1].isRevoked, true)
assert.strictEqual(messages[0].isRevoked, false)
assert.strictEqual(messages[3].cloudCustomData, '{"messageReply":{"messageId":"k-1"}}')
assert.strictEqual(messages[3].payload.extension, 'order')
assert.strictEqual(messages[1].needReadReceipt, true)
assert.strictEqual(messages[1].readReceiptInfo.isPeerRead, true, '本端消息的已读回执取 is_read')
assert.strictEqual(messages[0].readReceiptInfo.isPeerRead, true)
// read-status 组件会解构 readReceiptInfo，缺对象直接抛异常，因此每条都得带上
for (const m of messages) {
  assert.ok(m.readReceiptInfo && typeof m.readReceiptInfo === 'object', `${m.ID} 缺少 readReceiptInfo`)
}

// 4) 注入引擎：按 ID 去重、时间升序、不上报已读
TUIStore.update(StoreName.CONV, 'currentConversationID', CONVERSATION)
TUIStore.update(StoreName.CHAT, 'messageList', [])
readReports.length = 0
TUIChatService.updateMessageList(
  [{ ID: 'sdk-9', conversationID: CONVERSATION, conversationType: 'C2C', type: engine.TYPES.MSG_TEXT, flow: 'in', time: 900, status: 'success', payload: { text: '漫游内' } }],
  'unshift',
)
TUIChatService.updateMessageList(messages, 'unshift')
TUIChatService.updateMessageList(messages, 'unshift')

const merged = TUIStore.getData(StoreName.CHAT, 'messageList')
assert.deepStrictEqual(
  merged.map(m => m.ID),
  ['k-1', 'k-2', 'k-3', 'k-4', 'sdk-9'],
  '重复注入应去重，且深历史前插、按时间升序',
)
assert.strictEqual(merged[1].getMessageContent().url, 'https://oss.example.com/original.jpg')
assert.deepStrictEqual(readReports, [], '注入历史消息不能触发已读上报')

// 5) 重建结果本身没有 SDK 消息实例，只带渲染需要的字段
assert.strictEqual(messages[0].isRevoked, false)
assert.strictEqual(typeof messages[0].revocationInfo, 'undefined')

console.log('im history rebuild + merge checks passed')
// 引擎内部有常驻定时器，不主动退出进程不会结束
process.exit(0)
