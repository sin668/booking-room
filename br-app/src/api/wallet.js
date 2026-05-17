import { get, post } from '@/utils/request'

export function getBalance() {
  return get('/api/v1/wallet/balance')
}

export function getWalletTransactions(params) {
  return get('/api/v1/wallet/transactions', params)
}

export function createRechargeOrder(data) {
  return post('/api/v1/wallet/recharge', data)
}

export function getRechargeOrder(orderId) {
  return get(`/api/v1/wallet/recharge/${orderId}`)
}

export function confirmPayment(orderId) {
  return post(`/api/v1/wallet/recharge/${orderId}/confirm`)
}

export function redeemPromoCode(code) {
  return post('/api/v1/wallet/promo-code', { code })
}
