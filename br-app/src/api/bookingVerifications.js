import { post } from '@/utils/request'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function getAdminHeaders() {
  const adminToken = uni.getStorageSync('admin_token') || ''
  return adminToken ? { 'X-Admin-Token': adminToken } : {}
}

export function saveAdminToken(token) {
  if (token) {
    uni.setStorageSync('admin_token', token)
  } else {
    uni.removeStorageSync('admin_token')
  }
}

export function getStoredAdminToken() {
  return uni.getStorageSync('admin_token') || ''
}

function adminRequest(url, method) {
  // Admin verification uses X-Admin-Token, not the user Bearer token.
  // Use a direct request so admin 401/400/409/410 responses reach the page
  // instead of triggering the global Bearer token refresh flow in request.js.
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}${url}`,
      method,
      header: {
        'Content-Type': 'application/json',
        ...getAdminHeaders(),
      },
      success: (res) => {
        if (res.statusCode === 200 || res.statusCode === 201) {
          resolve(res.data)
        } else {
          reject({
            ...(res.data || {}),
            statusCode: res.statusCode,
          })
        }
      },
      fail: reject,
    })
  })
}

export function issueVerificationToken() {
  return post('/api/v1/booking-verifications/token')
}

export function inspectVerificationToken(token) {
  return adminRequest(`/api/v1/booking-verifications/${encodeURIComponent(token)}`, 'GET')
}

export function confirmVerification(token) {
  return adminRequest(`/api/v1/booking-verifications/${encodeURIComponent(token)}/confirm`, 'POST')
}
