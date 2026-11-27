<template>
  <view class="page" :class="themeClass">
    <view v-if="loading && !summary.today" class="loading-state">
      <view class="loading-spinner" />
      <text class="loading-text">加载中...</text>
    </view>

    <template v-else>
      <view class="hero">
        <view class="hero-orb hero-orb-lg" />
        <view class="hero-orb hero-orb-sm" />

        <view class="hero-head">
          <view class="hero-streak">
            <text class="hero-label">已连续签到</text>
            <view class="hero-value">
              <text class="hero-num">{{ summary.streak }}</text>
              <text class="hero-unit">天</text>
            </view>
          </view>
          <view class="hero-badge">
            <view class="hero-avatar">
              <view class="icon icon-star hero-avatar-icon" />
            </view>
            <text class="hero-badge-text">学习达人</text>
          </view>
        </view>

        <view class="hero-stats">
          <view class="hero-stat">
            <text class="hero-stat-label">累计签到</text>
            <view class="hero-stat-value">
              <text class="hero-stat-num">{{ summary.total_days }}</text>
              <text class="hero-stat-unit">天</text>
            </view>
          </view>
          <view class="hero-stat">
            <text class="hero-stat-label">补签卡</text>
            <view class="hero-stat-value">
              <text class="hero-stat-num">{{ summary.makeup_cards }}</text>
              <text class="hero-stat-unit">张</text>
            </view>
          </view>
        </view>

        <view
          class="sign-btn"
          :class="{ 'sign-btn-done': !canSign && !submitting }"
          @tap="onSign"
        >
          <view class="icon icon-check sign-btn-icon" />
          <text class="sign-btn-text">{{ signButtonText }}</text>
        </view>
        <text class="hero-hint">{{ heroHint }}</text>
      </view>

      <view class="card calendar-card">
        <view class="calendar-head">
          <view class="month-arrow" @tap="changeMonth(-1)">
            <view class="icon icon-arrow-right month-arrow-icon prev" />
          </view>
          <view class="month-center">
            <text class="month-text">{{ monthLabel }}</text>
            <text class="month-sub">本月已签到 {{ signedThisMonth }} 天</text>
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
            :key="cell.date"
            class="day-cell"
            :class="{ 'day-cell-outside': cell.outside && !cell.signed }"
            @tap="onCellTap(cell)"
          >
            <view
              class="day-badge"
              :class="{
                'day-badge-check': cell.signed && !cell.outside,
                'day-badge-check-outside': cell.signed && cell.outside,
                'day-badge-ring': cell.signed && cell.isToday && !cell.outside,
                'day-badge-miss': !cell.signed && cell.missed,
                'day-badge-today': !cell.signed && !cell.missed && cell.isToday,
                'day-badge-future': !cell.signed && !cell.missed && !cell.isToday && cell.future,
              }"
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
            <text class="legend-text">缺签</text>
          </view>
          <view class="legend-item">
            <view class="legend-badge legend-badge-future">
              <text class="legend-badge-text">{{ legendProjected }}</text>
            </view>
            <text class="legend-text">预计连签</text>
          </view>
        </view>
      </view>

      <view class="card reward-card">
        <view class="reward-head">
          <view class="reward-title-row">
            <view class="reward-icon">
              <view class="icon icon-gift" />
            </view>
            <view>
              <text class="reward-title">连签奖励</text>
              <text class="reward-subtitle">连续签到 30 天赠 1 张补签卡</text>
            </view>
          </view>
          <text class="reward-days">
            {{ streakInCycle }}<text class="reward-days-unit">/30天</text>
          </text>
        </view>
        <view class="reward-track">
          <view class="reward-fill" :style="{ width: `${rewardProgress}%` }" />
        </view>
        <view class="reward-foot">
          <text class="reward-foot-text">
            再签 <text class="reward-foot-strong">{{ nextRewardDays }}</text> 天可得补签卡
          </text>
          <text class="reward-foot-text">每日签到 +5 积分</text>
        </view>
      </view>

      <view class="card makeup-card" @tap="goMakeup">
        <view class="makeup-icon">
          <view class="icon icon-calendar-plus" />
        </view>
        <view class="makeup-info">
          <text class="makeup-title">补签漏签日期</text>
          <text class="makeup-desc">{{ makeupHint }}</text>
        </view>
        <text class="makeup-action">去补签</text>
        <view class="icon icon-arrow-right makeup-arrow" />
      </view>

      <view class="card rules-card">
        <view class="rules-head">
          <view class="icon icon-bell rules-head-icon" />
          <text class="rules-title">签到规则</text>
        </view>
        <view class="rule-item">
          <view class="rule-dot" />
          <text class="rule-text">每日可签到 1 次，签到成功即获得 5 积分。</text>
        </view>
        <view class="rule-item">
          <view class="rule-dot" />
          <text class="rule-text">连续签到 7 天，额外奖励 20 积分。</text>
        </view>
        <view class="rule-item">
          <view class="rule-dot" />
          <text class="rule-text">连续签到中断后，连续天数将从下一次签到重新计算。</text>
        </view>
        <view class="rule-item">
          <view class="rule-dot" />
          <text class="rule-text">每张补签卡可补签 1 天，仅支持近 30 天内的漏签日期。</text>
        </view>
      </view>
    </template>

    <view v-if="showSuccess" class="modal-mask" @tap="closeSuccess">
      <view class="success-card" @tap.stop>
        <view class="success-head">
          <view class="success-orb success-orb-lg" />
          <view class="success-orb success-orb-sm" />
          <view class="success-check">
            <view class="icon icon-check success-check-icon" />
          </view>
          <text class="success-title">签到成功</text>
          <text class="success-date">{{ formatDateWithWeekday(summary.today) }}</text>
        </view>
        <view class="success-body">
          <view class="success-stats">
            <view class="success-stat">
              <text class="success-stat-value success-stat-primary">{{ summary.streak }}</text>
              <text class="success-stat-label">连续签到(天)</text>
            </view>
            <view class="success-divider" />
            <view class="success-stat">
              <text class="success-stat-value success-stat-accent">+{{ rewardPoints }}</text>
              <text class="success-stat-label">获得积分</text>
            </view>
            <view class="success-divider" />
            <view class="success-stat">
              <text class="success-stat-value">{{ summary.total_days }}</text>
              <text class="success-stat-label">累计签到(天)</text>
            </view>
          </view>

          <view v-if="rewardCards > 0" class="success-extra">
            连续 30 天奖励：补签卡 +{{ rewardCards }}
          </view>

          <view class="success-progress">
            <view class="success-progress-head">
              <text class="success-progress-title">连签 30 天奖励</text>
              <text class="success-progress-value">{{ streakInCycle }}/30</text>
            </view>
            <view class="success-track">
              <view class="success-fill" :style="{ width: `${rewardProgress}%` }" />
            </view>
            <text class="success-progress-tip">再签 {{ nextRewardDays }} 天，可获赠 1 张补签卡</text>
          </view>

          <view class="success-btn" @tap="closeSuccess">
            <text class="success-btn-text">知道了</text>
          </view>
          <text class="success-tip">明日签到可继续累积连续天数</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getCheckinSummary, submitCheckin } from '@/api/checkin'
import { ensureLogin } from '@/utils/auth'

const weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const weekdayLabels = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const loading = ref(false)
const submitting = ref(false)
const showSuccess = ref(false)
const rewardPoints = ref(0)
const rewardCards = ref(0)
const monthCursor = ref(localMonthKey())

const emptySummary = () => ({
  today: '',
  today_signed: false,
  streak: 0,
  total_days: 0,
  points: 0,
  makeup_cards: 0,
  calendar_mark: [],
  missed_dates: [],
})

const summary = ref(emptySummary())
const adjacentMarks = ref([])
let requestSeq = 0

const monthKey = computed(() => {
  const [year, month] = monthCursor.value.split('-').map(Number)
  return `${year}-${String(month).padStart(2, '0')}`
})

const monthLabel = computed(() => {
  const [year, month] = monthCursor.value.split('-').map(Number)
  return `${year}年${month}月`
})

const currentMonthKey = computed(() => {
  const today = summary.value.today || localDateKey()
  return today.slice(0, 7)
})

const canGoNext = computed(() => monthKey.value < currentMonthKey.value)
const todaySigned = computed(() => summary.value.today_signed)
const canSign = computed(
  () => Boolean(summary.value.today) && !todaySigned.value && !submitting.value
)

const signButtonText = computed(() => {
  if (submitting.value) return '签到中...'
  if (!summary.value.today) return '暂不可用'
  return todaySigned.value ? '今日已签到' : '立即签到'
})

const heroHint = computed(() =>
  todaySigned.value
    ? '今日 +5 积分已到账 · 明天继续签到'
    : '今日签到可得 5 积分 · 连续 7 天额外 +20 积分'
)

const nextRewardDays = computed(() => 30 - (summary.value.streak % 30))
const streakInCycle = computed(() => summary.value.streak % 30)
const rewardProgress = computed(() =>
  Math.min(100, Math.round((streakInCycle.value / 30) * 100))
)

const signedThisMonth = computed(() =>
  (summary.value.calendar_mark || []).filter((mark) => mark.signed).length
)

const makeupHint = computed(() => {
  const count = summary.value.missed_dates.length
  if (count > 0) {
    return `当前有 ${count} 天漏签，可使用补签卡恢复连续签到`
  }
  return '近 30 天暂无漏签日期'
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
  return Math.max(summary.value.streak, 1)
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
  return summary.value.streak + diff + (summary.value.today_signed ? 0 : 1)
}

function formatDateWithWeekday(value) {
  if (!value) return ''
  const [year, month, day] = value.split('-')
  return `${year}年${Number(month)}月${Number(day)}日 · ${weekdayLabels[parseDate(value).getDay()]}`
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
  } catch (error) {
    if (seq !== requestSeq) return
    summary.value = emptySummary()
    adjacentMarks.value = []
    uni.showToast({ title: errorMessage(error, '签到数据加载失败'), icon: 'none' })
  } finally {
    if (seq === requestSeq) loading.value = false
  }
}

function applySummary(nextSummary) {
  if (nextSummary) {
    summary.value = nextSummary
    if (nextSummary.today) {
      const todayMonth = nextSummary.today.slice(0, 7)
      if (todayMonth !== monthCursor.value) {
        monthCursor.value = todayMonth
        adjacentMarks.value = []
      }
    }
  }
}

async function onSign() {
  if (!canSign.value) return
  submitting.value = true
  try {
    const result = await submitCheckin()
    applySummary(result.summary)
    rewardPoints.value = result.reward_points || 0
    rewardCards.value = result.reward_cards || 0
    showSuccess.value = true
  } catch (error) {
    uni.showToast({ title: errorMessage(error, '签到失败，请稍后重试'), icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function closeSuccess() {
  showSuccess.value = false
}

function changeMonth(delta) {
  if (delta > 0 && !canGoNext.value) return
  monthCursor.value = shiftMonthKey(monthCursor.value, delta)
  loadSummary()
}

function onCellTap(cell) {
  if (!cell || !cell.missed) return
  goMakeup()
}

function goMakeup() {
  uni.navigateTo({ url: '/pages-sub/checkin/makeup' })
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
  --check-track: #F3F4F6;
  --check-adjacent-bg: rgba(99, 113, 241, 0.42);
  --check-adjacent-text: rgba(255, 255, 255, 0.92);

  min-height: 100vh;
  background: $bg-color;
  padding: 24rpx 0 48rpx;

  &.theme-dark {
    --check-miss-bg: rgba(251, 113, 133, 0.14);
    --check-miss-border: rgba(251, 113, 133, 0.3);
    --check-miss-text: #FF9AAE;
    --check-future-bg: rgba(255, 138, 61, 0.14);
    --check-future-border: rgba(255, 138, 61, 0.3);
    --check-future-text: #FFB07A;
    --check-accent-soft: rgba(255, 138, 61, 0.16);
    --check-track: rgba(255, 255, 255, 0.08);
    --check-adjacent-bg: rgba(124, 138, 255, 0.34);
    --check-adjacent-text: rgba(255, 255, 255, 0.9);
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

.hero {
  position: relative;
  margin: 24rpx 32rpx 0;
  padding: 40rpx 40rpx 32rpx;
  border-radius: 48rpx;
  background: $gradient-primary;
  overflow: hidden;
  box-shadow: $shadow-float;
}

.hero-orb {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
  pointer-events: none;
}

.hero-orb-lg {
  width: 320rpx;
  height: 320rpx;
  right: -80rpx;
  top: -128rpx;
}

.hero-orb-sm {
  width: 192rpx;
  height: 192rpx;
  right: -128rpx;
  top: 128rpx;
}

.hero-head {
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24rpx;
}

.hero-label {
  font-size: 24rpx;
  letter-spacing: 2rpx;
  color: rgba(255, 255, 255, 0.7);
}

.hero-value {
  display: flex;
  align-items: flex-end;
  gap: 12rpx;
  margin-top: 8rpx;
}

.hero-num {
  font-size: 84rpx;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -2rpx;
  color: $white;
}

.hero-unit {
  margin-bottom: 8rpx;
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
}

.hero-badge {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 8rpx 24rpx 8rpx 8rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.15);
}

.hero-avatar {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  border: 2rpx solid rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: $white;
  font-size: 26rpx;
}

.hero-badge-text {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.9);
}

.hero-stats {
  position: relative;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
  margin-top: 32rpx;
}

.hero-stat {
  padding: 16rpx 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.1);
}

.hero-stat-label {
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.6);
}

.hero-stat-value {
  display: flex;
  align-items: baseline;
  gap: 6rpx;
  margin-top: 6rpx;
}

.hero-stat-num {
  font-size: 28rpx;
  font-weight: 600;
  color: $white;
}

.hero-stat-unit {
  font-size: 20rpx;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.7);
}

.sign-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  height: 96rpx;
  margin-top: 32rpx;
  border-radius: 999rpx;
  background: $white;
  box-shadow: 0 8rpx 24rpx rgba(15, 17, 21, 0.12);

  &:active {
    transform: scale(0.985);
  }
}

.sign-btn-icon {
  font-size: 30rpx;
  color: $primary;
}

.sign-btn-text {
  font-size: 32rpx;
  font-weight: 700;
  color: $primary;
}

.sign-btn-done {
  background: rgba(255, 255, 255, 0.2);
  box-shadow: none;
}

.sign-btn-done .sign-btn-icon,
.sign-btn-done .sign-btn-text {
  color: $white;
}

.hero-hint {
  position: relative;
  display: block;
  margin-top: 16rpx;
  text-align: center;
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.65);
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

.day-badge-check-outside {
  background: var(--check-adjacent-bg);
  color: var(--check-adjacent-text);
}

.day-badge-ring {
  box-shadow: 0 0 0 4rpx rgba(79, 110, 247, 0.18);
}

.day-badge-miss {
  background: var(--check-miss-bg);
  border-color: var(--check-miss-border);
  color: var(--check-miss-text);
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

.reward-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.reward-title-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  min-width: 0;
}

.reward-icon {
  width: 56rpx;
  height: 56rpx;
  flex-shrink: 0;
  border-radius: 16rpx;
  background: var(--check-accent-soft);
  color: $orange;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
}

.reward-title {
  display: block;
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.reward-subtitle {
  display: block;
  margin-top: 4rpx;
  font-size: 20rpx;
  color: $text-muted;
}

.reward-days {
  flex-shrink: 0;
  font-size: 22rpx;
  font-weight: 600;
  color: $primary;
}

.reward-days-unit {
  font-size: 20rpx;
  font-weight: 400;
  color: $text-muted;
}

.reward-track {
  height: 12rpx;
  margin-top: 24rpx;
  border-radius: 999rpx;
  background: var(--check-track);
  overflow: hidden;
}

.reward-fill {
  height: 100%;
  border-radius: 999rpx;
  background: $gradient-primary;
  transition: width 0.5s $ease-out;
}

.reward-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
}

.reward-foot-text {
  font-size: 20rpx;
  color: $text-muted;
}

.reward-foot-strong {
  font-weight: 500;
  color: $text-secondary;
}

.makeup-card {
  display: flex;
  align-items: center;
  gap: 24rpx;

  &:active {
    background: $surface-soft;
  }
}

.makeup-icon {
  width: 72rpx;
  height: 72rpx;
  flex-shrink: 0;
  border-radius: 24rpx;
  background: var(--check-accent-soft);
  color: $orange;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
}

.makeup-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.makeup-title {
  font-size: 26rpx;
  font-weight: 500;
  color: $text-primary;
}

.makeup-desc {
  font-size: 20rpx;
  color: $text-muted;
}

.makeup-action {
  flex-shrink: 0;
  font-size: 22rpx;
  color: $text-muted;
}

.makeup-arrow {
  flex-shrink: 0;
  font-size: 22rpx;
  color: $text-muted;
}

.rules-card {
  padding-bottom: 24rpx;
}

.rules-head {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.rules-head-icon {
  font-size: 24rpx;
  color: $text-muted;
}

.rules-title {
  font-size: 24rpx;
  font-weight: 600;
  color: $text-primary;
}

.rule-item {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  margin-top: 12rpx;
}

.rule-dot {
  flex-shrink: 0;
  width: 8rpx;
  height: 8rpx;
  margin-top: 14rpx;
  border-radius: 50%;
  background: $text-muted;
}

.rule-text {
  flex: 1;
  font-size: 20rpx;
  line-height: 34rpx;
  color: $text-secondary;
}

.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 200;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60rpx;
}

.success-card {
  position: relative;
  width: 100%;
  max-width: 620rpx;
  border-radius: 48rpx;
  background: $surface;
  overflow: hidden;
  box-shadow: 0 24rpx 64rpx rgba(15, 17, 21, 0.28);
}

.success-head {
  position: relative;
  padding: 56rpx 32rpx 48rpx;
  background: $gradient-primary;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
}

.success-orb {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
}

.success-orb-lg {
  width: 224rpx;
  height: 224rpx;
  right: -64rpx;
  top: -96rpx;
}

.success-orb-sm {
  width: 160rpx;
  height: 160rpx;
  left: -64rpx;
  bottom: -80rpx;
}

.success-check {
  position: relative;
  width: 128rpx;
  height: 128rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  border: 2rpx solid rgba(255, 255, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: $white;
  font-size: 52rpx;
}

.success-title {
  position: relative;
  margin-top: 24rpx;
  font-size: 36rpx;
  font-weight: 700;
  color: $white;
}

.success-date {
  position: relative;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.7);
}

.success-body {
  padding: 32rpx 40rpx 32rpx;
}

.success-stats {
  display: flex;
  align-items: center;
  padding: 24rpx 12rpx;
  border-radius: $radius-lg;
  background: $surface-soft;
}

.success-stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.success-divider {
  width: 1rpx;
  height: 64rpx;
  background: $border-color;
}

.success-stat-value {
  font-size: 36rpx;
  font-weight: 700;
  line-height: 1;
  color: $text-primary;
}

.success-stat-primary {
  color: $primary;
}

.success-stat-accent {
  color: $orange;
}

.success-stat-label {
  font-size: 18rpx;
  color: $text-muted;
}

.success-extra {
  margin-top: 16rpx;
  padding: 16rpx 24rpx;
  border-radius: 16rpx;
  background: var(--check-accent-soft);
  color: $orange;
  font-size: 22rpx;
  text-align: center;
}

.success-progress {
  margin-top: 32rpx;
}

.success-progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.success-progress-title {
  font-size: 20rpx;
  color: $text-secondary;
}

.success-progress-value {
  font-size: 20rpx;
  font-weight: 500;
  color: $primary;
}

.success-track {
  height: 12rpx;
  margin-top: 12rpx;
  border-radius: 999rpx;
  background: var(--check-track);
  overflow: hidden;
}

.success-fill {
  height: 100%;
  border-radius: 999rpx;
  background: $gradient-primary;
}

.success-progress-tip {
  display: block;
  margin-top: 12rpx;
  font-size: 20rpx;
  color: $text-muted;
}

.success-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 88rpx;
  margin-top: 32rpx;
  border-radius: 999rpx;
  background: $primary;

  &:active {
    opacity: 0.9;
  }
}

.success-btn-text {
  font-size: 28rpx;
  font-weight: 600;
  color: $white;
}

.success-tip {
  display: block;
  padding: 24rpx 0 0;
  text-align: center;
  font-size: 20rpx;
  color: $text-muted;
}
</style>
