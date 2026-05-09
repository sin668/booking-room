<template>
  <view class="page">
    <view v-if="loading && !summary" class="loading-state">
      <view class="loading-spinner" />
      <text class="loading-text">加载中...</text>
    </view>

    <template v-else>
      <view class="summary-card">
        <view class="stat-item">
          <text class="stat-value">{{ summary.monthly_hours }}h</text>
          <text class="stat-label">本月学习时长</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ summary.monthly_bookings }}次</text>
          <text class="stat-label">本月预约次数</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ summary.max_streak_days }}天</text>
          <text class="stat-label">最长连续天数</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ summary.total_hours }}h</text>
          <text class="stat-label">累计学习时长</text>
        </view>
      </view>

      <view class="calendar-card">
        <view class="calendar-header">
          <view class="arrow-btn" @tap="prevMonth">
            <text class="arrow-text">&lt;</text>
          </view>
          <text class="month-text">{{ currentYear }}年{{ currentMonth }}月</text>
          <view class="arrow-btn" @tap="nextMonth">
            <text class="arrow-text">&gt;</text>
          </view>
        </view>

        <view class="weekday-row">
          <text
            v-for="day in weekdays"
            :key="day"
            class="weekday-text"
          >{{ day }}</text>
        </view>

        <view class="days-grid">
          <view
            v-for="(cell, idx) in calendarDays"
            :key="idx"
            class="day-cell"
          >
            <view
              v-if="cell.day"
              :class="['day-inner', { 'day-today': cell.isToday, 'day-future': cell.isFuture }]"
            >
              <text :class="['day-number', { 'day-number-today': cell.isToday, 'day-number-future': cell.isFuture }]">{{ cell.day }}</text>
            </view>
            <view
              v-if="cell.day && cell.studied"
              class="studied-dot"
            />
          </view>
        </view>

        <view class="legend-row">
          <view class="legend-item">
            <view class="legend-dot legend-dot-green" />
            <text class="legend-text">已学习</text>
          </view>
          <view class="legend-item">
            <view class="legend-dot legend-dot-blue" />
            <text class="legend-text">今天</text>
          </view>
        </view>
      </view>

      <view class="record-section">
        <text class="section-title">学习记录</text>

        <view v-if="recordLoading && records.length === 0" class="record-loading">
          <view class="loading-spinner small" />
        </view>

        <view v-else-if="records.length === 0" class="empty-records">
          <text class="empty-text">暂无学习记录</text>
        </view>

        <view v-else class="record-list">
          <view
            v-for="record in records"
            :key="record.id"
            class="record-card"
          >
            <view class="record-top">
              <view class="record-room">
                <view class="book-icon">
                  <view class="book-icon-body" />
                  <view class="book-icon-page" />
                </view>
                <text class="room-name">{{ record.room_name }}</text>
                <text class="seat-number">{{ record.seat_number }}</text>
              </view>
              <text class="record-price">
                <text class="price-symbol">¥</text>{{ record.total_price }}
              </text>
            </view>
            <view class="record-bottom">
              <text class="record-time">{{ record.date }} {{ formatTime(record.start_time) }}-{{ formatTime(record.end_time) }}</text>
              <text class="record-duration">{{ record.hours }}小时</text>
            </view>
          </view>

          <view class="load-more">
            <text v-if="recordLoading" class="load-more-text">加载中...</text>
            <text v-else-if="!hasMore" class="load-more-text">没有更多了</text>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onMounted, onReachBottom } from '@dcloudio/uni-app'
import { getMonthlySummary, getStudyRecordList } from '@/api/studyRecords'

const now = new Date()
const currentYear = ref(now.getFullYear())
const currentMonth = ref(now.getMonth() + 1)

const loading = ref(false)
const recordLoading = ref(false)
const summary = ref({
  monthly_hours: 0,
  monthly_bookings: 0,
  max_streak_days: 0,
  total_hours: 0,
  calendar_mark: [],
})
const records = ref([])
const page = ref(1)
const total = ref(0)
const hasMore = ref(true)

const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const studiedDates = computed(() => {
  const set = new Set()
  for (const item of summary.value.calendar_mark || []) {
    if (item.studied) set.add(item.date)
  }
  return set
})

const calendarDays = computed(() => {
  const y = currentYear.value
  const m = currentMonth.value
  const firstDay = new Date(y, m - 1, 1).getDay()
  const daysInMonth = new Date(y, m, 0).getDate()
  const today = new Date()
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  const isCurrentMonth = today.getFullYear() === y && today.getMonth() + 1 === m

  const cells = []
  for (let i = 0; i < firstDay; i++) {
    cells.push({ day: null })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const isToday = isCurrentMonth && d === today.getDate()
    const isFuture = new Date(y, m - 1, d) > today
    cells.push({
      day: d,
      isToday,
      isFuture,
      studied: studiedDates.value.has(dateStr),
    })
  }
  return cells
})

function formatTime(time) {
  if (!time) return ''
  return time.substring(0, 5)
}

async function fetchSummary() {
  try {
    const monthStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}`
    const data = await getMonthlySummary({ month: monthStr })
    summary.value = data
  } catch {
    summary.value = { monthly_hours: 0, monthly_bookings: 0, max_streak_days: 0, total_hours: 0, calendar_mark: [] }
  }
}

async function fetchRecords(reset) {
  if (recordLoading.value) return
  if (reset) {
    page.value = 1
    records.value = []
    hasMore.value = true
  }
  recordLoading.value = true
  try {
    const monthStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}`
    const data = await getStudyRecordList({
      month: monthStr,
      page: page.value,
      page_size: 10,
    })
    const items = data.items || []
    if (page.value === 1) {
      records.value = items
    } else {
      records.value = records.value.concat(items)
    }
    total.value = data.total || 0
    hasMore.value = records.value.length < total.value
    if (!reset) page.value++
  } catch {
    if (page.value === 1) records.value = []
  } finally {
    recordLoading.value = false
  }
}

async function loadAll() {
  loading.value = true
  await Promise.all([fetchSummary(), fetchRecords(true)])
  loading.value = false
}

function prevMonth() {
  if (currentMonth.value === 1) {
    currentYear.value--
    currentMonth.value = 12
  } else {
    currentMonth.value--
  }
  loadAll()
}

function nextMonth() {
  if (currentMonth.value === 12) {
    currentYear.value++
    currentMonth.value = 1
  } else {
    currentMonth.value++
  }
  loadAll()
}

onMounted(() => {
  loadAll()
})

onReachBottom(() => {
  if (!hasMore.value || recordLoading.value) return
  fetchRecords(false)
})
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
  padding-bottom: 40rpx;
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

  &.small {
    width: 36rpx;
    height: 36rpx;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 26rpx;
  color: $text-muted;
}

.summary-card {
  margin: 24rpx 32rpx;
  padding: 32rpx 24rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, $primary, $purple);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20rpx;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 20rpx 0;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16rpx;
}

.stat-value {
  font-size: 36rpx;
  font-weight: 700;
  color: $white;
}

.stat-label {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.75);
}

.calendar-card {
  margin: 24rpx 32rpx;
  padding: 32rpx;
  border-radius: 28rpx;
  background: $white;
  box-shadow: $shadow-sm;
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 28rpx;
}

.arrow-btn {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: $bg-color;

  &:active {
    background: $border-color;
  }
}

.arrow-text {
  font-size: 28rpx;
  color: $text-primary;
  font-weight: 600;
}

.month-text {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-primary;
}

.weekday-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  margin-bottom: 16rpx;
}

.weekday-text {
  text-align: center;
  font-size: 24rpx;
  color: $text-muted;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  row-gap: 8rpx;
}

.day-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 64rpx;
}

.day-inner {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.day-inner.day-today {
  background: $primary;
}

.day-inner.day-future {
  background: transparent;
}

.day-number {
  font-size: 26rpx;
  color: $text-primary;
}

.day-number-today {
  color: $white;
  font-weight: 600;
}

.day-number-future {
  color: $text-muted;
}

.studied-dot {
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: $success;
  margin-top: 4rpx;
}

.day-inner.day-today + .studied-dot {
  background: $white;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 32rpx;
  margin-top: 24rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid $bg-color;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.legend-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
}

.legend-dot-green {
  background: $success;
}

.legend-dot-blue {
  background: $primary;
}

.legend-text {
  font-size: 22rpx;
  color: $text-muted;
}

.record-section {
  margin: 0 32rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 20rpx;
  display: block;
}

.record-loading {
  display: flex;
  justify-content: center;
  padding: 60rpx 0;
}

.empty-records {
  display: flex;
  justify-content: center;
  padding: 60rpx 0;
}

.empty-text {
  font-size: 26rpx;
  color: $text-muted;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.record-card {
  background: $white;
  border-radius: 24rpx;
  padding: 28rpx;
  box-shadow: $shadow-sm;
}

.record-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.record-room {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
  flex: 1;
}

.book-icon {
  width: 40rpx;
  height: 36rpx;
  position: relative;
  flex-shrink: 0;
}

.book-icon-body {
  width: 28rpx;
  height: 36rpx;
  border-radius: 4rpx;
  background: $primary;
  position: absolute;
  left: 0;
  top: 0;
}

.book-icon-page {
  width: 24rpx;
  height: 32rpx;
  border-radius: 2rpx;
  background: $primary-light;
  position: absolute;
  right: 0;
  bottom: 0;
}

.room-name {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.seat-number {
  font-size: 24rpx;
  color: $text-secondary;
  flex-shrink: 0;
}

.record-price {
  font-size: 32rpx;
  font-weight: 600;
  color: $primary;
  flex-shrink: 0;
  margin-left: 16rpx;
}

.price-symbol {
  font-size: 22rpx;
}

.record-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid $bg-color;
}

.record-time {
  font-size: 24rpx;
  color: $text-secondary;
}

.record-duration {
  font-size: 24rpx;
  color: $text-muted;
}

.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
}

.load-more-text {
  font-size: 24rpx;
  color: $text-muted;
}
</style>
