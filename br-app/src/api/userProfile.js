import { get, patch, post } from '@/utils/request'

export function getMe() {
  return get('/api/v1/users/me')
}

export function updateMe(data) {
  return patch('/api/v1/users/me', data)
}

export function changePhone(data) {
  return patch('/api/v1/users/me/phone', data)
}
