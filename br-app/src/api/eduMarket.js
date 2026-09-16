import { get, post } from '@/utils/request'

/**
 * 教培供需综合广场列表（教/学混排，仅已通过信息，游客可访问）
 * @param {Object} params - { listing_type, subject, city, sort, page, page_size }
 *   listing_type: tutor(家教) | training(培训班) | demand(求教)，不传为全部混排
 *   sort: new(最新) | price_asc(价格升序) | price_desc(价格降序)
 */
export function getEduListings(params) {
  return get('/api/v1/edu-listings', params)
}

/**
 * 供需信息详情（浏览数 +1，附带发布者昵称/头像/认证状态）
 * @param {number} id
 */
export function getEduListingDetail(id) {
  return get(`/api/v1/edu-listings/${id}`)
}

/**
 * 我发布的供需信息（全部状态，需登录）
 * @param {Object} params - { page, page_size }
 */
export function getMyEduListings(params) {
  return get('/api/v1/edu-listings/mine', params)
}

/**
 * 发布供需信息（后端按类型强制认证前置校验）
 * @param {Object} data - { listing_type, title, subject, teaching_mode, price, price_unit, area, description, images, available_times }
 */
export function createEduListing(data) {
  return post('/api/v1/edu-listings', data)
}
