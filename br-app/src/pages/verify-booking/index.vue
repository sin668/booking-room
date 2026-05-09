<template>
  <view class="page">
    <view v-if="viewState === 'loading'" class="state-card">
      <view class="loading-spinner" />
      <text class="state-title">正在读取预约</text>
      <text class="state-desc">请稍候，正在校验核销码</text>
    </view>

    <view v-else-if="viewState === 'success'" class="state-card success-card">
      <view class="state-mark success">✓</view>
      <text class="state-title">核销成功</text>
      <text class="state-desc">预约已完成，请勿重复核销</text>
      <view v-if="booking" class="success-summary">
        <text class="success-room">{{ roomName }}</text>
        <text class="success-time">{{ booking.date }} {{ timeRange }}</text>
      </view>
    </view>

    <template v-else>
      <view :class="['status-banner', bannerClass]">
        <text class="status-title">{{ stateTitle }}</text>
        <text class="status-desc">{{ stateDescription }}</text>
      </view>

      <view v-if="booking" class="detail-card">
        <view v-if="viewState === 'unauthorized'" class="admin-token-box">
          <text class="admin-token-label">管理员凭证</text>
          <input
            v-model="adminTokenInput"
            class="admin-token-input"
            password
            placeholder="请输入门店管理员核销口令"
          />
          <button class="admin-token-btn" @tap="saveTokenAndRetry">保存并重试</button>
        </view>

        <view class="user-row">
          <view class="user-avatar">
            <text class="user-avatar-text">{{ userInitial }}</text>
          </view>
          <view class="user-main">
            <text class="user-name">{{ userName }}</text>
            <text class="user-meta">预约编号 {{ booking.id || '-' }}</text>
          </view>
          <view :class="['status-pill', statusClass]">
            <text class="status-pill-text">{{ statusText }}</text>
          </view>
        </view>

        <view class="info-list">
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
          <view class="info-row">
            <text class="info-label">时间段</text>
            <text class="info-value">{{ timeRange }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">金额</text>
            <text class="info-value price">¥{{ priceText }}</text>
          </view>
          <view class="info-row last">
            <text class="info-label">可核销</text>
            <text class="info-value">{{ booking.can_verify ? '是' : '否' }}</text>
          </view>
        </view>
      </view>

      <view v-else class="state-card">
        <view :class="['state-mark', stateMarkClass]">{{ stateMarkText }}</view>
        <text class="state-title">{{ stateTitle }}</text>
        <text class="state-desc">{{ stateDescription }}</text>
      </view>

      <view v-if="viewState === 'unauthorized' && !booking" class="admin-token-card">
        <input
          v-model="adminTokenInput"
          class="admin-token-input"
          password
          placeholder="请输入门店管理员核销口令"
        />
        <button class="primary-token-btn" @tap="saveTokenAndRetry">保存并重试</button>
      </view>

      <button
        v-if="viewState === 'ready'"
        class="confirm-btn"
        :disabled="confirming"
        @tap="handleConfirm"
      >
        {{ confirming ? '核销中...' : '确认核销' }}
      </button>

      <button
        v-if="canRetry"
        class="retry-btn"
        :disabled="loading"
        @tap="inspectToken"
      >
        重新加载
      </button>
    </template>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  confirmVerification,
  getStoredAdminToken,
  inspectVerificationToken,
  saveAdminToken,
} from '@/api/bookingVerifications'

const token = ref('')
const loading = ref(false)
const confirming = ref(false)
const viewState = ref('loading')
const detail = ref(null)
const errorMessage = ref('')
const adminTokenInput = ref(getStoredAdminToken())

const booking = computed(() => detail.value?.booking || null)
const userName = computed(() => booking.value?.user_nickname || '预约用户')
const userInitial = computed(() => userName.value.charAt(0).toUpperCase())
const roomName = computed(() => booking.value?.room_name || booking.value?.store_name || '-')
const seatName = computed(() => booking.value?.seat_number || booking.value?.seat_name || '-')
const timeRange = computed(() => {
  const start = formatTime(booking.value?.start_time)
  const end = formatTime(booking.value?.end_time)
  if (!start && !end) return '-'
  return `${start}-${end}`
})
const priceText = computed(() => {
  const value = booking.value?.total_price ?? booking.value?.amount ?? booking.value?.price
  if (value === undefined || value === null || value === '') return '0.00'
  const num = Number(value)
  return Number.isNaN(num) ? value : num.toFixed(2)
})
const statusText = computed(() => {
  const map = {
    confirmed: '待核销',
    completed: '已核销',
    cancelled: '已取消',
  }
  return map[booking.value?.status] || booking.value?.status || '-'
})
const statusClass = computed(() => {
  return booking.value?.status || 'unknown'
})
const bannerClass = computed(() => {
  if (viewState.value === 'ready') return 'ready'
  if (['expired', 'invalid', 'unauthorized', 'not-verifiable'].includes(viewState.value)) return 'warning'
  return 'neutral'
})
const stateTitle = computed(() => {
  const titles = {
    missing: '缺少核销码',
    unauthorized: '需要员工权限',
    expired: '核销码已过期',
    invalid: '核销码无效',
    completed: '该预约已核销',
    cancelled: '该预约已取消',
    'not-verifiable': '当前不可核销',
    ready: '预约可核销',
    error: '读取失败',
  }
  return titles[viewState.value] || '预约核销'
})
const stateDescription = computed(() => {
  const descriptions = {
    missing: '请使用用户出示的学习码扫码打开本页面',
    unauthorized: '请使用有核销权限的员工账号登录后再操作',
    expired: '请让用户刷新学习码后重新扫码',
    invalid: '请确认链接完整，或让用户重新生成学习码',
    completed: '该预约已经完成核销，不能重复操作',
    cancelled: '该预约已取消，不能到店核销',
    'not-verifiable': '预约状态不满足核销条件',
    ready: '请核对用户和预约信息，确认无误后核销',
    error: errorMessage.value || '网络异常，请稍后重试',
  }
  return descriptions[viewState.value] || ''
})
const stateMarkClass = computed(() => {
  if (viewState.value === 'missing') return 'warning'
  if (viewState.value === 'error') return 'error'
  return 'warning'
})
const stateMarkText = computed(() => {
  if (viewState.value === 'error') return '×'
  return '!'
})
const canRetry = computed(() => ['error', 'unauthorized'].includes(viewState.value) && !!token.value)

function formatTime(value) {
  if (!value) return ''
  return String(value).substring(0, 5)
}

function readToken(options = {}) {
  if (options.token) return decodeURIComponent(options.token)

  // #ifdef H5
  const hash = window.location.hash || ''
  const query = hash.includes('?') ? hash.slice(hash.indexOf('?') + 1) : window.location.search.slice(1)
  const params = new URLSearchParams(query)
  return params.get('token') || ''
  // #endif

  return ''
}

function classifyState(err, fallbackBooking) {
  if (err?.statusCode === 401) return 'unauthorized'
  if (err?.statusCode === 410) return 'expired'
  if (err?.statusCode === 400) return 'invalid'
  if (err?.statusCode === 409 && fallbackBooking?.status === 'completed') return 'completed'
  if (err?.statusCode === 409 && fallbackBooking?.status === 'cancelled') return 'cancelled'
  if (err?.statusCode === 409) return 'not-verifiable'

  const detailText = String(err?.detail || err?.message || '')
  if (detailText.includes('登录') || detailText.includes('认证') || detailText.includes('Unauthorized')) return 'unauthorized'
  if (detailText.includes('过期') || detailText.includes('expired')) return 'expired'
  if (detailText.includes('已核销') || detailText.includes('completed')) return 'completed'
  if (detailText.includes('取消') || detailText.includes('cancelled')) return 'cancelled'
  if (detailText.includes('不可核销') || detailText.includes('not verifiable')) return 'not-verifiable'
  if (detailText.includes('无效') || detailText.includes('invalid')) return 'invalid'
  if (fallbackBooking?.status === 'completed') return 'completed'
  if (fallbackBooking?.status === 'cancelled') return 'cancelled'
  return 'error'
}

function applyDetailState(data) {
  detail.value = data
  const currentBooking = data?.booking || {}
  if (currentBooking.can_verify) {
    viewState.value = 'ready'
  } else if (currentBooking.status === 'completed') {
    viewState.value = 'completed'
  } else if (currentBooking.status === 'cancelled') {
    viewState.value = 'cancelled'
  } else {
    viewState.value = 'not-verifiable'
  }
}

function saveTokenAndRetry() {
  saveAdminToken(adminTokenInput.value.trim())
  inspectToken()
}

async function inspectToken() {
  if (!token.value) {
    viewState.value = 'missing'
    return
  }
  loading.value = true
  viewState.value = 'loading'
  errorMessage.value = ''
  try {
    const data = await inspectVerificationToken(token.value)
    applyDetailState(data)
  } catch (err) {
    errorMessage.value = err?.detail || err?.message || '网络异常，请稍后重试'
    viewState.value = classifyState(err)
  } finally {
    loading.value = false
  }
}

async function handleConfirm() {
  if (!token.value || confirming.value || viewState.value !== 'ready') return
  confirming.value = true
  try {
    const data = await confirmVerification(token.value)
    detail.value = data
    viewState.value = 'success'
  } catch (err) {
    errorMessage.value = err?.detail || err?.message || '核销失败，请稍后重试'
    viewState.value = classifyState(err, booking.value)
  } finally {
    confirming.value = false
  }
}

onLoad((options) => {
  token.value = readToken(options)
  inspectToken()
})
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
  padding: 32rpx 28rpx 52rpx;
  box-sizing: border-box;
}

.state-card,
.detail-card,
.status-banner {
  background: $white;
  border-radius: 28rpx;
  box-shadow: $shadow-sm;
}

.state-card {
  margin-top: 120rpx;
  padding: 58rpx 34rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.success-card {
  margin-top: 80rpx;
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
  width: 92rpx;
  height: 92rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44rpx;
  font-weight: 700;
}

.state-mark.success {
  background: rgba(7, 193, 96, 0.12);
  color: $success;
}

.state-mark.warning {
  background: #fff4e5;
  color: #e67900;
}

.state-mark.error {
  background: rgba(255, 107, 107, 0.12);
  color: $danger;
}

.state-title {
  margin-top: 22rpx;
  font-size: 34rpx;
  font-weight: 700;
  color: $text-primary;
}

.state-desc {
  margin-top: 12rpx;
  font-size: 25rpx;
  line-height: 1.5;
  color: $text-secondary;
}

.success-summary {
  width: 100%;
  margin-top: 34rpx;
  padding: 24rpx;
  border-radius: 18rpx;
  background: #f5f6fa;
}

.success-room,
.success-time {
  display: block;
}

.success-room {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
}

.success-time {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: $text-secondary;
}

.status-banner {
  padding: 30rpx;
}

.status-banner.ready {
  background: linear-gradient(135deg, $primary 0%, $purple 100%);
}

.status-banner.warning {
  background: linear-gradient(135deg, #fff7e8 0%, #ffffff 100%);
}

.status-banner.neutral {
  background: $white;
}

.status-title,
.status-desc {
  display: block;
}

.status-title {
  font-size: 36rpx;
  font-weight: 800;
  color: $text-primary;
}

.status-desc {
  margin-top: 10rpx;
  font-size: 25rpx;
  line-height: 1.45;
  color: $text-secondary;
}

.status-banner.ready .status-title,
.status-banner.ready .status-desc {
  color: $white;
}

.status-banner.ready .status-desc {
  opacity: 0.78;
}

.detail-card {
  margin-top: 24rpx;
  overflow: hidden;
}

.user-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 30rpx;
  border-bottom: 1rpx solid rgba(45, 52, 54, 0.06);
}

.user-avatar {
  width: 78rpx;
  height: 78rpx;
  border-radius: 50%;
  background: $primary-light;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-avatar-text {
  font-size: 30rpx;
  font-weight: 700;
  color: $primary;
}

.user-main {
  min-width: 0;
  flex: 1;
}

.user-name,
.user-meta {
  display: block;
}

.user-name {
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-meta {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.status-pill {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: $primary-light;
}

.status-pill.confirmed {
  background: $primary-light;
}

.status-pill.completed {
  background: rgba(7, 193, 96, 0.12);
}

.status-pill.cancelled {
  background: rgba(255, 107, 107, 0.12);
}

.status-pill-text {
  font-size: 22rpx;
  font-weight: 600;
  color: $primary;
}

.status-pill.completed .status-pill-text {
  color: $success;
}

.status-pill.cancelled .status-pill-text {
  color: $danger;
}

.info-list {
  padding: 8rpx 30rpx;
}

.info-row {
  min-height: 84rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28rpx;
  border-bottom: 1rpx solid rgba(45, 52, 54, 0.06);
}

.info-row.last {
  border-bottom: none;
}

.info-label {
  font-size: 26rpx;
  color: $text-secondary;
}

.info-value {
  min-width: 0;
  flex: 1;
  text-align: right;
  font-size: 27rpx;
  font-weight: 600;
  color: $text-primary;
  overflow-wrap: anywhere;
}

.info-value.price {
  color: #e67900;
}

.confirm-btn,
.retry-btn {
  margin-top: 32rpx;
  height: 90rpx;
  line-height: 90rpx;
  border: none;
  border-radius: 22rpx;
  font-size: 30rpx;
  font-weight: 700;

  &::after { border: none; }
}

.confirm-btn {
  background: $primary;
  color: $white;
  box-shadow: 0 10rpx 24rpx rgba(79, 110, 247, 0.24);
}

.retry-btn {
  background: $white;
  color: $primary;
  box-shadow: $shadow-sm;
}

.admin-token-box {
  margin: 24rpx 30rpx 0;
  padding: 24rpx;
  border-radius: 18rpx;
  background: #fff7e8;
}

.admin-token-card {
  margin-top: 24rpx;
  padding: 28rpx;
  border-radius: 24rpx;
  background: $white;
  box-shadow: $shadow-sm;
}

.admin-token-label {
  display: block;
  margin-bottom: 14rpx;
  font-size: 24rpx;
  color: $text-secondary;
}

.admin-token-input {
  height: 82rpx;
  padding: 0 22rpx;
  border-radius: 16rpx;
  background: #f5f6fa;
  font-size: 26rpx;
  color: $text-primary;
  box-sizing: border-box;
}

.admin-token-btn,
.primary-token-btn {
  margin-top: 18rpx;
  height: 78rpx;
  line-height: 78rpx;
  border: none;
  border-radius: 18rpx;
  font-size: 27rpx;
  font-weight: 700;
  background: $primary;
  color: $white;

  &::after { border: none; }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
