import { get, post } from '@/utils/request'

export function getAccountSecuritySummary() {
  return get('/api/v1/users/me/security')
}

export function changePassword(data) {
  return post('/api/v1/users/me/password', data)
}

export function submitIdentityVerification(data) {
  return post('/api/v1/users/me/identity-verification', data)
}

export function deactivateAccount() {
  return post('/api/v1/users/me/deactivation')
}
