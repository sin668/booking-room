// IM 登录韧性验证：源码断言 + 对真实 im.js 注入 mock 做行为自检。
// 覆盖三条契约：①握手超时后等既有实例 SDK_READY 就绪而非放弃 ②离线快速失败不空等
// ③入口直接采纳已就绪实例（不重新取凭证/不新建 login）。运行：node scripts/verify-im-login.js
const assert = require('assert')
const fs = require('fs')
const path = require('path')
const vm = require('vm')

function read(relative) {
  return fs.readFileSync(path.resolve(__dirname, '..', relative), 'utf8')
}

// ---------- 源码断言 ----------
const im = read('src/utils/im.js')
assert.ok(/const SDK_READY_EVENT = 'sdkStateReady'/.test(im), 'im.js 缺少 SDK_READY 事件名')
assert.ok(/function waitChatReady\(chat, ms\)/.test(im), 'im.js 缺少等既有实例就绪的 waitChatReady')
assert.ok(/async function loginResilient\(/.test(im), 'im.js 缺少韧性登录 loginResilient')
assert.ok(
  /for \(let attempt = 0; attempt < LOGIN_MAX_ATTEMPTS; attempt\+\+\)/.test(im),
  'loginResilient 未做有限重试',
)
assert.ok(
  /if \(TUILogin\.getContext\(\)\?\.chat\?\.isReady\?\.\(\)\) return/.test(im),
  'loginResilient 未在入口复用已就绪实例，会重复 login 新建实例互相抢占',
)
assert.ok(
  /await waitChatReady\(chat, LOGIN_READY_TIMEOUT\)/.test(im),
  '握手超时后未等既有实例就绪（SDK 后台重连），仍单次硬超时放弃',
)
assert.ok(
  /\(await getNetworkType\(\)\) === 'none'/.test(im),
  '缺少离线快速失败，无网络时会空等满预算',
)
assert.ok(
  /const ctx = TUILogin\.getContext\(\)\s*\n\s*if \(ctx\?\.chat\?\.isReady\?\.\(\) && ctx\.SDKAppID && ctx\.userID && ctx\.userSig\)/.test(im),
  'ensureIM 入口未直接采纳上次超时被放弃但已就绪的实例',
)
assert.ok(
  !/withTimeout\(\s*TUILogin\.login\(\{[\s\S]*?\}\),\s*15000,\s*'IM登录'\s*\)/.test(im),
  'ensureIM 仍残留单次 login + 15s 硬超时的旧写法',
)

const entry = read('src/TUIKit/components/TUIChat/entry-chat-only.ts')
assert.ok(/import \{ ensureIM \} from '@\/utils\/im'/.test(entry), 'initChat 未引入 ensureIM 主动拉起登录')
assert.ok(/const CHAT_READY_TIMEOUT = 35000/.test(entry), 'initChat 就绪预算未与登录重试对齐（仍 5s 就放弃）')
assert.ok(!/maxRetries = 25/.test(entry), 'initChat 仍残留 5s 旧上限')
assert.ok(/chat\.on\?\.\(SDK_READY_EVENT, onReady\)/.test(entry), 'initChat 未事件驱动即时切会话')
assert.ok(/ensureIM\(\);/.test(entry), 'initChat 未就绪时未主动拉起登录')

// ---------- 行为自检：把真实 im.js 去 import/export 后在 vm 里注入 mock ----------
function loadIM(mocks) {
  let src = read('src/utils/im.js')
  src = src.replace(/^import[^\n]*\n/gm, '').replace(/^export /gm, '')
  const scale = 1000 // 把 15s 预算缩到 15ms，测试秒级跑完
  const context = {
    Promise, Error, Math, Date, Number, Object, String, Set, Map, Array, JSON,
    console: { warn() {}, error() {}, log() {} },
    setTimeout: (fn, ms) => setTimeout(fn, Math.max(1, ms / scale)),
    setInterval: (fn, ms) => setInterval(fn, Math.max(1, ms / scale)),
    clearTimeout, clearInterval,
    ...mocks,
  }
  vm.createContext(context)
  vm.runInContext(src, context)
  return context
}

function fakeChat(readyAfterMs) {
  const handlers = []
  let ready = readyAfterMs === 0
  const chat = {
    isReady: () => ready,
    on: (evt, fn) => { if (evt === 'sdkStateReady') handlers.push(fn) },
    off: (evt, fn) => {
      if (evt !== 'sdkStateReady') return
      const i = handlers.indexOf(fn); if (i >= 0) handlers.splice(i, 1)
    },
  }
  if (readyAfterMs > 0) {
    setTimeout(() => { ready = true; handlers.slice().forEach(fn => fn()) }, readyAfterMs)
  }
  return chat
}

async function main() {
  // ① 握手超时（login 永不 resolve），但实例 20ms 后就绪 → waitChatReady 采纳，ensureIM 成功
  {
    let loginCalls = 0
    const chat = fakeChat(20)
    const ctx = loadIM({
      uni: { getNetworkType: o => o.success({ networkType: 'wifi' }) },
      getChatUserSig: async () => ({ sdk_app_id: 1, user_id: 'u', user_sig: 's' }),
      getChatMessages: async () => ({ messages: [], has_more: false }),
      TUIGlobal: {},
      TUIUserService: { updateMyProfile: async () => {} },
      TUIChatEngine: { login() {} },
      TUILogin: {
        getContext: () => ({ chat, SDKAppID: 1, userID: 'u', userSig: 's' }),
        login: () => { loginCalls++; return new Promise(() => {}) },
      },
    })
    const ok = await ctx.ensureIM()
    assert.strictEqual(ok, true, '晚到就绪未被采纳，ensureIM 仍误报失败')
    assert.strictEqual(ctx.isIMReady(), true, '晚到就绪后 imInitialized 未置真')
    assert.strictEqual(loginCalls, 1, '晚到就绪路径不应重复 login 新建实例')
  }

  // ② 离线：login 永不 resolve、实例不就绪 → 握手超时后离线快失败，不空等满预算
  {
    const chat = fakeChat(-1) // 永不就绪
    const ctx = loadIM({
      uni: { getNetworkType: o => o.success({ networkType: 'none' }) },
      getChatUserSig: async () => ({ sdk_app_id: 1, user_id: 'u', user_sig: 's' }),
      getChatMessages: async () => ({ messages: [], has_more: false }),
      TUIGlobal: {},
      TUIUserService: { updateMyProfile: async () => {} },
      TUIChatEngine: { login() {} },
      TUILogin: {
        getContext: () => ({ chat, SDKAppID: 1, userID: 'u', userSig: 's' }),
        login: () => new Promise(() => {}),
      },
    })
    const ok = await ctx.ensureIM()
    assert.strictEqual(ok, false, '离线应失败')
    assert.ok(/网络不可用/.test(ctx.getIMLastError()), '离线未快速失败给出网络提示：' + ctx.getIMLastError())
  }

  // ③ 入口已就绪：直接采纳，不取凭证、不 login
  {
    let sigCalls = 0, loginCalls = 0
    const chat = fakeChat(0)
    const ctx = loadIM({
      uni: { getNetworkType: o => o.success({ networkType: 'wifi' }) },
      getChatUserSig: async () => { sigCalls++; return { sdk_app_id: 1, user_id: 'u', user_sig: 's' } },
      getChatMessages: async () => ({ messages: [], has_more: false }),
      TUIGlobal: {},
      TUIUserService: { updateMyProfile: async () => {} },
      TUIChatEngine: { login() {} },
      TUILogin: {
        getContext: () => ({ chat, SDKAppID: 1, userID: 'u', userSig: 's' }),
        login: () => { loginCalls++; return Promise.resolve() },
      },
    })
    const ok = await ctx.ensureIM()
    assert.strictEqual(ok, true, '已就绪实例应直接采纳')
    assert.strictEqual(sigCalls, 0, '已就绪时不应重新取凭证')
    assert.strictEqual(loginCalls, 0, '已就绪时不应再 login 新建实例')
  }

  console.log('verify-im-login: 源码断言 + 行为自检（晚到就绪/离线快失败/已就绪采纳）全部通过')
}

main().catch((e) => { console.error(e); process.exit(1) })