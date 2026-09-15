import { request } from '@/utils/request'

/**
 * 获取用户的所有认证记录
 */
export function getUserCertifications() {
  return request({
    url: '/user-identity-verifications',
    method: 'GET',
  })
}

/**
 * 提交实名认证
 */
export function submitRealNameCertification(data) {
  return request({
    url: '/user-identity-verifications/real-name',
    method: 'POST',
    data,
  })
}

/**
 * 提交学历认证
 */
export function submitEducationCertification(data) {
  return request({
    url: '/user-identity-verifications/education',
    method: 'POST',
    data,
  })
}

/**
 * 提交教师资格认证
 */
export function submitTeacherCertification(data) {
  return request({
    url: '/user-identity-verifications/teacher',
    method: 'POST',
    data,
  })
}
