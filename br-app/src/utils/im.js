import { getChatUserSig } from '@/api/chat'
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
