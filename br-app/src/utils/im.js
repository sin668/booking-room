import { getChatMessages, getChatUserSig } from '@/api/chat'
import { TUILogin } from '@tencentcloud/tui-core-lite'
import { TUIGlobal } from '@tencentcloud/universal-api'
import TUIChatEngine, { TUIUserService } from '@tencentcloud/chat-uikit-engine-lite'

let imInitialized = false
let initPromise = null
let imProfile = null
let lastError = ''
let lastUploadError = null

// SDK 的上传失败分支只把 statusCode/data 拼进错误对象，wx 的 errMsg 和 URL 被整个丢掉，
// 线上表现为 `Unknown failed. error: {"message": }`，看不出是哪个域名没过白名单。
export function getIMLastUploadError() {
  return lastUploadError
}

function hookUploadDiagnostic() {
  if (!TUIGlobal?.uploadFile || TUIGlobal.__imUploadHooked) return
  TUIGlobal.__imUploadHooked = true
  const raw = TUIGlobal.uploadFile.bind(TUIGlobal)
  TUIGlobal.uploadFile = (options = {}) => {
    // 每次发起上传都清空，保证读到的一定属于这一次尝试
    lastUploadError = null
    return raw({
      ...options,
      fail: (e) => {
        lastUploadError = { url: options.url || '', errMsg: e?.errMsg || String(e) }
        console.error('[IM] uploadFile fail:', lastUploadError)
        options.fail?.(e)
      },
    })
  }
}

export function getIMLastError() {
  return lastError
}

function withTimeout(promise, ms, label) {
  return Promise.race([
    promise,
    new Promise((_, reject) => setTimeout(() => reject(new Error(`${label}超时(${ms}ms)`)), ms)),
  ])
}

async function pushIMProfile() {
  if (!imProfile) return
  const payload = {}
  if (imProfile.nick) payload.nick = imProfile.nick
  payload.avatar = imProfile.avatar || ''
  if (!payload.nick && !imProfile.avatar) return
  try {
    await TUIUserService.updateMyProfile(payload)
  } catch (e) {
    console.warn('IM profile sync failed:', e)
  }
}

export function setIMProfile(profile) {
  imProfile = profile
  if (imInitialized) pushIMProfile()
}

// IM 登录韧性：TUILogin.login 每次都新建 chat 实例，且要到 SDK_READY 事件才 resolve；
// SDK 自带断线/网络重连，握手超时不代表登录失败——实例往往几秒后就就绪。旧实现单次 login
// + 15s 硬超时就放弃，既误报「IM登录超时(15000ms)」，又丢弃了即将就绪的实例，下次进入再
// login 会新建实例互相抢占。改为：超时后等既有实例就绪、入口复用已就绪实例、实例始终不
// 就绪才有限重试，离线时快速失败不空等。
const SDK_READY_EVENT = 'sdkStateReady'
const LOGIN_HANDSHAKE_TIMEOUT = 15000
const LOGIN_READY_TIMEOUT = 15000
const LOGIN_MAX_ATTEMPTS = 2

function getNetworkType() {
  return new Promise((resolve) => {
    try {
      uni.getNetworkType({
        success: r => resolve(r?.networkType || 'unknown'),
        fail: () => resolve('unknown'),
      })
    } catch {
      resolve('unknown')
    }
  })
}

// 等 chat 实例就绪：SDK_READY 事件优先，isReady 轮询兜底（事件可能在订阅前已触发）
function waitChatReady(chat, ms) {
  return new Promise((resolve, reject) => {
    if (chat?.isReady?.()) { resolve(); return }
    let settled = false
    const onReady = () => finish()
    const finish = (err) => {
      if (settled) return
      settled = true
      clearTimeout(timer)
      clearInterval(poll)
      chat?.off?.(SDK_READY_EVENT, onReady)
      err ? reject(err) : resolve()
    }
    const timer = setTimeout(() => finish(new Error(`IM就绪超时(${ms}ms)`)), ms)
    const poll = setInterval(() => { if (chat?.isReady?.()) finish() }, 300)
    chat?.on?.(SDK_READY_EVENT, onReady)
  })
}

async function loginResilient(sdkAppID, user_id, user_sig) {
  let lastErr = null
  for (let attempt = 0; attempt < LOGIN_MAX_ATTEMPTS; attempt++) {
    // 上次握手超时但 SDK 后台重连已成功：直接复用就绪实例，不再 login 新建实例
    if (TUILogin.getContext()?.chat?.isReady?.()) return
    if (attempt > 0 && (await getNetworkType()) === 'none') {
      throw new Error('网络不可用，请检查网络后重试')
    }
    try {
      await withTimeout(
        TUILogin.login({ SDKAppID: sdkAppID, userID: user_id, userSig: user_sig }),
        LOGIN_HANDSHAKE_TIMEOUT,
        'IM登录'
      )
      return
    } catch (e) {
      lastErr = e
      // 握手超时/失败：实例可能已建立并在后台重连，等它就绪而不是立刻重来
      const chat = TUILogin.getContext()?.chat
      if (chat) {
        if ((await getNetworkType()) === 'none') {
          throw new Error('网络不可用，请检查网络后重试')
        }
        try {
          await waitChatReady(chat, LOGIN_READY_TIMEOUT)
          return
        } catch (e2) {
          lastErr = e2
        }
      }
    }
  }
  throw lastErr || new Error('IM登录失败')
}

export async function ensureIM() {
  if (imInitialized) return true
  if (initPromise) return initPromise

  // 上次握手超时被放弃、但 SDK 后台重连已就绪：直接采纳，省去重新取凭证与 login 新建实例
  const ctx = TUILogin.getContext()
  if (ctx?.chat?.isReady?.() && ctx.SDKAppID && ctx.userID && ctx.userSig) {
    TUIChatEngine.login({
      chat: ctx.chat,
      SDKAppID: ctx.SDKAppID,
      userID: ctx.userID,
      userSig: ctx.userSig,
    })
    imInitialized = true
    pushIMProfile()
    return true
  }

  initPromise = (async () => {
    try {
      lastError = ''
      const { sdk_app_id, user_id, user_sig } = await withTimeout(
        getChatUserSig(),
        10000,
        '获取IM凭证'
      )
      if (!sdk_app_id || !user_id || !user_sig) {
        throw new Error('API返回空值，请检查后端接口')
      }
      const sdkAppID = Number(sdk_app_id)
      hookUploadDiagnostic()
      await loginResilient(sdkAppID, user_id, user_sig)
      const { chat } = TUILogin.getContext()
      if (!chat) {
        throw new Error('SDK登录成功但chat实例为空')
      }
      TUIChatEngine.login({
        chat,
        SDKAppID: sdkAppID,
        userID: user_id,
        userSig: user_sig,
      })
      imInitialized = true
      pushIMProfile()
      return true
    } catch (e) {
      initPromise = null
      lastError = e?.message || String(e)
      console.warn('IM init failed:', lastError)
      return false
    }
  })()

  return initPromise
}

export function isIMReady() {
  return imInitialized
}

export async function resetIM() {
  if (!imInitialized) return
  try {
    await TUILogin.logout()
  } catch (e) {
    console.warn('IM logout failed:', e)
  } finally {
    imInitialized = false
    initPromise = null
    imProfile = null
    lastError = ''
  }
}

// 深历史：IM 云端单聊只漫游 7 天（免费版），更早的消息只能读本系统由服务端回调落库的镜像。
// 会话 ID 形如 C2C<imAccount>，群聊本系统暂未落库，直接返回空页。
export async function fetchImHistoryPage(conversationID, before, limit = 50) {
  if (!conversationID || conversationID.indexOf('C2C') !== 0) {
    return { messages: [], hasMore: false }
  }
  const res = await withTimeout(
    getChatMessages(conversationID.slice(3), { limit, before: before || undefined }),
    8000,
    '会话历史'
  )
  return {
    messages: (res && res.messages) || [],
    hasMore: !!(res && res.has_more),
  }
}

