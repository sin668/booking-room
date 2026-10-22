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

export async function ensureIM() {
  if (imInitialized) return true
  if (initPromise) return initPromise

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
      await withTimeout(
        TUILogin.login({
          SDKAppID: sdkAppID,
          userID: user_id,
          userSig: user_sig,
        }),
        15000,
        'IM登录'
      )
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

// 会话媒体优先使用本系统数据库里转存好的 OSS 地址：IM 的 COS 域名不在小程序白名单时，
// 历史图片/语音只有走 OSS 才能加载。命中不了就保持 IM 原地址，不阻塞聊天。
let mediaMapKey = ''
let mediaMap = {}

async function loadChatMediaMap(conversationID) {
  if (mediaMapKey === conversationID) return mediaMap
  mediaMapKey = conversationID
  mediaMap = {}
  // 只处理单聊会话，群聊会话 ID 形如 GROUPxxx 或 group_，本系统暂未落库群消息
  if (!conversationID || conversationID.indexOf('C2C') !== 0) return mediaMap
  try {
    const res = await withTimeout(
      getChatMessages(conversationID.slice(3), { limit: 200 }),
      8000,
      '会话历史'
    )
    const map = {}
    const messages = (res && res.messages) || []
    for (let i = 0; i < messages.length; i++) {
      const item = messages[i]
      if (!item.oss_url) continue
      // 数据库没有暴露 IM MsgKey，用「发送秒数 + 收发方向」对齐 SDK 消息
      const key = `${item.msg_time}_${item.direction === 'send' ? 'out' : 'in'}`
      if (!map[key]) map[key] = []
      map[key].push(item.oss_url)
    }
    mediaMap = map
  } catch (e) {
    console.warn('chat history media map failed:', e && e.message ? e.message : e)
  }
  return mediaMap
}

/** 用数据库的 OSS 地址覆盖图片/语音渲染地址，返回是否有改动（调用方据此触发重渲染）。 */
export async function applyChatMediaUrls(messageList, conversationID) {
  if (!messageList || !messageList.length) return false
  const map = await loadChatMediaMap(conversationID)
  if (!Object.keys(map).length) return false

  const used = {}
  let changed = false
  for (let i = 0; i < messageList.length; i++) {
    const message = messageList[i]
    const payload = message.payload
    if (!payload) continue
    const isImage = message.type === 'TIMImageElem'
    const isAudio = message.type === 'TIMSoundElem'
    if (!isImage && !isAudio) continue

    const key = `${message.time}_${message.flow}`
    const urls = map[key]
    if (!urls || !urls.length) continue
    const index = used[key] || 0
    used[key] = index + 1
    const ossUrl = urls[index]
    if (!ossUrl) continue

    if (isImage) {
      const info = payload.imageInfoArray && payload.imageInfoArray[0]
      if (info && info.url !== ossUrl) {
        info.url = ossUrl
        changed = true
      }
    } else if (payload.url !== ossUrl) {
      payload.url = ossUrl
      changed = true
    }
  }
  return changed
}
