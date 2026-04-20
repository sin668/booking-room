import { get } from '@/utils/request'

/**
 * 获取轮播图列表
 */
export function getBanners() {
  return get('/api/v1/banners/')
}
