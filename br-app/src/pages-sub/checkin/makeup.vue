<template>
  <view class="page" :class="themeClass">
    <view v-if="loading && !summary.today" class="loading-state">
      <view class="loading-spinner" />
      <text class="loading-text">加载中...</text>
    </view>

    <template v-else>
      <view class="banner">
        <view class="banner-orbit" />
        <view class="banner-left">
          <text class="banner-label">剩余补签卡</text>
          <view class="banner-value">
            <text class="banner-num">{{ summary.makeup_cards }}</text>
            <text class="banner-unit">张</text>
          </view>
        </view>
        <text class="banner-desc">每张补签卡可补签 1 天，仅支持近 30 天内的漏签日期。点击日历中的 ✕ 日期进行选择。</text>
      </view>

      <view class="card calendar-card">
        <view class="calendar-head">
          <view class="month-arrow" @tap="changeMonth(-1)">
            <view class="icon icon-arrow-right month-arrow-icon prev" />
          </view>
          <text class="month-text">{{ monthLabel }}</text>
          <view class="month-arrow" :class="{ 'month-arrow-disabled': !canGoNext }" @tap="changeMonth(1)">
            <view class="icon icon-arrow-right month-arrow-icon" />
          </view>
        </view>

        <view class="weekday-row">
          <text v-for="day in weekdays" :key="day" class="weekday-text">{{ day }}</text>
        </view>

        <view class="days-grid">
          <view
            v-for="(cell, index) in calendarCells"
            :key="index"
            class="day-cell"
            :class="{
              'day-cell-today': cell && cell.isToday,
              'day-cell-selectable': cell && cell.selectable,
              'day-cell-selected': cell && cell.selected,
            }"
            @tap="onCellTap(cell)"
          >
            <template v-if="cell">
              <text class="day-num" :class="{ 'day-num-muted': cell.signed || cell.missed }">{{ cell.day }}</text>
              <text v-if="cell.signed" class="day-mark day-mark-check">✓</text>
              <text v-else-if="cell.missed" class="day-mark" :class="cell.selectable ? 'day-mark-miss' : 'day-mark-disabled'">✕</text>
              <text v-else-if="cell.isToday" class="day-mark day-mark-today">签</text>
            </template>
          </view>
        </view>

        <view class="legend-row">
          <view class="legend-item">
            <text class="legend-mark legend-mark-check">✓</text>
            <text class="legend-text">已签到</text>
          </view>
          <view class="legend-item">
            <text class="legend-mark legend-mark-miss">✕</text>
            <text class="legend-text">可补签</text>
          </view>
          <view class="legend-item">
            <text class="legend-mark legend-mark-selected">选</text>
            <text class="legend-text">已选择</text>
          </view>
        </view>
      </view>

      <view class="list-section">
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
            v-for="item in missedDates"
            :key="item.date"
            class="pick-row"
            :class="{ 'pick-row-selected': item.selected }"
            @tap="toggleDate(item.date)"
          >
            <view class="pick-date">
              <text class="pick-day">{{ item.day }}</text>
              <text class="pick-month">{{ item.month }}</text>
            </view>
            <view class="pick-info">
              <text class="pick-weekday">{{ item.weekday }}</text>
              <text class="pick-desc">{{ item.daysAgo }} 天前漏签</text>
            </view>
            <view class="pick-state" :class="{ 'pick-state-selected': item.selected }">
              <text class="pick-state-text">{{ item.selected ? '已选' : '待补签' }}</text>
            </view>
          </view>
        </view>

        <text class="list-tip">补签成功后，该日期将记为已签到，连续签到天数按补签后的记录重新计算。补签卡可通过连续签到 30 天奖励获得。</text>
      </view>
    </template>

    <view class="action-bar">
      <view class="action-left">
        <text class="action-count">已选 {{ selected.length }} 天</text>
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

const weekdays = ['一', '二', '三', '四', '五', '六', '日']
const weekdayLabels = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const loading = ref(false)
const submitting = ref(false)
const selected = ref([])
const monthCursor = ref(localMonthKey())

const summary = ref({
  today: '',
  makeup_cards: 0,
  calendar_mark: [],
  missed_dates: [],
})

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

const listSummary = computed(() =>
  missedDates.value.length > 0 ? `共 ${missedDates.value.length} 天` : ''
)

const selectedSet = computed(() => new Set(selected.value))

const missedDates = computed(() => {
  const today = summary.value.today
  if (!today) return []
  return (summary.value.missed_dates || []).map((dateStr) => {
    const dateObj = parseDate(dateStr)
    return {
      date: dateStr,
      day: pad(dateObj.getDate()),
      month: `${dateObj.getMonth() + 1}月`,
      weekday: weekdayLabels[dateObj.getDay()],
      daysAgo: Math.round((parseDate(today) - dateObj) / 86400000),
      selected: selectedSet.value.has(dateStr),
    }
  })
})

const calendarCells = computed(() => {
  const marks = summary.value.calendar_mark || []
  if (!marks.length) return []

  const firstDay = parseDate(marks[0].date).getDay()
  const offset = (firstDay + 6) % 7
  const cells = Array.from({ length: offset }, () => null)

  for (const mark of marks) {
    const dateObj = parseDate(mark.date)
    cells.push({
      date: mark.date,
      day: dateObj.getDate(),
      signed: mark.signed,
      missed: mark.missed,
      selectable: mark.makeup_eligible,
      selected: selectedSet.value.has(mark.date),
      isToday: mark.date === summary.value.today,
    })
  }
  return cells
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

function parseDate(value) {
  return new Date(`${value}T00:00:00`)
}

function errorMessage(error, fallback) {
  if (error && typeof error.detail === 'string') return error.detail
  return fallback
}

async function loadSummary() {
  loading.value = true
  try {
    summary.value = await getCheckinSummary({ month: monthKey.value })
    selected.value = selected.value.filter((date) =>
      (summary.value.missed_dates || []).includes(date)
    )
  } catch (error) {
    uni.showToast({ title: errorMessage(error, '补签数据加载失败'), icon: 'none' })
  } finally {
    loading.value = false
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
  const [year, month] = monthCursor.value.split('-').map(Number)
  const next = new Date(year, month - 1 + delta, 1)
  monthCursor.value = `${next.getFullYear()}-${pad(next.getMonth() + 1)}`
  loadSummary()
}

async function onConfirm() {
  if (!canSubmit.value) return
  submitting.value = true
  const count = selected.value.length
  try {
    await submitMakeup(selected.value)
    selected.value = []
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
  min-height: 100vh;
  background: $bg-color;
  padding: 24rpx 0 220rpx;
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
  position: relative;
  margin: 0 32rpx;
  padding: 34rpx 32rpx;
  border-radius: $radius-xl;
  background: $gradient-primary;
  overflow: hidden;
  box-shadow: $shadow-float;
}

.banner-orbit {
  position: absolute;
  width: 260rpx;
  height: 260rpx;
  right: -90rpx;
  top: -110rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
}

.banner-left {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.banner-label {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.75);
}

.banner-value {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.banner-num {
  font-size: 56rpx;
  line-height: 1;
  font-weight: 700;
  color: $white;
}

.banner-unit {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.banner-desc {
  position: relative;
  display: block;
  margin-top: 20rpx;
  font-size: 22rpx;
  line-height: 34rpx;
  color: rgba(255, 255, 255, 0.78);
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
  margin-bottom: 26rpx;
}

.month-arrow {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: $primary-soft;
  display: flex;
  align-items: center;
  justify-content: center;

  &:active {
    background: $border-color;
  }
}

.month-arrow-disabled {
  opacity: 0.35;
}

.month-arrow-icon {
  font-size: 26rpx;
  color: $text-primary;
}

.month-arrow-icon.prev {
  transform: rotate(180deg);
}

.month-text {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-primary;
}

.weekday-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 10rpx;
}

.weekday-text {
  text-align: center;
  font-size: 22rpx;
  color: $text-muted;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  row-gap: 8rpx;
}

.day-cell {
  height: 92rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2rpx;
  border-radius: 20rpx;
  border: 1rpx solid transparent;
}

.day-cell-today {
  background: $primary-soft;
}

.day-cell-selectable:active {
  background: $surface-soft;
}

.day-cell-selected {
  background: $primary-soft;
  border-color: $primary;
}

.day-num {
  font-size: 26rpx;
  color: $text-primary;
}

.day-num-muted {
  color: $text-secondary;
}

.day-mark {
  font-size: 20rpx;
  line-height: 1;
  font-weight: 600;
}

.day-mark-check {
  color: $success;
}

.day-mark-miss {
  color: $danger;
}

.day-mark-disabled {
  color: $text-muted;
  opacity: 0.4;
}

.day-mark-today {
  color: $primary;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 36rpx;
  margin-top: 26rpx;
  padding-top: 22rpx;
  border-top: 1rpx solid $bg-color;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.legend-mark {
  font-size: 22rpx;
  font-weight: 600;
}

.legend-mark-check {
  color: $success;
}

.legend-mark-miss {
  color: $danger;
}

.legend-mark-selected {
  color: $primary;
}

.legend-text {
  font-size: 22rpx;
  color: $text-muted;
}

.list-section {
  margin: 32rpx 32rpx 0;
}

.list-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.list-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.list-summary {
  font-size: 22rpx;
  color: $text-muted;
}

.empty-state {
  padding: 60rpx 32rpx;
  border-radius: $radius-xl;
  background: $surface;
  border: 1rpx solid $border-soft;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
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
  gap: 16rpx;
}

.pick-row {
  padding: 22rpx 24rpx;
  border-radius: $radius-lg;
  background: $surface;
  border: 1rpx solid $border-soft;
  display: flex;
  align-items: center;
  gap: 20rpx;

  &:active {
    background: $surface-soft;
  }
}

.pick-row-selected {
  border-color: $primary;
  background: $primary-soft;
}

.pick-date {
  width: 96rpx;
  height: 88rpx;
  border-radius: 18rpx;
  background: $bg-color;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2rpx;
  flex-shrink: 0;
}

.pick-day {
  font-size: 34rpx;
  font-weight: 700;
  color: $text-primary;
}

.pick-month {
  font-size: 20rpx;
  color: $text-muted;
}

.pick-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.pick-weekday {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.pick-desc {
  font-size: 22rpx;
  color: $text-muted;
}

.pick-state {
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: $danger-light;
  color: $danger;
  flex-shrink: 0;
}

.pick-state-selected {
  background: $primary;
  color: $white;
}

.pick-state-text {
  font-size: 20rpx;
  font-weight: 600;
}

.list-tip {
  display: block;
  margin-top: 22rpx;
  font-size: 20rpx;
  line-height: 32rpx;
  color: $text-muted;
}

.action-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 50;
  padding: 20rpx 32rpx calc(20rpx + env(safe-area-inset-bottom));
  background: $surface;
  border-top: 1rpx solid $border-soft;
  box-shadow: $shadow-bottom;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.action-left {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.action-count {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.action-sub {
  font-size: 20rpx;
  color: $text-muted;
}

.action-btn {
  min-width: 280rpx;
  height: 84rpx;
  padding: 0 32rpx;
  border-radius: 24rpx;
  background: $gradient-primary;
  display: flex;
  align-items: center;
  justify-content: center;

  &:active {
    opacity: 0.9;
  }
}

.action-btn-disabled {
  background: $surface-muted;
  box-shadow: none;
}

.action-btn-text {
  font-size: 28rpx;
  font-weight: 600;
  color: $white;
}

.action-btn-disabled .action-btn-text {
  color: $text-muted;
}
</style>
