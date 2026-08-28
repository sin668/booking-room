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
          <text class="stat-label">本月已完成</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">{{ summary.total_hours }}h</text>
          <text class="stat-label">累计学习时长</text>
        </view>
      </view>

      <view class="calendar-card">
        <view class="calendar-header">
          <view class="arrow-btn" @tap="prevMonth">
            <text class="arrow-text">‹</text>
          </view>
          <text class="month-text">{{ currentYear }}年{{ currentMonth }}月</text>
          <view class="arrow-btn" @tap="nextMonth">
            <text class="arrow-text">›</text>
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
              class="studied-dot studied-dot-green"
            />
          </view>
        </view>

        <view class="legend-row">
          <view class="legend-item">
            <view class="legend-dot legend-dot-green" />
            <text class="legend-text">已学习</text>
          </view>
          <view class="legend-item">
            <view class="legend-dot legend-dot-today" />
            <text class="legend-text">今天</text>
          </view>
        </view>
      </view>

      <view class="record-section">
        <text class="section-title">学习记录</text>

        <view class="tab-bar">
          <view
            v-for="tab in tabs"
            :key="tab.value"
            :class="['tab-item', { 'tab-active': activeTab === tab.value }]"
            @tap="switchTab(tab.value)"
          >
            <text :class="['tab-text', { 'tab-text-active': activeTab === tab.value }]">{{ tab.label }}</text>
          </view>
        </view>

        <view v-if="recordLoading && records.length === 0" class="record-loading">
          <view class="loading-spinner small" />
        </view>

        <view v-else-if="records.length === 0" class="empty-records">
          <text class="empty-text">暂无学习记录</text>
        </view>

        <view v-else class="record-list">
          <view
            v-for="record in records"
            :key="`${record.record_type}-${record.id}`"
            class="record-card"
          >
            <view class="record-top">
              <view class="record-left">
                <view v-if="record.record_type === 'course'" class="course-icon">
                  <view class="course-icon-body" />
                </view>
                <view v-else class="book-icon">
                  <view class="book-icon-body" />
                  <view class="book-icon-page" />
                </view>
                <view class="record-info">
                  <text v-if="record.record_type === 'course'" class="course-name">{{ record.course_name || '培训课程' }}</text>
                  <text v-else class="room-name">{{ record.room_name }}</text>
                  <view class="record-sub-row">
                    <text v-if="record.record_type === 'course'" class="lesson-detail-text">{{ record.lesson_title || '课时' }}</text>
                    <text v-else-if="record.seat_number" class="seat-number">{{ record.seat_number }}号座位<template v-if="record.seat_zone"> · {{ record.seat_zone }}</template></text>
                  </view>
                </view>
              </view>
              <view class="record-right">
                <text class="status-badge status-completed">
                  已学习
                </text>
                <text v-if="record.record_type === 'seat'" class="record-price">
                  <text class="price-symbol">¥</text>{{ record.total_price }}
                </text>
              </view>
            </view>
            <view class="record-bottom">
              <text v-if="record.record_type === 'course' && record.lesson_date" class="record-time">{{ record.lesson_date }} {{ formatLessonStartTime(record.lesson_time_slot) }}上课</text>
              <text v-else class="record-time">{{ record.date }} {{ formatTime(record.start_time) }}-{{ formatTime(record.end_time) }}</text>
              <text v-if="record.record_type === 'course' && record.duration_minutes" class="record-duration">{{ record.duration_minutes }}分钟</text>
              <text v-else class="record-duration">{{ record.hours }}小时</text>
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
import { ref, computed, onMounted } from 'vue'
import { onReachBottom } from '@dcloudio/uni-app'
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
  monthly_upcoming_hours: 0,
  monthly_upcoming_count: 0,
})
const records = ref([])
const page = ref(1)
const total = ref(0)
const hasMore = ref(true)
const activeTab = ref('all')

const tabs = [
  { label: '全部', value: 'all' },
]

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

function formatLessonStartTime(timeSlot) {
  if (!timeSlot || typeof timeSlot !== 'string') return ''
  return timeSlot.split('-')[0] || ''
}

function formatLessonPrice(price) {
  if (price == null) return ''
  return Number(price).toFixed(2)
}

async function fetchSummary() {
  try {
    const monthStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}`
    const data = await getMonthlySummary({ month: monthStr })
    summary.value = data
  } catch {
    summary.value = { monthly_hours: 0, monthly_bookings: 0, max_streak_days: 0, total_hours: 0, calendar_mark: [], monthly_upcoming_hours: 0, monthly_upcoming_count: 0 }
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
    const params = {
      month: monthStr,
      page: page.value,
      page_size: 10,
    }
    const data = await getStudyRecordList(params)
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

function switchTab(tabValue) {
  if (activeTab.value === tabValue) return
  activeTab.value = tabValue
  fetchRecords(true)
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
  background: linear-gradient(180deg, $bg-warm 0, $bg-color 460rpx);
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
  border-radius: 32rpx;
  background: $gradient-primary;
  box-shadow: $shadow-float;
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
  background: rgba(255, 255, 255, 0.12);
  border-radius: 20rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.16);
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
  border-radius: 32rpx;
  background: $surface;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
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
  background: $primary-soft;
  border: 1rpx solid $border-soft;

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
  background: $gradient-primary;
  box-shadow: 0 6rpx 14rpx rgba(79, 110, 247, 0.22);
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
  margin-top: 4rpx;
}

.studied-dot-green {
  background: $success;
}

.studied-dot-blue {
  background: $primary;
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

.legend-dot-today {
  background: $primary;
  box-shadow: 0 2rpx 6rpx rgba(79, 110, 247, 0.3);
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

.tab-bar {
  display: flex;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.tab-item {
  padding: 12rpx 28rpx;
  border-radius: 24rpx;
  background: $surface;
  border: 1rpx solid $border-soft;
}

.tab-active {
  background: $primary;
  border-color: $primary;
}

.tab-text {
  font-size: 24rpx;
  color: $text-secondary;
}

.tab-text-active {
  color: $white;
  font-weight: 600;
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
  background: $surface;
  border-radius: 28rpx;
  padding: 28rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.record-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.record-left {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
  flex: 1;
}

.record-info {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  min-width: 0;
  flex: 1;
}

.record-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8rpx;
  flex-shrink: 0;
  margin-left: 16rpx;
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

.course-icon {
  width: 40rpx;
  height: 36rpx;
  position: relative;
  flex-shrink: 0;
}

.course-icon-body {
  width: 36rpx;
  height: 28rpx;
  border-radius: 6rpx;
  background: $orange;
  position: absolute;
  left: 2rpx;
  top: 4rpx;
}

.room-name {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-name {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-sub-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.seat-number {
  font-size: 24rpx;
  color: $text-secondary;
  flex-shrink: 0;
}

.lesson-detail-text {
  font-size: 24rpx;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-badge {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  font-weight: 500;
}

.status-completed {
  color: $success;
  background: rgba(82, 196, 26, 0.1);
}

.status-upcoming {
  color: $primary;
  background: rgba(79, 110, 247, 0.1);
}

.record-price {
  font-size: 32rpx;
  font-weight: 600;
  color: $primary;
  flex-shrink: 0;
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

.lesson-meta-row {
  margin-top: 12rpx;
  padding-top: 12rpx;
  border-top: 1rpx dashed $bg-color;
}

.lesson-meta-text {
  font-size: 22rpx;
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
