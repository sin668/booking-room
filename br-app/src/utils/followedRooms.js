const FOLLOWED_ROOMS_STORAGE_KEY = 'followed_rooms'

function normalizeRoom(room = {}) {
  const id = room.id ?? room.room_id
  if (id === undefined || id === null || id === '') return null

  return {
    id: Number(id),
    name: room.name || '未命名自习室',
    address: room.address || '',
    cover_image: room.cover_image || '',
    followed_at: room.followed_at || Date.now(),
  }
}

export function getFollowedRooms() {
  const storedRooms = uni.getStorageSync(FOLLOWED_ROOMS_STORAGE_KEY)
  const rooms = Array.isArray(storedRooms) ? storedRooms : []
  return rooms.map(normalizeRoom).filter(Boolean)
}

export function isRoomFollowed(roomId) {
  const normalizedId = Number(roomId)
  return getFollowedRooms().some((room) => room.id === normalizedId)
}

export function followRoom(room) {
  const normalizedRoom = normalizeRoom(room)
  if (!normalizedRoom) return getFollowedRooms()

  const rooms = getFollowedRooms().filter((item) => item.id !== normalizedRoom.id)
  const nextRooms = [normalizedRoom, ...rooms]
  uni.setStorageSync(FOLLOWED_ROOMS_STORAGE_KEY, nextRooms)
  return nextRooms
}

export function unfollowRoom(roomId) {
  const normalizedId = Number(roomId)
  const nextRooms = getFollowedRooms().filter((room) => room.id !== normalizedId)
  uni.setStorageSync(FOLLOWED_ROOMS_STORAGE_KEY, nextRooms)
  return nextRooms
}
