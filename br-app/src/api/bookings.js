import { get, post } from '@/utils/request'

/**
 * 创建预约
 * @param {Object} data - 预约数据，可包含 coupon_id
 */
export function createBooking(data) {
  return post('/api/v1/bookings/', data)
}

/**
 * 获取我的预约列表
 */
export function getBookings(params) {
  return get('/api/v1/bookings/', params)
}

/**
 * 获取预约详情
 */
export function getBooking(id) {
  return get(`/api/v1/bookings/${id}/`)
}

/**
 * 取消预约
 */
export function cancelBooking(id) {
  return post(`/api/v1/bookings/${id}/cancel/`)
}
