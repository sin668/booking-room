import { ensureLogin } from '@/utils/auth'
import { ensureIM, getIMLastError } from '@/utils/im'
import { useUserStore } from '@/store/modules/user'

// 平台客服账号 bd7f84cc-3d8b-480f-9327-30ee827cf386 的 IM 用户名（UUID 去横线）
export const PLATFORM_CS_IM_ID = 'bd7f84cc3d8b480f932730ee827cf386'

/**
 * 打开客服会话。创建人为空（存量数据）或就是当前用户自己时，回退到平台客服。
 * @param {string|null|undefined} creatorUsername 目标创建人的 IM 用户名
 */
export async function openCSChat(creatorUsername) {
  if (!ensureLogin()) return
  const ownImId = (useUserStore().userInfo?.id || '').replace(/-/g, '')
  const target =
    creatorUsername && creatorUsername !== ownImId ? creatorUsername : PLATFORM_CS_IM_ID
  uni.showLoading({ title: '正在连接...' })
  const ok = await ensureIM()
  uni.hideLoading()
  if (!ok) {
    uni.showToast({ title: '消息服务初始化失败：' + getIMLastError(), icon: 'none', duration: 3000 })
    return
  }
  uni.navigateTo({ url: `/TUIKit/components/TUIChat/index?conversationID=C2C${target}` })
}