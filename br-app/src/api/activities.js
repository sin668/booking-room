import { get, post } from '@/utils/request'

/**
 * 获取热门活动列表
 */
export function getActivities() {
  return get('/api/v1/activities/')
}

export function getActivityDetail(activityId) {
  return get(`/api/v1/activities/${activityId}/`)
}

export function claimActivityCoupon(activityId, activityCouponId) {
  return post(`/api/v1/activities/${activityId}/coupons/${activityCouponId}/claim`)
}
