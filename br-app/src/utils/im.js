import { getChatUserSig } from '@/api/chat'
import { TUILogin } from '@tencentcloud/tui-core-lite'
import TUIChatEngine, { TUIUserService } from '@tencentcloud/chat-uikit-engine-lite'

let imInitialized = false
let initPromise = null
let imProfile = null
let lastError = ''

export function getIMLastError() {
  return lastError
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
      const { sdk_app_id, user_id, user_sig } = await getChatUserSig()
      if (!sdk_app_id || !user_id || !user_sig) {
        throw new Error('API返回空值，请检查后端接口')
      }
      await TUILogin.login({
        SDKAppID: Number(sdk_app_id),
        userID: user_id,
        userSig: user_sig,
        framework: 'vue3',
      })
      const { chat } = TUILogin.getContext()
      if (!chat) {
        throw new Error('SDK登录成功但chat实例为空')
      }
      TUIChatEngine.login({
        chat,
        SDKAppID: Number(sdk_app_id),
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
