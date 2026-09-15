/**
 * 登录态守卫：需登录页面/操作在入口处主动检查，
 * 未登录时提示并跳转登录页，而不是放行请求后依赖 401 兜底。
 */
import { getToken } from '@/utils/request'

export function isLoggedIn() {
  return Boolean(getToken())
}

/**
 * 登录守卫。已登录返回 true；未登录 toast 提示并跳转登录页，返回 false。
 * 登录页用 navigateTo 进入，登录成功后 navigateBack 自然返回来源页。
 */
export function ensureLogin() {
  if (isLoggedIn()) return true
  uni.showToast({ title: '请先登录', icon: 'none' })
  uni.navigateTo({ url: '/pages/login/login' })
  return false
}
