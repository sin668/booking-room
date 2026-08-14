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

/**
 * 获取培训室详情（含课程列表和教师团队）
 * @param {number} roomId - 培训室ID
 */
export function getTrainingRoomDetail(roomId) {
  return get(`/api/v1/training/rooms/${roomId}`)
}
