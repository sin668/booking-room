import { get, post } from '@/utils/request'

/**
 * 获取用户的所有认证记录
 */
export function getUserCertifications() {
  return get('/user-identity-verifications')
}

/**
 * 提交实名认证
 */
export function submitRealNameCertification(data) {
  return post('/user-identity-verifications/real-name', data)
}

/**
 * 提交学历认证
 */
export function submitEducationCertification(data) {
  return post('/user-identity-verifications/education', data)
}

/**
 * 提交教师资格认证
 */
export function submitTeacherCertification(data) {
  return post('/user-identity-verifications/teacher', data)
}
