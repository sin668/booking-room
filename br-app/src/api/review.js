import { get, post } from '@/utils/request'

/**
 * 获取学员评价列表
 * @param {Object} params - { course_id, teacher_id, booking_id, mine, rating_band, has_images, sort, page, page_size }
 *   rating_band: all | good(4-5星) | mid(3星) | bad(1-2星)
 *   sort: new(最新) | score(评分最高)
 *   mine 为 true 时返回本人全部状态（含待审核/已驳回），需登录态
 */
export function getReviewList(params) {
  return get('/api/v1/reviews', params)
}

/**
 * 获取评价概览（均分/总数/好评率/星级分布）
 * @param {Object} params - { course_id } 或 { teacher_id }，至少传一个
 */
export function getReviewSummary(params) {
  return get('/api/v1/reviews/summary', params)
}

/**
 * 发表评价
 * @param {Object} data - { booking_id, rating, content, images, tags, is_anonymous }
 */
export function createReview(data) {
  return post('/api/v1/reviews', data)
}
