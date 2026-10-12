import { getToken, refreshAccessToken } from '@/utils/request'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const UPLOAD_IMAGE_URL = '/api/v1/upload/image'

function buildAuthHeader(tokenValue = getToken()) {
  return tokenValue ? { Authorization: `Bearer ${tokenValue}` } : {}
}

function normalizeErrorMessage(payload, fallback) {
  const detail = payload?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message || item)
      .filter(Boolean)
      .join('；') || fallback
  }
  return payload?.message || payload?.msg || detail?.message || fallback
}

function createUploadError(payload, fallback = '图片上传失败') {
  const error = new Error(normalizeErrorMessage(payload, fallback))
  error.response = payload
  return error
}

function parseUploadResponse(data) {
  let payload = data
  if (typeof data === 'string') {
    const text = data.trim()
    if (!text) {
      throw createUploadError(null, '上传响应为空')
    }
    try {
      payload = JSON.parse(text)
    } catch {
      throw createUploadError(null, '上传响应解析失败')
    }
  }

  const result = payload?.data && typeof payload.data === 'object' ? payload.data : payload
  if (!result?.url) {
    throw createUploadError(payload, '上传响应缺少图片地址')
  }

  return {
    url: result.url,
    object_key: result.object_key || '',
    size: result.size || 0,
    content_type: result.content_type || '',
  }
}

function uploadOnce(filePath, scope, tokenValue) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${BASE_URL}${UPLOAD_IMAGE_URL}`,
      filePath,
      name: 'file',
      formData: { scope },
      header: buildAuthHeader(tokenValue),
      success: resolve,
      fail: reject,
    })
  })
}

export async function uploadImage(filePath, scope = 'avatar') {
  if (!filePath) {
    throw new Error('请选择要上传的图片')
  }

  let response = await uploadOnce(filePath, scope)
  if (response.statusCode === 401) {
    const newToken = await refreshAccessToken()
    response = await uploadOnce(filePath, scope, newToken)
  }

  if (response.statusCode < 200 || response.statusCode >= 300) {
    let payload = response.data
    if (typeof payload === 'string' && payload.trim()) {
      try {
        payload = JSON.parse(payload)
      } catch {
        payload = { message: payload }
      }
    }
    throw createUploadError(payload, '图片上传失败')
  }

  return parseUploadResponse(response.data)
}

export default uploadImage
