import {
  PAYMENT_POLL_INTERVAL,
  PAYMENT_POLL_MAX_ATTEMPTS,
  PAYMENT_TERMINAL_FAILURE_STATUSES,
} from '@/constants/wallet'

export function createPaymentStatusError(status) {
  const error = new Error(`payment ${status}`)
  error.paymentStatus = status
  return error
}

export function getPaymentStatus(response) {
  return response?.payment_status || response?.paymentStatus || response?.status
}

export function waitForPaymentPoll(ms = PAYMENT_POLL_INTERVAL) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

export async function pollPaymentStatus({
  fetchStatus,
  isSuccess,
  failureStatuses = PAYMENT_TERMINAL_FAILURE_STATUSES,
  maxAttempts = PAYMENT_POLL_MAX_ATTEMPTS,
  wait = waitForPaymentPoll,
  timeoutResult = null,
}) {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const result = await fetchStatus()
    const status = getPaymentStatus(result)
    if (isSuccess(status, result)) return result
    if (failureStatuses.includes(status)) throw createPaymentStatusError(status)
    if (attempt < maxAttempts - 1) await wait()
  }

  return timeoutResult
}
