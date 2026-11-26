<template>
  <view class="page" :class="themeClass">
    <view v-if="loading && !summary.today" class="loading-state">
      <view class="loading-spinner" />
      <text class="loading-text">加载中...</text>
    </view>

    <template v-else>
      <view class="hero">
        <view class="hero-orbit hero-orbit-lg" />
        <view class="hero-orbit hero-orbit-sm" />

        <view class="hero-main">
          <view class="hero-streak">
            <view class="hero-fire">
              <view class="icon icon-fire" />
            </view>
            <view class="hero-streak-text">
              <text class="hero-label">已连续签到</text>
              <view class="hero-streak-value">
                <text class="hero-streak-num">{{ summary.streak }}</text>
                <text class="hero-streak-unit">天</text>
              </view>
            </view>
          </view>
          <view class="hero-stats">
            <view class="hero-stat">
              <text class="hero-stat-value">{{ summary.total_days }}</text>
              <text class="hero-stat-label">累计签到</text>
            </view>
            <view class="hero-stat">
              <text class="hero-stat-value">{{ summary.points }}</text>
              <text class="hero-stat-label">积分</text>
            </view>
            <view class="hero-stat">
              <text class="hero-stat-value">{{ summary.makeup_cards }}</text>
              <text class="hero-stat-label">补签卡</text>
            </view>
          </view>
        </view>
        <text class="hero-hint">{{ heroHint }}</text>
      </view>

      <view
        class="sign-btn"
        :class="{ 'sign-btn-disabled': !canSign }"
        @tap="onSign"
      >
        <text class="sign-btn-text">{{ signButtonText }}</text>
      </view>

      <view class="card calendar-card">
        <view class="calendar-head">
          <view class="month-arrow" @tap="changeMonth(-1)">
            <view class="icon icon-arrow-right month-arrow-icon prev" />
          </view>
          <text class="month-text">{{ monthLabel }}</text>
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
            v-for="(cell, index) in calendarCells"
            :key="index"
            class="day-cell"
            :class="{ 'day-cell-today': cell && cell.isToday, 'day-cell-missed': cell && cell.missed }"
            @tap="onCellTap(cell)"
          >
            <template v-if="cell">
              <text
                class="day-num"
                :class="{ 'day-num-muted': cell.signed || cell.missed, 'day-num-future': cell.future && !cell.signed && !cell.missed }"
              >{{ cell.day }}</text>
              <text v-if="cell.signed" class="day-mark day-mark-check">✓</text>
              <text v-else-if="cell.missed" class="day-mark day-mark-miss">✕</text>
              <text v-else-if="cell.isToday" class="day-mark day-mark-today">签</text>
              <text v-else-if="cell.projected" class="day-mark day-mark-projected">{{ cell.projected }}</text>
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
            <text class="legend-text">缺签</text>
          </view>
          <view class="legend-item">
            <text class="legend-mark legend-mark-future">8</text>
            <text class="legend-text">未开始</text>
          </view>
        </view>
      </view>

      <view class="card reward-card">
        <view class="reward-head">
          <view class="reward-title-row">
            <view class="reward-icon">
              <view class="icon icon-ticket" />
            </view>
            <view>
              <text class="reward-title">连续签到 30 天</text>
              <text class="reward-subtitle">赠 1 张补签卡</text>
            </view>
          </view>
          <text class="reward-left">再签 {{ nextRewardDays }} 天</text>
        </view>
        <view class="reward-track">
          <view class="reward-fill" :style="{ width: `${rewardProgress}%` }" />
        </view>
        <view class="reward-foot">
          <text class="reward-foot-text">{{ rewardProgressText }}</text>
          <text class="reward-foot-text">每日签到 +5 积分</text>
        </view>
      </view>

      <view class="card makeup-card" @tap="goMakeup">
        <view class="makeup-icon">
          <view class="icon icon-ticket" />
        </view>
        <view class="makeup-info">
          <text class="makeup-title">补签卡</text>
          <text class="makeup-desc">{{ makeupHint }}</text>
        </view>
        <view class="makeup-right">
          <text class="makeup-count">{{ summary.makeup_cards }}张</text>
          <view class="icon icon-arrow-right makeup-arrow" />
        </view>
      </view>

      <view class="card rules-card">
        <text class="rules-title">签到规则</text>
        <view class="rule-item">
          <text class="rule-index">1</text>
          <text class="rule-text">每日可签到 1 次，签到成功即获得 5 积分。</text>
        </view>
        <view class="rule-item">
          <text class="rule-index">2</text>
          <text class="rule-text">连续签到 7 天，额外奖励 20 积分。</text>
        </view>
        <view class="rule-item">
          <text class="rule-index">3</text>
          <text class="rule-text">连续签到中断后，连续天数将从下一次签到重新计算。</text>
        </view>
        <view class="rule-item">
          <text class="rule-index">4</text>
          <text class="rule-text">每张补签卡可补签 1 天，仅支持近 30 天内的漏签日期。</text>
        </view>
      </view>
    </template>

    <view v-if="showSuccess" class="modal-mask" @tap="closeSuccess">
      <view class="success-card" @tap.stop>
        <view class="success-close" @tap="closeSuccess">
          <view class="icon icon-close" />
        </view>
        <view class="success-head">
          <view class="success-check">
            <text class="success-check-mark">✓</text>
          </view>
          <text class="success-title">签到成功</text>
          <text class="success-date">{{ formatDate(summary.today) }}</text>
        </view>
        <view class="success-body">
          <view class="success-stats">
            <view class="success-stat">
              <text class="success-stat-value">+{{ rewardPoints }}</text>
              <text class="success-stat-label">获得积分</text>
            </view>
            <view class="success-stat">
              <text class="success-stat-value">{{ summary.streak }}天</text>
              <text class="success-stat-label">连续签到</text>
            </view>
            <view class="success-stat">
              <text class="success-stat-value">{{ summary.total_days }}天</text>
              <text class="success-stat-label">累计签到</text>
            </view>
          </view>
          <view v-if="rewardCards > 0" class="success-extra">连续 30 天奖励：补签卡 +{{ rewardCards }}</view>
          <view class="success-progress">
            <view class="success-progress-head">
              <text class="success-progress-title">连签 30 天奖励</text>
              <text class="success-progress-value">{{ streakInCycle }}/30</text>
            </view>
            <view class="success-track">
              <view class="success-fill" :style="{ width: `${rewardProgress}%` }" />
            </view>
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

const weekdays = ['一', '二', '三', '四', '五', '六', '日']

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
    ? '明天再来签到，连续天数将继续累积'
    : '今日签到可得 5 积分 · 连续 7 天额外 +20 积分'
)

const nextRewardDays = computed(() => 30 - (summary.value.streak % 30))
const streakInCycle = computed(() => summary.value.streak % 30)
const rewardProgress = computed(() =>
  Math.min(100, Math.round((streakInCycle.value / 30) * 100))
)
const rewardProgressText = computed(() =>
  todaySigned.value
    ? '今日进度已记录，继续加油'
    : '今日还未签到，签到后计入进度'
)

const makeupHint = computed(() => {
  const count = summary.value.missed_dates.length
  if (count > 0) {
    return `当前有 ${count} 天漏签，可使用补签卡恢复连续签到`
  }
  return '近 30 天暂无漏签日期'
})

const calendarCells = computed(() => {
  const marks = summary.value.calendar_mark || []
  if (!marks.length) return []

  const firstDay = parseDate(marks[0].date).getDay()
  const offset = (firstDay + 6) % 7
  const cells = Array.from({ length: offset }, () => null)

  for (const mark of marks) {
    const dateObj = parseDate(mark.date)
    const future = mark.date > summary.value.today
    cells.push({
      date: mark.date,
      day: dateObj.getDate(),
      signed: mark.signed,
      missed: mark.missed,
      eligible: mark.makeup_eligible,
      isToday: mark.date === summary.value.today,
      future,
      projected: future ? projectedStreak(mark.date) : 0,
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

function projectedStreak(dateStr) {
  const base = summary.value.streak
  if (base === 0 && !summary.value.today_signed) return 0
  const diff = Math.round(
    (parseDate(dateStr) - parseDate(summary.value.today)) / 86400000
  )
  return base + diff + (summary.value.today_signed ? 0 : 1)
}

function formatDate(value) {
  if (!value) return ''
  const [year, month, day] = value.split('-')
  return `${year}年${Number(month)}月${Number(day)}日`
}

function errorMessage(error, fallback) {
  if (error && typeof error.detail === 'string') return error.detail
  return fallback
}

async function loadSummary() {
  loading.value = true
  try {
    summary.value = await getCheckinSummary({ month: monthKey.value })
  } catch (error) {
    summary.value = emptySummary()
    uni.showToast({ title: errorMessage(error, '签到数据加载失败'), icon: 'none' })
  } finally {
    loading.value = false
  }
}

function applySummary(nextSummary) {
  if (nextSummary) {
    summary.value = nextSummary
    if (nextSummary.today) {
      monthCursor.value = nextSummary.today.slice(0, 7)
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
  const [year, month] = monthCursor.value.split('-').map(Number)
  const next = new Date(year, month - 1 + delta, 1)
  monthCursor.value = `${next.getFullYear()}-${pad(next.getMonth() + 1)}`
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
  min-height: 100vh;
  background: $bg-color;
  padding: 24rpx 0 48rpx;
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
  margin: 0 32rpx;
  padding: 40rpx 36rpx 34rpx;
  border-radius: $radius-2xl;
  background: $gradient-primary;
  overflow: hidden;
  box-shadow: $shadow-float;
}

.hero-orbit {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
}

.hero-orbit-lg {
  width: 320rpx;
  height: 320rpx;
  right: -120rpx;
  top: -150rpx;
}

.hero-orbit-sm {
  width: 160rpx;
  height: 160rpx;
  right: 80rpx;
  bottom: -90rpx;
  background: rgba(255, 255, 255, 0.08);
}

.hero-main {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.hero-streak {
  display: flex;
  align-items: center;
  gap: 18rpx;
  min-width: 0;
}

.hero-fire {
  width: 72rpx;
  height: 72rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFD8A8;
  font-size: 40rpx;
}

.hero-streak-text {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.hero-label {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.75);
}

.hero-streak-value {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.hero-streak-num {
  font-size: 64rpx;
  line-height: 1;
  font-weight: 700;
  color: $white;
}

.hero-streak-unit {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.hero-stats {
  display: flex;
  gap: 12rpx;
}

.hero-stat {
  min-width: 96rpx;
  padding: 14rpx 12rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.12);
  border: 1rpx solid rgba(255, 255, 255, 0.16);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
}

.hero-stat-value {
  font-size: 32rpx;
  font-weight: 600;
  color: $white;
}

.hero-stat-label {
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.7);
}

.hero-hint {
  position: relative;
  display: block;
  margin-top: 26rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.72);
}

.sign-btn {
  margin: 28rpx 32rpx 0;
  height: 92rpx;
  border-radius: 28rpx;
  background: $surface;
  border: 2rpx solid $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow-card;

  &:active {
    transform: scale(0.99);
  }
}

.sign-btn-disabled {
  background: $surface-muted;
  border-color: $border-color;
  box-shadow: none;
}

.sign-btn-text {
  font-size: 30rpx;
  font-weight: 600;
  color: $primary;
}

.sign-btn-disabled .sign-btn-text {
  color: $text-muted;
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
  border-color: rgba(79, 110, 247, 0.18);
}

.day-cell-missed:active {
  background: $danger-light;
}

.day-num {
  font-size: 26rpx;
  color: $text-primary;
}

.day-num-muted {
  color: $text-secondary;
}

.day-num-future {
  color: $text-muted;
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

.day-mark-today {
  color: $primary;
}

.day-mark-projected {
  color: $primary;
  opacity: 0.65;
  font-weight: 500;
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

.legend-mark-future {
  color: $primary;
  opacity: 0.6;
}

.legend-text {
  font-size: 22rpx;
  color: $text-muted;
}

.reward-card {
  padding-bottom: 26rpx;
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
}

.reward-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 20rpx;
  background: $orange-light;
  color: $orange;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
}

.reward-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.reward-subtitle {
  display: block;
  margin-top: 4rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.reward-left {
  font-size: 22rpx;
  color: $text-secondary;
}

.reward-track {
  height: 12rpx;
  margin-top: 24rpx;
  border-radius: 999rpx;
  background: $bg-color;
  overflow: hidden;
}

.reward-fill {
  height: 100%;
  border-radius: 999rpx;
  background: $gradient-primary;
  transition: width 0.3s $ease-out;
}

.reward-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14rpx;
}

.reward-foot-text {
  font-size: 20rpx;
  color: $text-muted;
}

.makeup-card {
  display: flex;
  align-items: center;
  gap: 20rpx;

  &:active {
    background: $surface-soft;
  }
}

.makeup-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 22rpx;
  background: $primary-soft;
  color: $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
}

.makeup-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.makeup-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.makeup-desc {
  font-size: 22rpx;
  color: $text-muted;
}

.makeup-right {
  display: flex;
  align-items: center;
  gap: 8rpx;
  flex-shrink: 0;
}

.makeup-count {
  font-size: 26rpx;
  font-weight: 600;
  color: $primary;
}

.makeup-arrow {
  font-size: 24rpx;
  color: $text-muted;
}

.rules-card {
  padding-bottom: 22rpx;
}

.rules-title {
  display: block;
  margin-bottom: 20rpx;
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.rule-item {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  margin-bottom: 14rpx;
}

.rule-index {
  flex-shrink: 0;
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  background: $primary-soft;
  color: $primary;
  font-size: 20rpx;
  text-align: center;
  line-height: 32rpx;
}

.rule-text {
  flex: 1;
  font-size: 22rpx;
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
  background: rgba(15, 17, 21, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48rpx;
}

.success-card {
  position: relative;
  width: 100%;
  max-width: 620rpx;
  border-radius: $radius-2xl;
  background: $surface;
  overflow: hidden;
  box-shadow: 0 24rpx 64rpx rgba(15, 17, 21, 0.24);
}

.success-close {
  position: absolute;
  top: 20rpx;
  right: 20rpx;
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: $white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  z-index: 2;
}

.success-head {
  padding: 48rpx 32rpx 36rpx;
  background: $gradient-primary;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.success-check {
  width: 104rpx;
  height: 104rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.18);
  border: 3rpx solid rgba(255, 255, 255, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8rpx;
}

.success-check-mark {
  font-size: 52rpx;
  color: $white;
  font-weight: 700;
}

.success-title {
  font-size: 36rpx;
  font-weight: 700;
  color: $white;
}

.success-date {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.75);
}

.success-body {
  padding: 30rpx 32rpx 36rpx;
}

.success-stats {
  display: flex;
  gap: 12rpx;
}

.success-stat {
  flex: 1;
  padding: 18rpx 8rpx;
  border-radius: 20rpx;
  background: $bg-color;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
}

.success-stat-value {
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
}

.success-stat-label {
  font-size: 20rpx;
  color: $text-muted;
}

.success-extra {
  margin-top: 16rpx;
  padding: 14rpx 20rpx;
  border-radius: 16rpx;
  background: $orange-light;
  color: $orange;
  font-size: 22rpx;
  text-align: center;
}

.success-progress {
  margin-top: 24rpx;
  padding: 22rpx;
  border-radius: 20rpx;
  background: $surface-soft;
  border: 1rpx solid $border-soft;
}

.success-progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14rpx;
}

.success-progress-title {
  font-size: 22rpx;
  color: $text-secondary;
}

.success-progress-value {
  font-size: 22rpx;
  font-weight: 600;
  color: $primary;
}

.success-track {
  height: 10rpx;
  border-radius: 999rpx;
  background: $bg-color;
  overflow: hidden;
}

.success-fill {
  height: 100%;
  border-radius: 999rpx;
  background: $gradient-primary;
}

.success-btn {
  margin-top: 28rpx;
  height: 84rpx;
  border-radius: 24rpx;
  background: $gradient-primary;
  display: flex;
  align-items: center;
  justify-content: center;

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
  margin-top: 18rpx;
  text-align: center;
  font-size: 20rpx;
  color: $text-muted;
}
</style>
