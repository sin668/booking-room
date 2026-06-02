import { del, get, post } from '@/utils/request'

export function getFollowedRooms() {
  return get('/api/v1/room-follows')
}

export function followRoom(roomId) {
  return post(`/api/v1/room-follows/${roomId}`)
}

export function unfollowRoom(roomId) {
  return del(`/api/v1/room-follows/${roomId}`)
}

export const persistFollowRoom = followRoom
export const fetchPersistedFollowedRooms = getFollowedRooms
export const persistUnfollowRoom = unfollowRoom
