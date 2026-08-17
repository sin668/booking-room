import { get, post } from '@/utils/request'

/**
 * 获取课程详情 + 课时列表
 * @param {number|string} courseId - 课程 ID
 */
export function getCourseLessons(courseId) {
  return get(`/api/v1/courses/${courseId}/lessons`)
}

/**
 * 创建课程预约
 * @param {Object} data - 预约数据
 * @param {number} data.course_id - 课程 ID
 * @param {string} data.booking_type - 预约类型 fixed|custom
 * @param {number[]} data.lesson_ids - 选中的课时 ID 列表
 * @param {string} data.schedule_type - 上课时间类型 fixed|custom
 * @param {string} data.payment_method - 支付方式 balance|wechat
 * @param {number} [data.coupon_id] - 优惠券 ID
 */
export function createCourseBooking(data) {
  return post('/api/v1/course-bookings', data)
}

/**
 * 取消课程预约
 * @param {number|string} bookingId - 预约 ID
 */
export function cancelCourseBooking(bookingId) {
  return post(`/api/v1/course-bookings/${bookingId}/cancel`)
}
