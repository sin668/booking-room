import { get } from '@/utils/request'

/**
 * 获取启用城市列表
 */
export function getCities() {
  return get('/api/v1/cities/')
}
