/**
 * uni.request 封装，支持 Token 自动刷新
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

let isRefreshing = false
let pendingRequests = []

function getToken() {
  return uni.getStorageSync('access_token') || ''
}

function setToken(token) {
  uni.setStorageSync('access_token', token)
}

function removeToken() {
  uni.removeStorageSync('access_token')
}

function resolvePendingRequests(token) {
  pendingRequests.forEach((cb) => cb(token))
  pendingRequests = []
}

async function doRefreshToken() {
  const res = await new Promise((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}/api/v1/auth/refresh`,
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          reject(new Error('refresh failed'))
        }
      },
      fail: reject,
    })
  })
  setToken(res.access_token)
  return res.access_token
}

function request(options) {
  const buildRequest = (tokenValue) => {
    const header = {
      'Content-Type': 'application/json',
      ...options.header,
    }
    if (tokenValue) {
      header['Authorization'] = `Bearer ${tokenValue}`
    }
    return new Promise((resolve, reject) => {
      uni.request({
        url: `${BASE_URL}${options.url}`,
        method: options.method || 'GET',
        data: options.data,
        header,
        success: (res) => {
          if (res.statusCode === 200 || res.statusCode === 201) {
            resolve(res.data)
          } else if (res.statusCode === 401) {
            if (!isRefreshing) {
              isRefreshing = true
              doRefreshToken()
                .then((newToken) => {
                  isRefreshing = false
                  resolvePendingRequests(newToken)
                  buildRequest(newToken).then(resolve).catch(reject)
                })
                .catch(() => {
                  isRefreshing = false
                  pendingRequests = []
                  removeToken()
                  uni.reLaunch({ url: '/pages/login/login' })
                  reject(new Error('登录已过期'))
                })
            } else {
              pendingRequests.push((newToken) => {
                buildRequest(newToken).then(resolve).catch(reject)
              })
            }
          } else {
            reject(res.data)
          }
        },
        fail: reject,
      })
    })
  }

  return buildRequest(getToken())
}

export function get(url, data) {
  return request({ url, method: 'GET', data })
}

export function post(url, data) {
  return request({ url, method: 'POST', data })
}

export { getToken, setToken, removeToken }
export default request
