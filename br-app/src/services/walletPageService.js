import {
  confirmPayment,
  createRechargeOrder,
  getBalance,
  getRechargeOrder,
  getWalletTransactions,
  redeemPromoCode,
} from '@/api/wallet'

export function fetchWalletBalance() {
  return getBalance()
}

export function fetchWalletTransactionsPage(params) {
  return getWalletTransactions(params)
}

export function createRechargePaymentOrder(payload) {
  return createRechargeOrder(payload)
}

export function fetchRechargePaymentOrder(orderId) {
  return getRechargeOrder(orderId)
}

export function confirmRechargePayment(orderId) {
  return confirmPayment(orderId)
}

export function redeemRechargePromoCode(code) {
  return redeemPromoCode(code)
}
