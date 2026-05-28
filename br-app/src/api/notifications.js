import request, { get, post } from '@/utils/request'

export function getNotifications(params) {
  return get('/api/v1/notifications', params)
}

export function getNotificationUnreadSummary() {
  return get('/api/v1/notifications/unread-summary')
}

export function markNotificationRead(id) {
  return post(`/api/v1/notifications/${id}/read`)
}

export function markAllNotificationsRead(params) {
  const type = typeof params === 'string' ? params : params?.type
  const query = type ? `?type=${encodeURIComponent(type)}` : ''
  return post(`/api/v1/notifications/read-all${query}`)
}

export function getNotificationPreferences() {
  return get('/api/v1/notifications/preferences')
}

export function updateNotificationPreferences(data) {
  return request({
    url: '/api/v1/notifications/preferences',
    method: 'PUT',
    data,
  })
}
