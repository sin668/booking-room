// 深历史补齐的源码断言：数据库翻页入口存在、旧的「只为换媒体地址」的读取逻辑已删除、
// 聊天页只在 SDK 漫游到头后翻数据库，并且用不会上报已读的 unshift 注入。
const assert = require('assert')
const fs = require('fs')
const path = require('path')

function read(relative) {
  return fs.readFileSync(path.resolve(__dirname, '..', relative), 'utf8')
}

const im = read('src/utils/im.js')
assert.ok(
  !/applyChatMediaUrls|loadChatMediaMap|MEDIA_MAP_/.test(im),
  'im.js 仍残留只换媒体地址的数据库读取逻辑',
)
const fetchPage = im.match(/export async function fetchImHistoryPage\(([^)]*)\)/)
assert.ok(fetchPage, 'im.js 缺少 fetchImHistoryPage')
assert.strictEqual(fetchPage[1].replace(/\s+/g, ''), 'conversationID,before,limit=50')
// 本系统只落库单聊，群会话 ID 不能打到历史接口
assert.ok(/conversationID\.indexOf\('C2C'\)\s*!==\s*0/.test(im), 'fetchImHistoryPage 未排除群会话')
assert.ok(/before/.test(im.match(/getChatMessages\(conversationID\.slice\(3\), \{[^}]*\}\)/)[0]),
  'fetchImHistoryPage 未把游标传给接口')

const history = read('src/utils/im-history.js')
const typeMap = history.match(/const ELEMENT_TO_TYPE = \{([\s\S]*?)\n\}/)
assert.ok(typeMap, 'im-history.js 缺少类型映射表')
const types = [...typeMap[1].matchAll(/^\s*(\w+):/gm)].map(m => m[1])
assert.deepStrictEqual(types, ['text', 'image', 'sound', 'video', 'face', 'custom'], '可重建类型集合变化')
assert.ok(!/MSG_FILE/.test(typeMap[1]), '文件缺少 payload 契约，不应重建')
assert.ok(/function videoPayload/.test(history), '视频重建缺少 payload 构造函数')
// ID 用 MsgKey：与 SDK 消息不同源，靠游标分区就不会重复上屏
assert.ok(/ID:\s*row\.msg_key/.test(history), '重建消息未使用 MsgKey 作为 ID')
// 回调只落 SendMsgResult==0，历史消息一律是发送成功
assert.ok(/status:\s*'success'/.test(history), '重建消息未固定发送状态为 success')
assert.ok(/oss_url \|\|/.test(history), '媒体地址未优先使用转存后的 OSS 地址')
assert.ok(/isPeerRead: peerRead/.test(history), '重建消息未带上已读回执字段')
assert.ok(
  /const peerRead = from === myIMID \? !!row\.is_read : true/.test(history),
  '已读回执未按数据库 is_read 推导',
)
assert.ok(/readReceiptInfo: \{/.test(history), '重建消息缺少 readReceiptInfo 对象')

const list = read('src/TUIKit/components/TUIChat/message-list/index.vue')
assert.ok(!/applyChatMediaUrls/.test(list), '消息列表仍在调用已删除的媒体地址替换')
assert.ok(
  /TUIChatService\.updateMessageList\(messages as any,\s*'unshift'\)/.test(list),
  "深历史未通过 updateMessageList(..., 'unshift') 注入",
)
// SDK 窗口未到头时仍归 SDK 翻页，只有到头才转数据库
assert.ok(
  /if \(isCompleted\.value && !props\.isGroup\) \{[\s\S]*?loadDatabaseHistoryPage\(\)/.test(list),
  '未先判断 SDK 漫游是否到头',
)
assert.ok(
  /const earliestTime =[\s\S]*?cursor \|\|[\s\S]*?'messageList'\)\?\.\[0\]\?\.time/.test(list),
  '数据库游标未取当前最早一条消息的时间',
)
// 不再手点「查看更多」：顶部滚动自动加载 + 不足一屏自动续拉，铺满视口为止
assert.ok(!/@click="getHistoryMessageList"/.test(list), '消息列表仍残留手点「查看更多」按钮')
assert.ok(
  /scrollTop < 50 && canLoadMore && !isLoadingMessage\.value/.test(list),
  '滚动到顶部未自动加载更早历史',
)
assert.ok(
  /async function autoFillViewport\(\)/.test(list)
    && /nextTick\(\(\) => autoFillViewport\(\)\)/.test(list),
  '缺少不足一屏自动续拉逻辑',
)
// 前插历史不再用 scroll-into-view 锚旧首条：小程序原生 scroll-view 会在前插子节点布局前就执行
// scroll-into-view，锚到旧位置导致视口被前插内容顶到超一屏外。改用确定性的「高度差补偿 scroll-top」。
assert.ok(!/setAnchor\(oldFirst\)/.test(list), '前插仍用 scroll-into-view 锚旧首条，小程序会前跳超一屏')
assert.ok(/setAnchor\(newLast\)/.test(list), '末条变化（初次加载/新消息）仍应锚末条滚底')
assert.ok(
  /async function measureScroll\(\)/.test(list)
    && /getBoundingClientRect\('#messageScrollContent'/.test(list)
    && /getScrollInfo\('#messageScrollList'/.test(list),
  '缺少前插前后测量内容高度与滚动位置的 measureScroll',
)
assert.ok(
  /function anchorPrepend\(/.test(list)
    && /const delta = after\.height - before\.height/.test(list)
    && /before\.top \+ delta/.test(list),
  '缺少按高度差补偿 scroll-top 的 anchorPrepend（目标=原 scrollTop+高度差）',
)
// 两条加载路径都必须在渲染后接入补偿，而不是交给 watcher 同帧 scroll-into-view
assert.ok(
  /await TUIChatService\.getMessageList\(\)[\s\S]*?anchorPrepend\(before, after\)/.test(list),
  'SDK 翻页路径未接入前插高度差补偿',
)
assert.ok(
  /updateMessageList\(messages as any,\s*'unshift'\)[\s\S]*?anchorPrepend\(before, after\)/.test(list),
  '数据库深历史路径未接入前插高度差补偿',
)
// iOS/Skyline 原生 scroll-anchoring 作为免闪第一道防线（安卓 webview 由高度差补偿兜底）
assert.ok(/:scroll-anchoring="true"/.test(list), 'scroll-view 未开启原生 scroll-anchoring')
assert.ok(!/scrollTop\.value \+= 300/.test(list), '仍盲增 scroll-top，小程序会滚出内容外白屏')
assert.ok(/#messageScrollContent/.test(list), '缺少内容包裹层，小程序无法测内容高度做自动续拉')
const conversationSwitch = list.match(/const onCurrentConversationIDUpdated = \([^)]*\) => \{[\s\S]*?\n\};/)
assert.ok(conversationSwitch && /dbHasMore\.value = true/.test(conversationSwitch[0]), '切会话未重置数据库翻页状态')

console.log('im history rebuild checks passed')
