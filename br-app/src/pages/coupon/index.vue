<template>
  <view class="page">
    <view class="tabs">
      <view
        v-for="tab in tabs"
        :key="tab.value"
        :class="['tab-item', { active: currentStatus === tab.value }]"
        @tap="switchStatus(tab.value)"
      >
        <view class="tab-label-row">
          <text class="tab-text">{{ tab.label }}</text>
          <text
            v-if="tab.value === 'available' && availableCount > 0"
            class="tab-badge"
          >{{ availableCount }}</text>
        </view>
        <view v-if="currentStatus === tab.value" class="tab-indicator" />
      </view>
    </view>

    <scroll-view
      class="coupon-scroll"
      scroll-y
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="refreshCoupons"
    >
      <view v-if="loading && coupons.length === 0" class="loading-state">
        <view v-for="i in 3" :key="i" class="skeleton-card">
          <view class="skeleton-bar" />
          <view class="skeleton-content">
            <view class="skeleton-row title" />
            <view class="skeleton-row short" />
            <view class="skeleton-row date" />
          </view>
        </view>
      </view>

      <view v-else-if="loadError" class="state-wrap">
        <view class="state-icon error-icon">
          <text class="state-icon-text">!</text>
        </view>
        <text class="state-text">卡券加载失败，请重试</text>
        <view class="retry-btn" @tap="loadCoupons(currentStatus)">
          <text class="retry-btn-text">重新加载</text>
        </view>
      </view>

      <view v-else-if="coupons.length === 0" class="state-wrap">
        <view class="state-icon ticket-empty">
          <view class="ticket-hole left" />
          <view class="ticket-hole right" />
          <view class="ticket-line main" />
          <view class="ticket-line sub" />
        </view>
        <text class="state-text">{{ emptyText }}</text>
      </view>

      <view v-else class="coupon-list">
        <view
          v-for="coupon in coupons"
          :key="coupon.id"
          :class="['coupon-card', `status-${currentStatus}`]"
        >
          <view :class="['coupon-bar', couponTone(coupon)]" />
          <view class="coupon-body">
            <view class="coupon-main">
              <view class="coupon-info">
                <text :class="['coupon-title', couponTone(coupon)]">{{ couponTitle(coupon) }}</text>
                <text class="coupon-scope">{{ scopeText(coupon) }}</text>
              </view>
              <view
                v-if="currentStatus === 'available'"
                class="use-btn"
                @tap="useCoupon"
              >
                <text class="use-btn-text">立即使用</text>
              </view>
              <view v-else class="status-stamp">
                <text class="status-stamp-text">{{ statusText }}</text>
              </view>
            </view>
            <view class="coupon-footer">
              <text class="coupon-desc">{{ coupon.description || typeText(coupon.type) }}</text>
              <text class="coupon-expiry">{{ expiryText(coupon) }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="bottom-safe" />
    </scroll-view>
  </view>
</template>

<script>
import { getCoupons } from '@/api/coupons'

const TABS = [
  { label: '可使用', value: 'available' },
  { label: '已使用', value: 'used' },
  { label: '已过期', value: 'expired' },
]

const EMPTY_TEXT = {
  available: '暂无可使用的优惠券',
  used: '暂无已使用的优惠券',
  expired: '暂无已过期的优惠券',
}

const SCOPE_TEXT = {
  all: '全场通用',
  first_booking: '限首次预约',
  seat_zone: '指定座位可用',
}

const ZONE_TEXT = {
  quiet: '静音区',
  keyboard: '键盘区',
  vip: 'VIP区',
}

const TYPE_TEXT = {
  amount_off: '立减券',
  threshold_amount_off: '满减券',
  percentage_off: '折扣券',
}

export default {
  data() {
    return {
      tabs: TABS,
      currentStatus: 'available',
      coupons: [],
      availableCount: 0,
      loading: false,
      refreshing: false,
      loadError: false,
      loadRequestId: 0,
      availableCountRequestId: 0,
    }
  },

  computed: {
    emptyText() {
      return EMPTY_TEXT[this.currentStatus]
    },

    statusText() {
      return this.currentStatus === 'used' ? '已使用' : '已过期'
    },
  },

  onLoad() {
    this.loadCoupons('available')
  },

  onShow() {
    this.loadCoupons(this.currentStatus, { silent: this.coupons.length > 0 })
    if (this.currentStatus !== 'available') {
      this.loadAvailableCount()
    }
  },

  methods: {
    async loadCoupons(status, options = {}) {
      const requestId = ++this.loadRequestId
      this.loading = !options.silent
      this.loadError = false
      try {
        const data = await getCoupons(status)
        const items = Array.isArray(data) ? data : ((data && data.items) || [])
        if (requestId !== this.loadRequestId || status !== this.currentStatus) return
        this.coupons = items
        if (status === 'available') {
          this.availableCountRequestId += 1
          this.availableCount = items.length
        }
      } catch {
        if (requestId !== this.loadRequestId || status !== this.currentStatus) return
        this.coupons = []
        this.loadError = true
      } finally {
        if (requestId === this.loadRequestId) {
          this.loading = false
          this.refreshing = false
        }
      }
    },

    async loadAvailableCount() {
      const requestId = ++this.availableCountRequestId
      try {
        const data = await getCoupons('available')
        const items = Array.isArray(data) ? data : ((data && data.items) || [])
        if (requestId !== this.availableCountRequestId) return
        this.availableCount = items.length
      } catch {
        // Keep the last known badge count when the background refresh fails.
      }
    },

    switchStatus(status) {
      if (this.currentStatus === status) return
      this.currentStatus = status
      this.coupons = []
      this.loadCoupons(status)
    },

    refreshCoupons() {
      this.refreshing = true
      this.loadCoupons(this.currentStatus)
    },

    useCoupon() {
      uni.switchTab({ url: '/pages/booking/index' })
    },

    couponTitle(coupon) {
      if (coupon.name) return coupon.name
      if (coupon.type === 'percentage_off' && coupon.discount_percent) {
        return `${this.trimNumber(coupon.discount_percent / 10)}折优惠`
      }
      if (coupon.type === 'threshold_amount_off') {
        return `满${this.money(coupon.min_order_amount)}减${this.money(coupon.discount_amount)}`
      }
      if (coupon.discount_amount) {
        return `立减${this.money(coupon.discount_amount)}`
      }
      return TYPE_TEXT[coupon.type] || '优惠券'
    },

    scopeText(coupon) {
      if (coupon.scope === 'seat_zone' && coupon.seat_zone) {
        return `限${ZONE_TEXT[coupon.seat_zone] || coupon.seat_zone}`
      }
      return SCOPE_TEXT[coupon.scope] || coupon.scope || '全场通用'
    },

    typeText(type) {
      return TYPE_TEXT[type] || '优惠券'
    },

    expiryText(coupon) {
      if (this.currentStatus === 'used' && coupon.used_at) {
        return `使用于 ${this.formatDate(coupon.used_at)}`
      }
      if (!coupon.expires_at) return '有效期以门店规则为准'
      return `有效期至 ${this.formatDate(coupon.expires_at)}`
    },

    formatDate(value) {
      return String(value).slice(0, 10)
    },

    money(value) {
      if (value === null || value === undefined || value === '') return '0'
      return this.trimNumber(Number(value))
    },

    trimNumber(value) {
      if (!Number.isFinite(value)) return '0'
      return Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/\.?0+$/, '')
    },

    couponTone(coupon) {
      if (this.currentStatus !== 'available') return 'muted'
      if (coupon.type === 'percentage_off') return 'purple'
      if (coupon.scope === 'first_booking') return 'orange'
      return 'red'
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
  display: flex;
  flex-direction: column;
}

.tabs {
  height: 88rpx;
  display: flex;
  align-items: center;
  background: $white;
  border-top: 1rpx solid rgba(45, 52, 54, 0.04);
  box-shadow: 0 2rpx 10rpx rgba(45, 52, 54, 0.03);
  z-index: 2;
}

.tab-item {
  flex: 1;
  height: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tab-label-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.tab-text {
  font-size: 28rpx;
  color: $text-secondary;
  line-height: 1;
}

.tab-item.active .tab-text {
  color: $primary;
  font-weight: 600;
}

.tab-badge {
  min-width: 30rpx;
  height: 30rpx;
  padding: 0 8rpx;
  border-radius: 999rpx;
  background: $primary;
  color: $white;
  font-size: 20rpx;
  line-height: 30rpx;
  text-align: center;
}

.tab-indicator {
  position: absolute;
  bottom: 0;
  width: 56rpx;
  height: 4rpx;
  border-radius: 4rpx 4rpx 0 0;
  background: $primary;
}

.coupon-scroll {
  flex: 1;
  height: calc(100vh - 88rpx);
}

.coupon-list {
  padding: 24rpx 32rpx 0;
}

.coupon-card {
  position: relative;
  display: flex;
  min-height: 178rpx;
  margin-bottom: 24rpx;
  background: $white;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 8rpx 26rpx rgba(45, 52, 54, 0.07);
}

.coupon-card::before,
.coupon-card::after {
  content: '';
  position: absolute;
  top: 50%;
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  background: $bg-color;
  transform: translateY(-50%);
  z-index: 2;
}

.coupon-card::before {
  left: -16rpx;
}

.coupon-card::after {
  right: -16rpx;
}

.coupon-card.status-used,
.coupon-card.status-expired {
  box-shadow: 0 4rpx 18rpx rgba(45, 52, 54, 0.04);
  opacity: 0.78;
}

.coupon-bar {
  width: 12rpx;
  flex-shrink: 0;
}

.coupon-bar.red {
  background: #ff6b6b;
}

.coupon-bar.orange {
  background: #ff9f43;
}

.coupon-bar.purple {
  background: $purple;
}

.coupon-bar.muted {
  background: $text-muted;
}

.coupon-body {
  flex: 1;
  min-width: 0;
  padding: 30rpx 30rpx 24rpx;
}

.coupon-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.coupon-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.coupon-title {
  font-size: 36rpx;
  font-weight: 700;
  line-height: 44rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.coupon-title.red {
  color: #ff5a5f;
}

.coupon-title.orange {
  color: #f08a24;
}

.coupon-title.purple {
  color: $purple;
}

.coupon-title.muted {
  color: $text-secondary;
}

.coupon-scope {
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 32rpx;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.use-btn {
  flex-shrink: 0;
  height: 64rpx;
  padding: 0 30rpx;
  border-radius: 999rpx;
  background: $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 18rpx rgba(79, 110, 247, 0.22);
}

.use-btn:active {
  background: $primary-dark;
}

.use-btn-text {
  color: $white;
  font-size: 24rpx;
  font-weight: 600;
  white-space: nowrap;
}

.status-stamp {
  flex-shrink: 0;
  height: 52rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: rgba(178, 190, 195, 0.14);
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-stamp-text {
  font-size: 24rpx;
  color: $text-muted;
}

.coupon-footer {
  margin-top: 18rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.coupon-desc,
.coupon-expiry {
  font-size: 22rpx;
  line-height: 32rpx;
  color: $text-muted;
}

.coupon-desc {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.coupon-expiry {
  flex-shrink: 0;
}

.state-wrap {
  min-height: 600rpx;
  padding: 120rpx 48rpx 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.state-icon {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background: rgba(178, 190, 195, 0.12);
  margin-bottom: 28rpx;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ticket-empty {
  border-radius: 32rpx;
  width: 168rpx;
  height: 118rpx;
  background: rgba(178, 190, 195, 0.12);
}

.ticket-hole {
  position: absolute;
  top: 50%;
  width: 28rpx;
  height: 28rpx;
  border-radius: 50%;
  background: $bg-color;
  transform: translateY(-50%);
}

.ticket-hole.left {
  left: -14rpx;
}

.ticket-hole.right {
  right: -14rpx;
}

.ticket-line {
  position: absolute;
  left: 38rpx;
  height: 8rpx;
  border-radius: 8rpx;
  background: $text-muted;
  opacity: 0.55;
}

.ticket-line.main {
  top: 40rpx;
  width: 92rpx;
}

.ticket-line.sub {
  top: 68rpx;
  width: 60rpx;
}

.error-icon {
  background: rgba(255, 107, 107, 0.12);
}

.state-icon-text {
  font-size: 64rpx;
  font-weight: 700;
  color: $danger;
}

.state-text {
  font-size: 28rpx;
  color: $text-muted;
  text-align: center;
}

.retry-btn {
  margin-top: 36rpx;
  height: 72rpx;
  padding: 0 44rpx;
  border-radius: 999rpx;
  border: 2rpx solid $primary;
  background: $white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.retry-btn:active {
  background: $primary-light;
}

.retry-btn-text {
  color: $primary;
  font-size: 26rpx;
  font-weight: 600;
}

.loading-state {
  padding: 24rpx 32rpx 0;
}

.skeleton-card {
  display: flex;
  height: 178rpx;
  margin-bottom: 24rpx;
  border-radius: 24rpx;
  overflow: hidden;
  background: $white;
  box-shadow: $shadow-sm;
}

.skeleton-bar {
  width: 12rpx;
  background: rgba(178, 190, 195, 0.4);
}

.skeleton-content {
  flex: 1;
  padding: 30rpx;
}

.skeleton-row {
  height: 24rpx;
  border-radius: 12rpx;
  background: $bg-color;
  margin-bottom: 20rpx;
  animation: skeleton-pulse 1.2s ease-in-out infinite;
}

.skeleton-row.title {
  width: 58%;
  height: 36rpx;
}

.skeleton-row.short {
  width: 34%;
}

.skeleton-row.date {
  width: 76%;
  margin-bottom: 0;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}

.bottom-safe {
  height: 40rpx;
}
</style>
