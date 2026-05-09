<template>
  <view class="page">
    <view v-if="loading && !verification" class="state-card top-state">
      <view class="loading-spinner" />
      <text class="state-title">正在生成学习码</text>
      <text class="state-desc">请稍候，核销码仅短时间有效</text>
    </view>

    <view v-else-if="state === 'login'" class="state-card top-state">
      <view class="state-mark warning">!</view>
      <text class="state-title">请先登录</text>
      <text class="state-desc">登录后可生成到店核销学习码</text>
      <button class="primary-btn" @tap="goLogin">去登录</button>
    </view>

    <view v-else-if="state === 'empty'" class="state-card top-state">
      <view class="state-mark empty">-</view>
      <text class="state-title">暂无可核销预约</text>
      <text class="state-desc">当前没有待到店核销的预约，预约成功后再来查看</text>
      <view class="state-actions">
        <button class="secondary-btn" @tap="goBooking">去预约</button>
        <button class="primary-btn compact" :disabled="loading" @tap="loadToken">刷新</button>
      </view>
    </view>

    <view v-else-if="state === 'error'" class="state-card top-state">
      <view class="state-mark error">×</view>
      <text class="state-title">学习码生成失败</text>
      <text class="state-desc">{{ errorMessage }}</text>
      <button class="primary-btn" :disabled="loading" @tap="loadToken">重试</button>
    </view>

    <template v-else>
      <view class="user-block">
        <view class="avatar">
          <text class="avatar-text">{{ avatarText }}</text>
        </view>
        <text class="nickname">{{ displayName }}</text>
        <view class="member-badge">
          <text class="member-badge-text">VIP会员</text>
        </view>
      </view>

      <view class="qr-card">
        <view class="qr-shell">
          <image class="qr-image" :src="qrImageSrc" mode="aspectFit" />
        </view>
        <text class="qr-title">到店出示此码即可核销</text>
        <text class="qr-subtitle">核销码 {{ countdownText }} 后失效</text>
        <button class="refresh-btn" :disabled="loading" @tap="loadToken">
          {{ loading ? '刷新中...' : '刷新核销码' }}
        </button>
      </view>

      <view class="info-card">
        <view class="info-row">
          <text class="info-label">预约编号</text>
          <text class="info-value">{{ booking.id || '-' }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">门店</text>
          <text class="info-value">{{ roomName }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">座位</text>
          <text class="info-value">{{ seatName }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">日期</text>
          <text class="info-value">{{ booking.date || '-' }}</text>
        </view>
        <view class="info-row last">
          <text class="info-label">时间段</text>
          <text class="info-value">{{ timeRange }}</text>
        </view>
      </view>

      <view class="link-card">
        <text class="link-label">核销链接</text>
        <text class="link-value">{{ displayVerifyUrl }}</text>
        <button class="copy-btn" @tap="copyVerifyUrl">复制链接</button>
      </view>

      <view class="tip">
        <text class="tip-icon">盾</text>
        <text class="tip-text">请勿截图分享，核销码 5 分钟内有效且仅限本人当次预约使用</text>
      </view>
    </template>
  </view>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { issueVerificationToken } from '@/api/bookingVerifications'
import { useUserStore } from '@/store/modules/user'
import { createQrSvgDataUrl } from '@/utils/qrcode'

const userStore = useUserStore()

const loading = ref(false)
const state = ref('loading')
const verification = ref(null)
const qrImageSrc = ref('')
const errorMessage = ref('网络异常，请稍后重试')
const remainingSeconds = ref(0)
let countdownTimer = null

const booking = computed(() => verification.value?.booking || {})
const displayVerifyUrl = computed(() => toAbsoluteVerifyUrl(verification.value?.verify_url || ''))
const displayName = computed(() => {
  return booking.value.user_nickname || userStore.nickname || '学习达人'
})
const avatarText = computed(() => {
  return (displayName.value || userStore.phone || 'U').charAt(0).toUpperCase()
})
const roomName = computed(() => booking.value.room_name || booking.value.store_name || '-')
const seatName = computed(() => booking.value.seat_number || booking.value.seat_name || '-')
const timeRange = computed(() => {
  const start = formatTime(booking.value.start_time)
  const end = formatTime(booking.value.end_time)
  if (!start && !end) return '-'
  return `${start}-${end}`
})
const countdownText = computed(() => {
  const minutes = Math.floor(remainingSeconds.value / 60)
  const seconds = remainingSeconds.value % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
})

function formatTime(value) {
  if (!value) return ''
  return String(value).substring(0, 5)
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

function startCountdown(expiresAt) {
  stopCountdown()
  const update = () => {
    const expiresTime = new Date(expiresAt).getTime()
    const diff = Math.max(0, Math.floor((expiresTime - Date.now()) / 1000))
    remainingSeconds.value = diff
    if (diff <= 0) stopCountdown()
  }
  update()
  countdownTimer = setInterval(update, 1000)
}

function normalizeError(err) {
  const detail = err?.detail || err?.message || ''
  if (detail.includes('登录') || detail.includes('认证') || detail.includes('Unauthorized')) {
    return { state: 'login', message: '请先登录后再生成学习码' }
  }
  if (detail.includes('暂无') || detail.includes('No verifiable') || detail.includes('not found')) {
    return { state: 'empty', message: '暂无可核销预约' }
  }
  return { state: 'error', message: detail || '网络异常，请稍后重试' }
}

function toAbsoluteVerifyUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  // #ifdef H5
  if (url.startsWith('/')) return `${window.location.origin}${url}`
  // #endif
  return url
}

async function loadToken() {
  if (!userStore.isLoggedIn) {
    state.value = 'login'
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await issueVerificationToken()
    verification.value = data
    qrImageSrc.value = createQrSvgDataUrl(toAbsoluteVerifyUrl(data.verify_url))
    state.value = 'ready'
    startCountdown(data.expires_at)
  } catch (err) {
    stopCountdown()
    verification.value = null
    qrImageSrc.value = ''
    const normalized = normalizeError(err)
    state.value = normalized.state
    errorMessage.value = normalized.message
  } finally {
    loading.value = false
  }
}

function copyVerifyUrl() {
  if (!displayVerifyUrl.value) return
  uni.setClipboardData({
    data: displayVerifyUrl.value,
    success: () => {
      uni.showToast({ title: '已复制核销链接', icon: 'none' })
    },
  })
}

function goLogin() {
  uni.navigateTo({ url: '/pages/login/login' })
}

function goBooking() {
  uni.switchTab({ url: '/pages/booking/index' })
}

onMounted(() => {
  loadToken()
})

onUnmounted(() => {
  stopCountdown()
})
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
  padding: 32rpx 28rpx 48rpx;
  box-sizing: border-box;
}

.user-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 22rpx;
}

.avatar {
  width: 132rpx;
  height: 132rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, $primary, $purple);
  border: 6rpx solid $white;
  box-shadow: 0 10rpx 26rpx rgba(79, 110, 247, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-text {
  color: $white;
  font-size: 46rpx;
  font-weight: 700;
}

.nickname {
  margin-top: 18rpx;
  font-size: 34rpx;
  font-weight: 700;
  color: $text-primary;
}

.member-badge {
  margin-top: 10rpx;
  padding: 6rpx 18rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #ffd666, #ff9f43);
}

.member-badge-text {
  font-size: 20rpx;
  font-weight: 600;
  color: #6b4200;
}

.qr-card,
.info-card,
.link-card,
.state-card {
  background: $white;
  border-radius: 28rpx;
  box-shadow: $shadow-sm;
}

.qr-card {
  margin-top: 36rpx;
  padding: 40rpx 32rpx 34rpx;
  text-align: center;
}

.qr-shell {
  width: 392rpx;
  height: 392rpx;
  margin: 0 auto;
  border: 1rpx solid rgba(45, 52, 54, 0.08);
  border-radius: 22rpx;
  padding: 24rpx;
  box-sizing: border-box;
}

.qr-image {
  width: 100%;
  height: 100%;
  display: block;
}

.qr-title {
  display: block;
  margin-top: 28rpx;
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.qr-subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $danger;
}

.refresh-btn,
.primary-btn,
.secondary-btn,
.copy-btn {
  border: none;
  border-radius: 999rpx;

  &::after { border: none; }
}

.refresh-btn {
  margin-top: 24rpx;
  width: 260rpx;
  height: 72rpx;
  line-height: 72rpx;
  background: $primary;
  color: $white;
  font-size: 26rpx;
  font-weight: 600;
}

.info-card {
  margin-top: 24rpx;
  padding: 8rpx 28rpx;
}

.info-row {
  min-height: 82rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28rpx;
  border-bottom: 1rpx solid rgba(45, 52, 54, 0.06);
}

.info-row.last {
  border-bottom: none;
}

.info-label,
.link-label {
  font-size: 26rpx;
  color: $text-secondary;
}

.info-value {
  min-width: 0;
  flex: 1;
  text-align: right;
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
  overflow-wrap: anywhere;
}

.link-card {
  margin-top: 24rpx;
  padding: 28rpx;
}

.link-label,
.link-value {
  display: block;
}

.link-value {
  margin-top: 12rpx;
  padding: 18rpx;
  border-radius: 16rpx;
  background: #f5f6fa;
  font-size: 22rpx;
  line-height: 1.45;
  color: $text-secondary;
  overflow-wrap: anywhere;
}

.copy-btn {
  margin-top: 18rpx;
  height: 68rpx;
  line-height: 68rpx;
  background: $primary-light;
  color: $primary;
  font-size: 25rpx;
}

.tip {
  margin-top: 28rpx;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 10rpx;
  padding: 0 18rpx;
}

.tip-icon,
.tip-text {
  font-size: 22rpx;
  color: $text-muted;
}

.tip-text {
  line-height: 1.45;
}

.top-state {
  margin-top: 120rpx;
}

.state-card {
  padding: 56rpx 34rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.loading-spinner {
  width: 54rpx;
  height: 54rpx;
  border: 6rpx solid $primary-light;
  border-top-color: $primary;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.state-mark {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44rpx;
  font-weight: 700;
}

.state-mark.warning {
  background: #fff4e5;
  color: #e67900;
}

.state-mark.empty {
  background: $primary-light;
  color: $primary;
}

.state-mark.error {
  background: rgba(255, 107, 107, 0.12);
  color: $danger;
}

.state-title {
  margin-top: 22rpx;
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
}

.state-desc {
  margin-top: 12rpx;
  font-size: 25rpx;
  line-height: 1.5;
  color: $text-secondary;
}

.state-actions {
  width: 100%;
  margin-top: 32rpx;
  display: flex;
  gap: 18rpx;
}

.primary-btn,
.secondary-btn {
  margin-top: 32rpx;
  width: 320rpx;
  height: 78rpx;
  line-height: 78rpx;
  font-size: 27rpx;
  font-weight: 600;
}

.state-actions .primary-btn,
.state-actions .secondary-btn {
  flex: 1;
  width: auto;
  margin-top: 0;
}

.primary-btn {
  background: $primary;
  color: $white;
}

.secondary-btn {
  background: $primary-light;
  color: $primary;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
