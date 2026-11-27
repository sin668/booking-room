<template>
  <view class="page" :class="themeClass">
    <view v-if="loading && !summary.today" class="loading-state">
      <view class="loading-spinner" />
      <text class="loading-text">加载中...</text>
    </view>

    <template v-else>
      <view class="banner">
        <view class="banner-icon">
          <view class="icon icon-calendar-plus" />
        </view>
        <view class="banner-info">
          <text class="banner-title">{{ bannerTitle }}</text>
          <text class="banner-desc">每张补签卡可补签 1 天，仅支持近 30 天内的漏签日期。点击日历中的 ✕ 日期进行选择。</text>
        </view>
      </view>

      <view class="card calendar-card">
        <view class="calendar-head">
          <view class="month-arrow" @tap="changeMonth(-1)">
            <view class="icon icon-arrow-right month-arrow-icon prev" />
          </view>
          <view class="month-center">
            <text class="month-text">{{ monthLabel }}</text>
            <text class="month-sub">本月漏签 {{ missedLeft }} 天</text>
          </view>
          <view
            class="month-arrow"
            :class="{ 'month-arrow-disabled': !canGoNext }"
            @tap="changeMonth(1)"
          >
            <view class="icon icon-arrow-right month-arrow-icon" />
          </view>
        </view>

        <view class="weekday-row">
          <text v-for="day in weekdays" :key="day" class="weekday-text">{{ day }}</text>
        </view>

        <view class="days-grid">
          <view
            v-for="cell in calendarCells"
            :key="`${cell.date}-${cell.outside}`"
            class="day-cell"
            :class="{ 'day-cell-outside': cell.outside && !cell.signed, 'day-cell-selectable': cell.selectable }"
            @tap="onCellTap(cell)"
          >
            <view
              class="day-badge"
              :class="{
                'day-badge-check': cell.signed,
                'day-badge-ring': cell.signed && cell.isToday,
                'day-badge-miss': !cell.signed && cell.missed,
                'day-badge-selected': !cell.signed && cell.selected,
                'day-badge-today': !cell.signed && !cell.missed && cell.isToday,
                'day-badge-future': !cell.signed && !cell.missed && !cell.isToday && cell.future,
              }"
              :style="cell.signed && cell.outside ? 'opacity: 0.45;' : ''"
            >
              <view v-if="cell.signed" class="icon icon-check day-badge-icon" />
              <view v-else-if="cell.missed" class="icon icon-close day-badge-icon" />
              <text v-else-if="cell.isToday" class="day-badge-text">签</text>
              <text v-else-if="cell.future" class="day-badge-text">{{ cell.projected }}</text>
              <text v-else class="day-badge-text day-badge-text-plain">{{ cell.day }}</text>
            </view>
            <text
              class="day-label"
              :class="{
                'day-label-miss': !cell.signed && cell.missed,
                'day-label-today': cell.isToday,
                'day-label-outside': cell.outside,
              }"
            >{{ cell.isToday ? '今天' : cell.label }}</text>
          </view>
        </view>

        <view class="legend-row">
          <view class="legend-item">
            <view class="legend-badge legend-badge-check">
              <view class="icon icon-check legend-badge-icon" />
            </view>
            <text class="legend-text">已签到</text>
          </view>
          <view class="legend-item">
            <view class="legend-badge legend-badge-miss">
              <view class="icon icon-close legend-badge-icon" />
            </view>
            <text class="legend-text">可补签</text>
          </view>
          <view class="legend-item">
            <view class="legend-badge legend-badge-future">
              <text class="legend-badge-text">{{ legendProjected }}</text>
            </view>
            <text class="legend-text">未开始</text>
          </view>
        </view>
      </view>

      <view class="card list-card">
        <view class="list-head">
          <text class="list-title">待补签日期</text>
          <text class="list-summary">{{ listSummary }}</text>
        </view>

        <view v-if="missedDates.length === 0" class="empty-state">
          <view class="empty-icon">
            <view class="icon icon-check" />
          </view>
          <text class="empty-title">近 30 天暂无漏签日期</text>
          <text class="empty-desc">保持每日签到，连续天数会持续累积</text>
        </view>

        <view v-else class="pick-list">
          <view
            v-for="(item, index) in missedDates"
            :key="item.date"
            class="pick-row"
            :class="{ 'pick-row-selected': item.selected }"
            @tap="toggleDate(item.date)"
          >
            <view class="row-icon">
              <view class="icon icon-calendar-xmark" />
            </view>
            <view class="pick-info">
              <text class="pick-title">{{ item.month }}月{{ item.day }}日</text>
              <text class="pick-desc">{{ item.weekday }} · 漏签</text>
            </view>
            <text class="row-state" :class="{ 'row-state-selected': item.selected }">
              {{ item.selected ? '已选择' : '可选择' }}
            </text>
            <view v-if="index < missedDates.length - 1" class="pick-divider" />
          </view>
        </view>
      </view>

      <text class="list-tip">补签成功后，该日期将记为已签到，连续签到天数按补签后的记录重新计算。补签卡可通过连续签到 30 天奖励获得。</text>
    </template>

    <view class="action-bar">
      <view class="action-left">
        <text class="action-count">已选 <text class="action-strong">{{ selected.length }}</text> 天</text>
        <text class="action-sub">剩余补签卡 {{ summary.makeup_cards }} 张</text>
      </view>
      <view
        class="action-btn"
        :class="{ 'action-btn-disabled': !canSubmit }"
        @tap="onConfirm"
      >
        <text class="action-btn-text">{{ submitting ? '补签中...' : '确认补签' }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getCheckinSummary, submitMakeup } from '@/api/checkin'
import { ensureLogin } from '@/utils/auth'

const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const weekdayLabels = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const loading = ref(false)
const submitting = ref(false)
const selected = ref([])
const monthCursor = ref(localMonthKey())

const summary = ref({
  today: '',
  today_signed: false,
  streak: 0,
  makeup_cards: 0,
  calendar_mark: [],
  missed_dates: [],
})

const makeupSucceeded = ref(false)
const adjacentMarks = ref([])
let requestSeq = 0

const monthKey = computed(() => monthCursor.value)

const monthLabel = computed(() => {
  const [year, month] = monthCursor.value.split('-').map(Number)
  return `${year}年${month}月`
})

const currentMonthKey = computed(() => {
  const today = summary.value.today || localDateKey()
  return today.slice(0, 7)
})

const canGoNext = computed(() => monthKey.value < currentMonthKey.value)
const canSubmit = computed(
  () => selected.value.length > 0 && !submitting.value
)

const missedLeft = computed(() => (summary.value.missed_dates || []).length)

const bannerTitle = computed(() => {
  if (missedLeft.value > 0) return `漏签 ${missedLeft.value} 天，补签可恢复连续签到`
  if (makeupSucceeded.value) return '漏签已全部补签，连续签到已恢复'
  return '太棒了！近30天暂无漏签日期'
})

const listSummary = computed(() => {
  if (missedLeft.value > 0) return `共 ${missedLeft.value} 天待补签`
  return makeupSucceeded.value ? '已全部补签' : ''
})

const selectedSet = computed(() => new Set(selected.value))

const missedDates = computed(() => {
  const today = summary.value.today
  if (!today) return []
  return (summary.value.missed_dates || []).map((dateStr) => {
    const dateObj = parseDate(dateStr)
    return {
      date: dateStr,
      day: dateObj.getDate(),
      month: dateObj.getMonth() + 1,
      weekday: weekdayLabels[dateObj.getDay()],
      selected: selectedSet.value.has(dateStr),
    }
  })
})

const markMap = computed(() => {
  const map = new Map()
  for (const mark of adjacentMarks.value) {
    map.set(mark.date, mark)
  }
  for (const mark of summary.value.calendar_mark || []) {
    map.set(mark.date, mark)
  }
  return map
})

const calendarCells = computed(() => {
  if (!summary.value.today) return []

  const [year, month] = monthCursor.value.split('-').map(Number)
  const first = new Date(year, month - 1, 1)
  const offset = (first.getDay() + 6) % 7
  const today = summary.value.today
  const cells = []

  for (let i = 0; i < 42; i += 1) {
    const date = new Date(year, month - 1, 1 - offset + i)
    const dateKey = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
    const mark = markMap.value.get(dateKey)
    const outside = date.getMonth() !== month - 1
    const future = dateKey > today
    const signed = Boolean(mark && mark.signed)
    const missed = Boolean(mark && mark.missed) && !outside

    cells.push({
      date: dateKey,
      day: date.getDate(),
      label: `${date.getMonth() + 1}.${date.getDate()}`,
      outside,
      signed,
      missed,
      selectable: missed && Boolean(mark.makeup_eligible),
      selected: selectedSet.value.has(dateKey),
      isToday: dateKey === today,
      future,
      projected: future ? projectedStreak(dateKey) : 0,
    })
  }
  return cells
})

const legendProjected = computed(() => {
  const last = calendarCells.value[calendarCells.value.length - 1]
  if (last && last.future) return last.projected
  return Math.max(summary.value.streak || 0, 1)
})

function pad(value) {
  return String(value).padStart(2, '0')
}

function localDateKey() {
  const now = new Date()
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

function localMonthKey() {
  const now = new Date()
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}`
}

function shiftMonthKey(key, delta) {
  const [year, month] = key.split('-').map(Number)
  const next = new Date(year, month - 1 + delta, 1)
  return `${next.getFullYear()}-${pad(next.getMonth() + 1)}`
}

function parseDate(value) {
  return new Date(`${value}T00:00:00`)
}

function projectedStreak(dateStr) {
  const diff = Math.round(
    (parseDate(dateStr) - parseDate(summary.value.today)) / 86400000
  )
  return (summary.value.streak || 0) + diff + (summary.value.today_signed ? 0 : 1)
}

function errorMessage(error, fallback) {
  if (error && typeof error.detail === 'string') return error.detail
  return fallback
}

async function loadSummary() {
  const seq = ++requestSeq
  const key = monthKey.value
  loading.value = true
  try {
    const [current, prev, next] = await Promise.allSettled([
      getCheckinSummary({ month: key }),
      getCheckinSummary({ month: shiftMonthKey(key, -1) }),
      getCheckinSummary({ month: shiftMonthKey(key, 1) }),
    ])
    if (seq !== requestSeq) return
    if (current.status !== 'fulfilled') throw current.reason
    summary.value = current.value
    adjacentMarks.value = [
      ...(prev.status === 'fulfilled' ? prev.value?.calendar_mark || [] : []),
      ...(next.status === 'fulfilled' ? next.value?.calendar_mark || [] : []),
    ]
    selected.value = selected.value.filter((date) =>
      (summary.value.missed_dates || []).includes(date)
    )
  } catch (error) {
    if (seq !== requestSeq) return
    adjacentMarks.value = []
    uni.showToast({ title: errorMessage(error, '补签数据加载失败'), icon: 'none' })
  } finally {
    if (seq === requestSeq) loading.value = false
  }
}

function toggleDate(dateStr) {
  if (selected.value.includes(dateStr)) {
    selected.value = selected.value.filter((item) => item !== dateStr)
    return
  }
  if (summary.value.makeup_cards <= 0) {
    uni.showToast({ title: '暂无可用补签卡', icon: 'none' })
    return
  }
  if (selected.value.length >= summary.value.makeup_cards) {
    uni.showToast({ title: '补签卡不足，请先取消其他日期', icon: 'none' })
    return
  }
  selected.value = [...selected.value, dateStr].sort()
}

function onCellTap(cell) {
  if (!cell || !cell.selectable) return
  toggleDate(cell.date)
}

function changeMonth(delta) {
  if (delta > 0 && !canGoNext.value) return
  monthCursor.value = shiftMonthKey(monthCursor.value, delta)
  loadSummary()
}

async function onConfirm() {
  if (!canSubmit.value) return
  submitting.value = true
  const count = selected.value.length
  try {
    await submitMakeup(selected.value)
    selected.value = []
    makeupSucceeded.value = true
    await loadSummary()
    uni.showToast({ title: `补签成功，已补签 ${count} 天`, icon: 'none' })
  } catch (error) {
    uni.showToast({ title: errorMessage(error, '补签失败，请稍后重试'), icon: 'none' })
  } finally {
    submitting.value = false
  }
}

onShow(() => {
  if (!ensureLogin()) return
  loadSummary()
})
</script>

<style lang="scss" scoped>
.page {
  --check-miss-bg: #FFF1F2;
  --check-miss-border: #FFE4E6;
  --check-miss-text: #FB7185;
  --check-future-bg: #FFF6EF;
  --check-future-border: #FFE3CF;
  --check-future-text: #FF8A3D;
  --check-accent-soft: #FFF4EC;
  --check-banner-bg: #EEF1FF;
  --check-banner-border: #E0E6FF;

  min-height: 100vh;
  background: $bg-color;
  padding: 24rpx 0 260rpx;

  &.theme-dark {
    --check-miss-bg: rgba(251, 113, 133, 0.14);
    --check-miss-border: rgba(251, 113, 133, 0.3);
    --check-miss-text: #FF9AAE;
    --check-future-bg: rgba(255, 138, 61, 0.14);
    --check-future-border: rgba(255, 138, 61, 0.3);
    --check-future-text: #FFB07A;
    --check-accent-soft: rgba(255, 138, 61, 0.16);
    --check-banner-bg: rgba(79, 110, 247, 0.12);
    --check-banner-border: rgba(79, 110, 247, 0.24);
  }
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60vh;
  gap: 24rpx;
}

.loading-spinner {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  border: 4rpx solid $border-color;
  border-top-color: $primary;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 26rpx;
  color: $text-muted;
}

.banner {
  display: flex;
  align-items: flex-start;
  gap: 24rpx;
  margin: 0 32rpx;
  padding: 28rpx 32rpx;
  border-radius: $radius-xl;
  background: var(--check-banner-bg);
  border: 1rpx solid var(--check-banner-border);
}

.banner-icon {
  width: 72rpx;
  height: 72rpx;
  flex-shrink: 0;
  border-radius: 24rpx;
  background: $surface;
  color: $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  box-shadow: $shadow-sm;
}

.banner-info {
  flex: 1;
  min-width: 0;
}

.banner-title {
  display: block;
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.banner-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  line-height: 34rpx;
  color: $text-secondary;
}

.card {
  margin: 24rpx 32rpx 0;
  padding: 32rpx;
  border-radius: $radius-xl;
  background: $surface;
  border: 1rpx solid $border-soft;
  box-shadow: $shadow-card;
}

.calendar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.month-arrow {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: $surface-soft;
  display: flex;
  align-items: center;
  justify-content: center;

  &:active {
    background: $surface-muted;
  }
}

.month-arrow-disabled {
  opacity: 0.35;
}

.month-arrow-icon {
  font-size: 20rpx;
  color: $text-secondary;
}

.month-arrow-icon.prev {
  transform: rotate(180deg);
}

.month-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
}

.month-text {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.month-sub {
  font-size: 20rpx;
  color: $text-muted;
}

.weekday-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin: 24rpx 0 8rpx;
  text-align: center;
}

.weekday-text {
  font-size: 20rpx;
  color: $text-muted;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  row-gap: 16rpx;
}

.day-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.day-cell-outside {
  opacity: 0.45;
}

.day-cell-selectable:active {
  opacity: 0.7;
}

.day-badge {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2rpx solid transparent;
}

.day-badge-check {
  background: $gradient-primary;
  box-shadow: 0 4rpx 12rpx rgba(79, 110, 247, 0.28);
  color: $white;
}

.day-badge-ring {
  box-shadow: 0 0 0 4rpx rgba(79, 110, 247, 0.18);
}

.day-badge-miss {
  background: var(--check-miss-bg);
  border-color: var(--check-miss-border);
  color: var(--check-miss-text);
}

.day-badge-selected {
  border: 4rpx solid $primary;
}

.day-badge-today {
  background: $surface;
  border: 4rpx solid $primary;
  color: $primary;
}

.day-badge-future {
  background: var(--check-future-bg);
  border-color: var(--check-future-border);
  color: var(--check-future-text);
}

.day-badge-icon {
  font-size: 22rpx;
}

.day-badge-text {
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1;
}

.day-badge-text-plain {
  font-weight: 400;
  color: $text-muted;
}

.day-label {
  font-size: 18rpx;
  line-height: 1;
  color: $text-muted;
}

.day-label-miss {
  color: var(--check-miss-text);
}

.day-label-today {
  font-weight: 600;
  color: $primary;
}

.day-label-outside {
  opacity: 0.6;
}

.legend-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 24rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid $border-soft;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.legend-badge {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2rpx solid transparent;
}

.legend-badge-check {
  background: $gradient-primary;
  color: $white;
}

.legend-badge-miss {
  background: var(--check-miss-bg);
  border-color: var(--check-miss-border);
  color: var(--check-miss-text);
}

.legend-badge-future {
  background: var(--check-future-bg);
  border-color: var(--check-future-border);
  color: var(--check-future-text);
}

.legend-badge-icon {
  font-size: 14rpx;
}

.legend-badge-text {
  font-size: 16rpx;
  font-weight: 700;
  line-height: 1;
}

.legend-text {
  font-size: 20rpx;
  color: $text-muted;
}

.list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.list-title {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.list-summary {
  font-size: 20rpx;
  color: $text-muted;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  padding: 48rpx 24rpx 40rpx;
}

.empty-icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: $success-light;
  color: $success;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  margin-bottom: 8rpx;
}

.empty-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.empty-desc {
  font-size: 22rpx;
  color: $text-muted;
}

.pick-list {
  display: flex;
  flex-direction: column;
}

.pick-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 20rpx 0;

  &:active {
    opacity: 0.7;
  }
}

.pick-divider {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 1rpx;
  background: $border-soft;
}

.row-icon {
  width: 64rpx;
  height: 64rpx;
  flex-shrink: 0;
  border-radius: 16rpx;
  background: var(--check-miss-bg);
  color: var(--check-miss-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
}

.pick-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.pick-title {
  font-size: 24rpx;
  font-weight: 500;
  color: $text-primary;
}

.pick-desc {
  font-size: 20rpx;
  color: $text-muted;
}

.row-state {
  flex-shrink: 0;
  padding: 6rpx 18rpx;
  border-radius: 999rpx;
  border: 1rpx solid $border-color;
  font-size: 20rpx;
  color: $text-muted;
}

.row-state-selected {
  border-color: transparent;
  background: $primary-soft;
  font-weight: 500;
  color: $primary;
}

.list-tip {
  display: block;
  margin: 32rpx 48rpx 0;
  font-size: 20rpx;
  line-height: 34rpx;
  color: $text-muted;
}

.action-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 50;
  padding: 24rpx 32rpx calc(20rpx + env(safe-area-inset-bottom));
  background: $surface;
  border-top: 1rpx solid $border-soft;
  box-shadow: $shadow-bottom;
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.action-left {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.action-count {
  font-size: 22rpx;
  font-weight: 500;
  color: $text-primary;
}

.action-strong {
  font-weight: 700;
  color: $primary;
}

.action-sub {
  font-size: 20rpx;
  color: $text-muted;
}

.action-btn {
  width: 288rpx;
  height: 88rpx;
  flex-shrink: 0;
  border-radius: 999rpx;
  background: $primary;
  display: flex;
  align-items: center;
  justify-content: center;

  &:active {
    opacity: 0.9;
  }
}

.action-btn-disabled {
  opacity: 0.4;
}

.action-btn-text {
  font-size: 28rpx;
  font-weight: 600;
  color: $white;
}
</style>
