import { get, post } from '@/utils/request'

export function getCheckinSummary(params) {
  return get('/api/v1/checkin/summary', params)
}

export function submitCheckin() {
  return post('/api/v1/checkin')
}

export function submitMakeup(dates) {
  return post('/api/v1/checkin/makeup', { dates })
}
