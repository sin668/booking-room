import { get } from '@/utils/request'

/**
 * 获取自习室列表
 * @param {Object} params - { page, page_size }
 */
export function getRooms(params) {
  return get('/api/v1/rooms/', params)
}
