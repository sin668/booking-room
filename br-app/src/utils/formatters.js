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

const COURSE_WEEKDAY_NAMES = ['', '周一', '周二', '周三', '周四', '周五', '周六', '周日']

function normalizeScheduleSlot(slot) {
  if (!slot || typeof slot !== 'object') return null
  const weekday = Number(slot.weekday)
  if (!Number.isInteger(weekday) || weekday < 1 || weekday > 7) return null

  let start = slot.start
  let end = slot.end
  if (!start && typeof slot.time_slot === 'string') {
    const [slotStart, slotEnd] = slot.time_slot.split('-')
    start = slotStart
    end = slotEnd
  }
  start = String(start || '').trim()
  if (!start) return null
  return { weekday, start, end: String(end || '').trim() }
}

/**
 * 将 course_schedules.time_slots 数据处理为可读的上课时间文案
 * - 单选：每周三 14:00上课（时间段开始时间）
 * - 多选：每周三 14:00，周四 15:00上课
 * - 周一至周五同一时间段：工作日 14:00上课
 * - 旧版纯文本（如 "周六 9:00-11:30"、"预约制"）原样返回
 */
export function formatCourseSchedule(timeSlots) {
  if (timeSlots === null || timeSlots === undefined || timeSlots === '') return ''

  let slots = timeSlots
  if (typeof timeSlots === 'string') {
    const trimmed = timeSlots.trim()
    if (!trimmed) return ''
    if (!trimmed.startsWith('[')) return trimmed
    try {
      slots = JSON.parse(trimmed)
    } catch {
      return trimmed
    }
  }
  if (!Array.isArray(slots)) return typeof timeSlots === 'string' ? timeSlots : ''

  const normalized = slots
    .map(normalizeScheduleSlot)
    .filter(Boolean)
    .sort((a, b) => a.weekday - b.weekday)
  if (normalized.length === 0) return typeof timeSlots === 'string' ? timeSlots : ''

  const sameSlot = (
    normalized.length === 5 &&
    normalized.every((slot) => slot.weekday <= 5) &&
    normalized.every(
      (slot) => slot.start === normalized[0].start && slot.end === normalized[0].end,
    )
  )
  if (sameSlot) return `工作日 ${normalized[0].start}上课`

  const parts = normalized.map((slot) => `${COURSE_WEEKDAY_NAMES[slot.weekday]} ${slot.start}`)
  return `每${parts.join('，')}上课`
}

/**
 * 将 course_schedules.start_date 处理为开课时间文案，如 "于 2026-08-18日 后开课"
 * @param {string|null|undefined} startDate - 开课日期（YYYY-MM-DD，兼容带时间部分）
 * @returns {string} 开课时间文案，无有效日期时返回空字符串
 */
export function formatCourseStartDate(startDate) {
  if (startDate === null || startDate === undefined) return ''
  const text = String(startDate).trim()
  if (!text) return ''
  const datePart = text.includes('T') ? text.slice(0, text.indexOf('T')) : text.slice(0, 10)
  if (!datePart) return ''
  return `于 ${datePart} 后开课`
}

/**
 * 将 end_date 处理为结课时间文案，如 "于 2026-08-26 结课"
 * @param {string|null|undefined} endDate - 结课日期（YYYY-MM-DD）
 * @returns {string} 结课时间文案
 */
export function formatCourseEndDate(endDate) {
  if (endDate === null || endDate === undefined) return ''
  const text = String(endDate).trim()
  if (!text) return ''
  const datePart = text.includes('T') ? text.slice(0, text.indexOf('T')) : text.slice(0, 10)
  if (!datePart) return ''
  return `于 ${datePart} 结课`
}

/**
 * 把评分渲染为 5 个星级字符（★ 实心 / ☆ 空心），入参越界与非数字均被钳制
 *
 * 返回数组而非字符串，便于逐颗上色（如空心星置灰）；只需纯文本时 `.join('')` 即可。
 * 在 JS 侧算好比较结果，避免小程序模板出现 `<` `>` 字符（BUG-20）。
 * @param {number|string|null|undefined} rating - 评分，支持小数（四舍五入到整星）
 * @returns {string[]} 长度为 5 的星级字符数组
 */
export function buildStarChars(rating) {
  const filled = Math.min(5, Math.max(0, Math.round(Number(rating) || 0)))
  return [1, 2, 3, 4, 5].map((star) => (star <= filled ? '★' : '☆'))
}

/**
 * 把时间格式化为相对日期文案，如 "今天" / "昨天" / "3天前"，超过 30 天回落到日期
 * @param {string|null|undefined} value - ISO 时间字符串
 * @returns {string} 相对日期文案
 */
export function formatRelativeDay(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)

  const days = Math.floor((Date.now() - date.getTime()) / 86400000)
  if (days <= 0) return '今天'
  if (days === 1) return '昨天'
  if (days < 30) return `${days}天前`
  return formatDateSlash(value)
}

/**
 * 把后端错误响应归一为可直接 toast 的中文文案
 * 兼容 FastAPI 的 `{ detail: "..." }`、422 校验错误数组与普通 Error 对象
 * @param {*} error - request 失败时 reject 的响应体或 Error
 * @param {string} fallback - 无法解析时的兜底文案
 * @returns {string} 错误文案
 */
export function formatErrorDetail(error, fallback = '操作失败') {
  const detail = error?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const message = detail
      .map((item) => item?.msg || item?.message || '')
      .filter(Boolean)
      .join('；')
    if (message) return message
  }
  const message = error?.message || error?.msg
  return typeof message === 'string' && message.trim() ? message : fallback
}
