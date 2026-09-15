import { request } from '@/utils/request'

/**
 * 获取认证列表（管理员）
 */
export function getCertifications(params) {
  return request({
    url: '/admin/certifications',
    method: 'GET',
    params,
  })
}

/**
 * 审核认证
 */
export function reviewCertification(certId, data) {
  return request({
    url: `/admin/certifications/${certId}/review`,
    method: 'PATCH',
    data,
  })
}
