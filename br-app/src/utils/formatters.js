import { BOOKING_STATUS_LABELS, SEAT_ZONE_LABELS } from '@/constants/booking'
import { WALLET_TRANSACTION_STATUS_LABELS } from '@/constants/wallet'

function toFiniteNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

export function formatMoney(value) {
  return toFiniteNumber(value).toFixed(2)
}

export function formatAmount(value) {
  const amount = toFiniteNumber(value)
  return Number.isInteger(amount)
    ? String(amount)
    : amount.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')
}

export function formatShortTime(value) {
  if (!value) return ''
  if (typeof value === 'string' && /^\d{1,2}:\d{2}/.test(value)) return value.slice(0, 5)

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)

  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

export function formatDateTime(value) {
  if (!value) return '时间 -'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)

  const pad = (number) => String(number).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function formatDateSlash(value) {
  if (!value) return ''
  return String(value).slice(0, 10).replace(/-/g, '/')
}

export function formatRoomMinPrice(room) {
  const price = Number(room?.min_price ?? room?.minPrice)
  if (!Number.isFinite(price) || price <= 0) return ''
  return `¥${formatAmount(price)}起`
}

export function formatBookingStatus(status) {
  return BOOKING_STATUS_LABELS[status] || status || ''
}

export function formatWalletStatus(status) {
  return WALLET_TRANSACTION_STATUS_LABELS[status] || '处理中'
}

export function formatSeatZone(zone) {
  return SEAT_ZONE_LABELS[zone] || zone || ''
}

export function formatHourDuration(startTime, endTime) {
  return `${formatHourCount(startTime, endTime)}小时`
}

export function formatHourCount(startTime, endTime) {
  const parse = (time) => {
    const [hours = 0, minutes = 0] = String(time || '').split(':').map(Number)
    return hours + minutes / 60
  }
  const duration = Math.max(0, parse(endTime) - parse(startTime))
  return formatAmount(duration)
}
