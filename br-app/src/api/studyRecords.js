import { get } from '@/utils/request'

export function getMonthlySummary(params) {
  return get('/api/v1/study-records/summary', params)
}

export function getStudyRecordList(params) {
  return get('/api/v1/study-records', params)
}