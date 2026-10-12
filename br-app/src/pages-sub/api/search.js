import { get } from '@/utils/request'

/**
 * 全局搜索（自习室、培训室、课程、老师）
 * @param {Object} params - { q, city_id }
 */
export function searchAll(params) {
  return get('/api/v1/search', params)
}
