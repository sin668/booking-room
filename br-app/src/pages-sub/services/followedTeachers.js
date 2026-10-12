export const FOLLOWED_TEACHERS_STORAGE_KEY = 'followed_teachers'

import { followRoom, unfollowRoom, getFollowedRooms } from '@/api/roomFollows'

export function normalizeTeacher(teacher = {}) {
  const id = teacher.id ?? teacher.teacher_id
  if (id === undefined || id === null || id === '') return null

  return {
    id: Number(id),
    name: teacher.name || '未命名教师',
    avatar: teacher.avatar || '',
    title: teacher.title || '',
    followed_at: teacher.followed_at || Date.now(),
  }
}

export function getFollowedTeachers() {
  const stored = uni.getStorageSync(FOLLOWED_TEACHERS_STORAGE_KEY)
  const teachers = Array.isArray(stored) ? stored : []
  return teachers.map(normalizeTeacher).filter(Boolean)
}

function setFollowedTeachers(teachers) {
  const next = (Array.isArray(teachers) ? teachers : []).map(normalizeTeacher).filter(Boolean)
  uni.setStorageSync(FOLLOWED_TEACHERS_STORAGE_KEY, next)
  return next
}

export function isTeacherFollowed(teacherId) {
  const normalizedId = Number(teacherId)
  return getFollowedTeachers().some((t) => t.id === normalizedId)
}

export async function followTeacher(teacher) {
  const normalized = normalizeTeacher(teacher)
  if (!normalized) return getFollowedTeachers()

  const previous = getFollowedTeachers()
  const filtered = previous.filter((t) => t.id !== normalized.id)
  const next = [normalized, ...filtered]
  uni.setStorageSync(FOLLOWED_TEACHERS_STORAGE_KEY, next)

  try {
    await followRoom(normalized.id, 'teacher')
    return setFollowedTeachers(next)
  } catch (error) {
    uni.setStorageSync(FOLLOWED_TEACHERS_STORAGE_KEY, previous)
    throw error
  }
}

export async function unfollowTeacher(teacherId) {
  const normalizedId = Number(teacherId)
  const previous = getFollowedTeachers()
  const next = previous.filter((t) => t.id !== normalizedId)
  uni.setStorageSync(FOLLOWED_TEACHERS_STORAGE_KEY, next)

  try {
    await unfollowRoom(normalizedId, 'teacher')
  } catch (error) {
    uni.setStorageSync(FOLLOWED_TEACHERS_STORAGE_KEY, previous)
    throw error
  }
  return next
}
