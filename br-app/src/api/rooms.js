import { get } from '@/utils/request'

/**
 * 获取自习室列表
 * @param {Object} params - { page, page_size }
 */
export function getRooms(params) {
  return get('/api/v1/rooms/', params)
}

/**
 * 获取自习室详情
 * @param {number} roomId - 自习室ID
 */
export function getRoom(roomId) {
  return get(`/api/v1/rooms/${roomId}`)
}
