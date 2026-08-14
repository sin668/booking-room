import { get } from '@/utils/request'

/**
 * 获取培训室列表（含热门课程）
 * @param {Object} params - { page, page_size, city_id }
 */
export function getTrainingRooms(params) {
  return get('/api/v1/training/rooms', params)
}

/**
 * 获取培训课程列表
 * @param {Object} params - { page, page_size, category }
 */
export function getTrainingCourses(params) {
  return get('/api/v1/training/courses', params)
}
