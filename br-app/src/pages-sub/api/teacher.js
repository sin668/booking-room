import { get } from '@/utils/request'

export function getTeacherDetail(teacherId) {
  return get(`/api/v1/teachers/${teacherId}`)
}
