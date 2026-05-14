import { get } from '@/utils/request'

/**
 * 获取我的卡券列表
 * @param {string} status - 卡券状态
 */
export function getCoupons(status) {
  return get('/api/v1/coupons', { status })
}

/**
 * 获取预约可用卡券列表
 * @param {Object} params - 预约参数
 */
export function getAvailableCouponsForBooking(params) {
  return get('/api/v1/coupons/available-for-booking', params)
}
