import { get } from '@/utils/request'

/**
 * 获取热门活动列表
 */
export function getActivities() {
  return get('/api/v1/activities/')
}
