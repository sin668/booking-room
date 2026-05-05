import { get } from '@/utils/request'

/**
 * 获取自习室座位列表
 * @param {number} roomId - 自习室ID
 * @param {Object} params - { date, start_time, end_time }
 */
export function getSeats(roomId, params) {
  return get(`/api/v1/rooms/${roomId}/seats/`, params)
}
