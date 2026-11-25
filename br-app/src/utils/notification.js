import { sendArrivalReminder } from '@/api/notifications'
import { isLoggedIn } from '@/utils/auth'

const SENDERS = {
  arrival: sendArrivalReminder,
}

/**
 * 公共发送消息方法：未登录直接跳过；失败静默，不阻塞业务页面。
 */
export async function sendNotification(type, payload) {
  const sender = SENDERS[type]
  if (!sender || !isLoggedIn()) return null
  try {
    return await sender(payload)
  } catch (error) {
    console.warn('[Notification] send failed:', type, error)
    return null
  }
}
