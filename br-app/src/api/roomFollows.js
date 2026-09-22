import { del, get, post } from '@/utils/request'

export function getFollowedRooms(followType = 'room', cityId = null) {
  const parts = []
  if (followType !== 'room') parts.push(`follow_type=${followType}`)
  if (cityId !== null && cityId !== undefined && cityId !== '') {
    parts.push(`city_id=${cityId}`)
  }
  const qs = parts.length ? `?${parts.join('&')}` : ''
  return get(`/api/v1/room-follows${qs}`)
}

export function followRoom(roomId, followType = 'room') {
  const params = followType !== 'room' ? `?follow_type=${followType}` : ''
  return post(`/api/v1/room-follows/${roomId}${params}`)
}

export function unfollowRoom(roomId, followType = 'room') {
  const params = followType !== 'room' ? `?follow_type=${followType}` : ''
  return del(`/api/v1/room-follows/${roomId}${params}`)
}

export const persistFollowRoom = followRoom
export const fetchPersistedFollowedRooms = getFollowedRooms
export const persistUnfollowRoom = unfollowRoom
