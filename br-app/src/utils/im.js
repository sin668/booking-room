import { getChatUserSig } from '@/api/chat'
import { TUILogin } from '@tencentcloud/tui-core-lite'
import TUIChatEngine, { TUIUserService } from '@tencentcloud/chat-uikit-engine-lite'

let imInitialized = false
let initPromise = null
let imProfile = null

/** 会话列表里对方的头像/昵称取自 IM 用户画像，因此需把本系统资料写回 IM，否则对方只能看到账号名 */
async function pushIMProfile() {
  if (!imProfile) return
  const payload = {}
  if (imProfile.nick) payload.nick = imProfile.nick
  if (imProfile.avatar) payload.avatar = imProfile.avatar
  if (!payload.nick && !payload.avatar) return
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
      const { sdk_app_id, user_id, user_sig } = await getChatUserSig()
      await TUILogin.login({
        SDKAppID: sdk_app_id,
        userID: user_id,
        userSig: user_sig,
        framework: 'vue3',
      })
      const { chat } = TUILogin.getContext()
      TUIChatEngine.login({
        chat,
        SDKAppID: sdk_app_id,
        userID: user_id,
        userSig: user_sig,
      })
      imInitialized = true
      pushIMProfile()
      return true
    } catch (e) {
      initPromise = null
      console.warn('IM init failed:', e)
      return false
    }
  })()

  return initPromise
}

export function isIMReady() {
  return imInitialized
}

/** 退出系统登录必须同步登出 IM，否则 imInitialized 短路会让下一个用户复用上一个账号的 IM 会话 */
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
  }
}
