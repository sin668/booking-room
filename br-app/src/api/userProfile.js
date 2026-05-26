import { get, patch } from '@/utils/request'

export function getMe() {
  return get('/api/v1/users/me')
}

export function updateMe(data) {
  return patch('/api/v1/users/me', data)
}
