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
  /TUIChatService\.updateMessageList\(batch as any,\s*'unshift'\)/.test(list),
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
// 滚动统一用数值 scroll-top（原生 clamp 到最大滚动位置）。scroll-into-view 会把目标「顶部」
// 对齐视口顶部：锚旧首条会在前插时前跳超一屏，锚末条会在末条不足一屏时滚过内容末尾白屏。
assert.ok(!/:scroll-into-view=/.test(list), '仍绑定 scroll-into-view，锚末条会滚出内容外白屏')
assert.ok(!/setAnchor\(/.test(list), '仍残留 scroll-into-view 锚点机制')
// 滚底必须等渲染落定后量「内容总高 - 视口高」精确落到 maxScroll：盲设超大值赌原生 clamp，
// 会在与 resetMessageSource 重渲染同帧时按旧高度钳制滚出内容外，首点白屏、再点才正确。
assert.ok(
  /async function scrollToBottom\(\)/.test(list)
    && /await nextTick\(\)/.test(list)
    && /const nudge = bottomScrollSeq\+\+ % 2/.test(list)
    && /Math\.max\(0, ch - vh\) \+ nudge/.test(list)
    && /scrollTop\.value = target/.test(list),
  '滚底未等渲染落定后量真实 maxScroll 精确落底（同帧盲设超大值会按旧高度钳制滚出内容外白屏）',
)
assert.ok(
  /if \(!\(scrollButtonInstanceRef\.value\?\.isScrollButtonVisible && lastFlow === 'in'\)\) \{\s*scrollToBottom\(\)/.test(list),
  '末条变化（初次加载/新消息）未走数值滚底',
)
assert.ok(
  /async function measureScroll\(\)/.test(list)
    && /getBoundingClientRect\('#messageScrollContent'/.test(list)
    && /getScrollInfo\('#messageScrollList'/.test(list),
  '缺少前插前后测量内容高度与滚动位置的 measureScroll',
)
assert.ok(
  /function anchorPrepend\(/.test(list)
    && /const delta = afterHeight - before\.height/.test(list)
    && /before\.top \+ delta/.test(list),
  '缺少按高度差补偿 scroll-top 的 anchorPrepend（目标=原 scrollTop+高度差）',
)
// 渲染后只补测一次内容高（单查询），把兜底补偿过渡压到最短
assert.ok(
  /async function measureContentHeight\(\)/.test(list)
    && /const afterHeight = await measureContentHeight\(\)/.test(list),
  '前插后未用单查询 measureContentHeight 补测内容高',
)
// 两条加载路径都必须在渲染后接入补偿，而不是交给 watcher 同帧 scroll-into-view
assert.ok(
  /await TUIChatService\.getMessageList\(\)[\s\S]*?anchorPrepend\(before, afterHeight\)/.test(list),
  'SDK 翻页路径未接入前插高度差补偿',
)
// 数据库深历史路径：插入前离屏镜像预测量批次高度，再原子前插（前插+scroll-top 同一次 setData），
// 第一帧即定位正确，彻底消除「先画错位帧再拉回」的过渡
assert.ok(
  /async function measureBatchHeight\(/.test(list)
    && /measureMessages\.value = batch/.test(list)
    && /getBoundingClientRect\('#measureMirror'/.test(list),
  '缺少插入前的离屏镜像预测量 measureBatchHeight',
)
assert.ok(
  /id="measureMirror"/.test(list) && /v-for="\(item, index\) in measureMessages"/.test(list),
  '缺少离屏镜像容器或其批次渲染',
)
assert.ok(
  /function commitPrepend\(/.test(list)
    && /scrollTop\.value = before\.height <= before\.vp \+ 10[\s\S]*?before\.top \+ delta/.test(list)
    && /measureMessages\.value = \[\][\s\S]*?TUIChatService\.updateMessageList\(batch as any,\s*'unshift'\)/.test(list),
  'commitPrepend 未在同一次 flush 内先设 scroll-top 再清镜像并前插（原子前插）',
)
assert.ok(
  /const delta = await measureBatchHeight\(messages\)[\s\S]*?commitPrepend\(messages, before, delta\)[\s\S]*?await verifyPrepend\(before, delta\)/.test(list),
  '数据库深历史路径未走「预测量→原子前插→安全网」流程',
)
// 安全网仅在真实位置明显偏离时微调，原子前插到位则不动（无额外绘制）
assert.ok(
  /async function verifyPrepend\(/.test(list) && /Math\.abs\(\(actualTop \|\| 0\) - ideal\) > 40/.test(list),
  '缺少原子前插后的位置校验安全网 verifyPrepend',
)
// spinner 移出内容流改为覆盖层，前插高度差核算不受其干扰
assert.ok(
  /class="message-loading-overlay"/.test(list) && !/class="message-more message-loading"/.test(list),
  '加载指示仍在内容流内，会干扰前插高度差核算',
)
// iOS/Skyline 原生 scroll-anchoring 作为免闪第一道防线
assert.ok(/:scroll-anchoring="true"/.test(list), 'scroll-view 未开启原生 scroll-anchoring')
// 安卓 webview：开启内部滚动容器的 overflow-anchor，让浏览器原生锚定原子接管前插，消除先跳后拉回
assert.ok(
  /overflow-anchor: auto !important/.test(list)
    && /:deep\(\.wx-scroll-view\)/.test(list),
  '未覆盖 scroll-view 内部滚动容器的 overflow-anchor，安卓前插仍会先跳后拉回',
)
assert.ok(!/scrollTop\.value \+= 300/.test(list), '仍盲增 scroll-top，小程序会滚出内容外白屏')
assert.ok(/#messageScrollContent/.test(list), '缺少内容包裹层，小程序无法测内容高度做自动续拉')
const conversationSwitch = list.match(/const onCurrentConversationIDUpdated = \([^)]*\) => \{[\s\S]*?\n\};/)
assert.ok(conversationSwitch && /dbHasMore\.value = true/.test(conversationSwitch[0]), '切会话未重置数据库翻页状态')

console.log('im history rebuild checks passed')
