export const FOLLOWED_COURSES_STORAGE_KEY = 'followed_courses'

import {
  fetchPersistedFollowedRooms,
  persistFollowRoom,
  persistUnfollowRoom,
} from '@/api/roomFollows'

const COURSE_FOLLOW_TYPE = 'course'

export function normalizeCourse(course = {}) {
  const id = course.id ?? course.course_id
  if (id === undefined || id === null || id === '') return null

  return {
    id: Number(id),
    name: course.name || '未命名课程',
    cover_image: course.cover_image || course.coverImage || '',
    price: course.price ?? '',
    teacher: course.teacher || null,
    tags: course.tags || [],
    is_hot: course.is_hot || false,
    followed_at: course.followed_at || Date.now(),
  }
}

export function getFollowedCourses() {
  const stored = uni.getStorageSync(FOLLOWED_COURSES_STORAGE_KEY)
  const courses = Array.isArray(stored) ? stored : []
  return courses.map(normalizeCourse).filter(Boolean)
}

function setFollowedCourses(courses) {
  const next = (Array.isArray(courses) ? courses : []).map(normalizeCourse).filter(Boolean)
  uni.setStorageSync(FOLLOWED_COURSES_STORAGE_KEY, next)
  return next
}

export async function syncFollowedCourses() {
  const data = await fetchPersistedFollowedRooms(COURSE_FOLLOW_TYPE)
  return setFollowedCourses(data?.items || [])
}

export function isCourseFollowed(courseId) {
  const normalizedId = Number(courseId)
  return getFollowedCourses().some((c) => c.id === normalizedId)
}

export async function followCourse(course) {
  const normalized = normalizeCourse(course)
  if (!normalized) return getFollowedCourses()

  const previous = getFollowedCourses()
  const courses = previous.filter((item) => item.id !== normalized.id)
  const next = [normalized, ...courses]
  uni.setStorageSync(FOLLOWED_COURSES_STORAGE_KEY, next)

  try {
    const persisted = await persistFollowRoom(normalized.id, COURSE_FOLLOW_TYPE)
    return setFollowedCourses([persisted, ...courses])
  } catch (error) {
    uni.setStorageSync(FOLLOWED_COURSES_STORAGE_KEY, previous)
    throw error
  }
}

export async function unfollowCourse(courseId) {
  const normalizedId = Number(courseId)
  const previous = getFollowedCourses()
  const next = previous.filter((c) => c.id !== normalizedId)
  uni.setStorageSync(FOLLOWED_COURSES_STORAGE_KEY, next)

  try {
    await persistUnfollowRoom(normalizedId, COURSE_FOLLOW_TYPE)
  } catch (error) {
    uni.setStorageSync(FOLLOWED_COURSES_STORAGE_KEY, previous)
    throw error
  }
  return next
}
