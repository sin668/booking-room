import {
  fetchPersistedFollowedRooms,
} from '@/api/roomFollows'

export function normalizeRoom(room = {}) {
  const id = room.id ?? room.room_id
  if (id === undefined || id === null || id === '') return null

  return {
    id: Number(id),
    name: room.name || '未命名自习室',
    address: room.address || '',
    cover_image: room.cover_image || room.coverImage || '',
    city_id: room.city_id ?? room.cityId ?? null,
    city_name: room.city_name || room.cityName || '',
    min_price: room.min_price ?? room.minPrice ?? '',
    status: room.status || '',
    followed_at: room.followed_at || Date.now(),
  }
}

/**
 * 从后端 API 获取关注房间列表（异步）
 */
export async function getFollowedRooms() {
  const data = await fetchPersistedFollowedRooms()
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
