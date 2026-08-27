import {
  fetchPersistedFollowedRooms,
} from '@/api/roomFollows'

export function normalizeRoom(room = {}) {
  const id = room.id ?? room.room_id
  if (id === undefined || id === null || id === '') return null

  return {
    id: Number(id),
    name: room.name || '未命名',
    address: room.address || '',
    cover_image: room.cover_image || room.coverImage || '',
    city_id: room.city_id ?? room.cityId ?? null,
    city_name: room.city_name || room.cityName || '',
    min_price: room.min_price ?? room.minPrice ?? '',
    status: room.status || '',
    room_type: room.room_type || '',
    description: room.description || '',
    followed_at: room.followed_at || Date.now(),
  }
}

/**
 * 从后端 API 获取关注房间列表（异步）
 */
export async function getFollowedRooms(followType = 'room') {
  const data = await fetchPersistedFollowedRooms(followType)
  const items = data?.items || []
  return items.map(normalizeRoom).filter(Boolean)
}

/**
 * syncFollowedRooms 保留为 getFollowedRooms 的别名，兼容旧调用
 */
export const syncFollowedRooms = getFollowedRooms

/**
 * 纯函数：根据传入的房间数组生成关注摘要文本
 */
export function getFollowedRoomsSummary(rooms = []) {
  if (rooms.length === 0) return '暂无关注'
  if (rooms.length === 1) return rooms[0].name
  return `${rooms[0].name}等${rooms.length}家`
}

/**
 * 获取所有分类的关注列表（自习室、培训室、课程、教师）
 */
export async function getAllFollowedCategories() {
  const [roomItems, courseItems, teacherItems] = await Promise.allSettled([
    getFollowedRooms('room'),
    getFollowedRooms('course'),
    getFollowedRooms('teacher'),
  ])

  const allRooms = roomItems.status === 'fulfilled' ? roomItems.value : []
  const studyRooms = allRooms.filter(r => r.room_type !== 'training')
  const trainingRooms = allRooms.filter(r => r.room_type === 'training')
  const courses = courseItems.status === 'fulfilled' ? courseItems.value : []
  const teachers = teacherItems.status === 'fulfilled' ? teacherItems.value : []

  return { studyRooms, trainingRooms, courses, teachers }
}
