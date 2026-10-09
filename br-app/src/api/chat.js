import { get } from '@/utils/request'

export function getChatUserSig() {
  return get('/api/v1/chat/user-sig')
}

export function getPublisherUsername(listingId) {
  return get('/api/v1/chat/publisher-username', { listing_id: listingId })
}
