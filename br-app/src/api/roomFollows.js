import { del, get, post } from '@/utils/request'

export function getFollowedRooms(followType = 'room') {
  const params = followType !== 'room' ? `?follow_type=${followType}` : ''
  return get(`/api/v1/room-follows${params}`)
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
