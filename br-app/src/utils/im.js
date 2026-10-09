import { getChatUserSig } from '@/api/chat'
import { TUILogin } from '@tencentcloud/tui-core-lite'
import TUIChatEngine from '@tencentcloud/chat-uikit-engine-lite'

let imInitialized = false
let initPromise = null

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
