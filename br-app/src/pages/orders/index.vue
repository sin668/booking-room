<template>
  <view class="page">
    <!-- Status filter tabs -->
    <view class="tabs">
      <view
        v-for="tab in tabs"
        :key="tab.value"
        :class="['tab-item', { active: currentTab === tab.value }]"
        @tap="onSwitchTab(tab.value)"
      >
        <text class="tab-text">{{ tab.label }}</text>
        <view v-if="currentTab === tab.value" class="tab-indicator" />
      </view>
    </view>

    <!-- Order list -->
    <scroll-view
      class="order-scroll"
      scroll-y
      @scrolltolower="onLoadMore"
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onPullRefresh"
    >
      <!-- Loading skeleton -->
      <view v-if="loading && orders.length === 0" class="loading-state">
        <view v-for="i in 3" :key="i" class="skeleton-card">
          <view class="skeleton-row skeleton-row-header" />
          <view class="skeleton-divider" />
          <view class="skeleton-row" />
          <view class="skeleton-row" />
          <view class="skeleton-row skeleton-row-short" />
        </view>
      </view>

      <!-- Empty state -->
      <view v-else-if="!loading && orders.length === 0" class="empty-state">
        <view class="empty-icon">
          <view class="empty-icon-body" />
          <view class="empty-icon-line" />
          <view class="empty-icon-line short" />
        </view>
        <text class="empty-text">暂无预约记录</text>
        <view class="empty-btn" @tap="goBooking">
          <text class="empty-btn-text">去预约</text>
        </view>
      </view>

      <!-- Order cards -->
      <view v-else class="order-list">
        <view
          v-for="(order, index) in orders"
          :key="order.id"
          :class="['order-card', `status-${order.status}`, `card-enter-${index % 5}`]"
        >
          <!-- Accent bar for confirmed -->
          <view v-if="order.status === 'confirmed'" class="accent-bar" />

          <!-- Top row: store name + status badge -->
          <view class="card-header">
            <text class="store-name">{{ order.room ? order.room.name : '未知门店' }}</text>
            <view :class="['status-badge', `badge-${order.status}`]">
              <text class="status-badge-text">{{ statusLabel(order.status) }}</text>
            </view>
          </view>

          <!-- Dashed divider -->
          <view class="dashed-divider">
            <view class="dash" v-for="i in 20" :key="i" />
          </view>

          <!-- Seat info -->
          <view class="card-info-row">
            <view class="info-icon seat-icon">
              <view class="seat-icon-shape" />
            </view>
            <text class="info-text">{{ seatInfoText(order) }}</text>
          </view>

          <!-- Time -->
          <view class="card-info-row">
            <view class="info-icon clock-icon">
              <view class="clock-icon-circle" />
              <view class="clock-icon-hand" />
            </view>
            <text class="info-text">{{ order.date }} {{ order.start_time }} - {{ order.end_time }}</text>
          </view>

          <!-- Duration + Price -->
          <view class="card-bottom-row">
            <text class="duration-text">{{ calcHours(order) }}小时</text>
            <text class="price-text">
              <text class="price-symbol">¥</text>{{ order.total_price || '0.00' }}
            </text>
          </view>

          <!-- Action row -->
          <view class="card-action-row">
            <view
              v-if="order.status === 'confirmed'"
              class="action-btn"
              @tap="viewSeat(order)"
            >
              <text class="action-btn-text">查看座位</text>
            </view>
            <view
              v-if="order.status === 'completed'"
              class="action-btn"
              @tap="rebook(order)"
            >
              <text class="action-btn-text">再来一单</text>
            </view>
            <view
              v-if="order.status === 'cancelled'"
              class="action-btn"
              @tap="rebook(order)"
            >
              <text class="action-btn-text">重新预约</text>
            </view>
          </view>
        </view>

        <!-- Load more indicator -->
        <view class="load-more">
          <text v-if="loading" class="load-more-text">加载中...</text>
          <text v-else-if="!hasMore" class="load-more-text">没有更多了</text>
        </view>
      </view>

      <!-- Bottom spacing for tab bar -->
      <view style="height: 120rpx;" />
    </scroll-view>
  </view>
</template>

<script>
import { getBookings } from '@/api/bookings'

const TABS = [
  { label: '全部', value: 'all' },
  { label: '已确认', value: 'confirmed' },
  { label: '已取消', value: 'cancelled' },
  { label: '已完成', value: 'completed' },
]

const STATUS_MAP = {
  confirmed: '已确认',
  cancelled: '已取消',
  completed: '已完成',
}

const ZONE_MAP = {
  quiet: '静音区',
  keyboard: '键盘区',
  vip: 'VIP区',
}

const PAGE_SIZE = 20

export default {
  data() {
    return {
      tabs: TABS,
      currentTab: 'all',
      orders: [],
      page: 1,
      total: 0,
      loading: false,
      refreshing: false,
      hasMore: true,
    }
  },

  onShow() {
    this.resetAndLoad()
  },

  methods: {
    async resetAndLoad() {
      this.page = 1
      this.orders = []
      this.hasMore = true
      await this.loadOrders()
    },

    async loadOrders() {
      if (this.loading) return
      this.loading = true
      try {
        const params = { page: this.page, page_size: PAGE_SIZE }
        if (this.currentTab !== 'all') {
          params.status = this.currentTab
        }
        const data = await getBookings(params)
        const items = data.items || []
        if (this.page === 1) {
          this.orders = items
        } else {
          this.orders = this.orders.concat(items)
        }
        this.total = data.total || 0
        this.hasMore = this.orders.length < this.total
      } catch {
        if (this.page === 1) this.orders = []
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },

    onSwitchTab(value) {
      if (this.currentTab === value) return
      this.currentTab = value
      this.resetAndLoad()
    },

    onPullRefresh() {
      this.refreshing = true
      this.resetAndLoad()
    },

    onLoadMore() {
      if (!this.hasMore || this.loading) return
      this.page++
      this.loadOrders()
    },

    statusLabel(status) {
      return STATUS_MAP[status] || status
    },

    seatInfoText(order) {
      if (!order.seat) return '座位信息 unavailable'
      const seat = order.seat
      const zone = ZONE_MAP[seat.zone] || seat.zone || ''
      return zone ? `${seat.seat_number}号座位 · ${zone}` : `${seat.seat_number}号座位`
    },

    calcHours(order) {
      const parse = (t) => {
        const parts = t.split(':').map(Number)
        return parts[0] + parts[1] / 60
      }
      const start = parse(order.start_time)
      const end = parse(order.end_time)
      const h = end - start
      return Number.isInteger(h) ? h : h.toFixed(1)
    },

    viewSeat(order) {
      if (!order.room_id || !order.seat_id) return
      uni.navigateTo({
        url: `/pages/booking/detail?room_id=${order.room_id}`,
      })
    },

    rebook(order) {
      uni.switchTab({ url: '/pages/booking/index' })
    },

    goBooking() {
      uni.switchTab({ url: '/pages/booking/index' })
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

/* Tabs */
.tabs {
  display: flex;
  align-items: center;
  background: #fff;
  padding: 0 16rpx;
  height: 88rpx;
  position: sticky;
  top: 0;
  z-index: 10;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  position: relative;
}

.tab-text {
  font-size: 28rpx;
  color: $text-secondary;
  transition: color 0.2s;
}

.tab-item.active .tab-text {
  font-weight: 600;
  color: $text-primary;
}

.tab-indicator {
  position: absolute;
  bottom: 8rpx;
  width: 48rpx;
  height: 6rpx;
  border-radius: 3rpx;
  background: $primary;
}

/* Scroll view */
.order-scroll {
  flex: 1;
  height: calc(100vh - 88rpx);
}

/* Loading skeleton */
.loading-state {
  padding: 24rpx 32rpx;
}

.skeleton-card {
  background: #fff;
  border-radius: 32rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.skeleton-row {
  height: 32rpx;
  border-radius: 8rpx;
  background: $bg-color;
  margin-bottom: 16rpx;
  animation: skeleton-pulse 1.2s ease-in-out infinite;
}

.skeleton-row-header {
  width: 60%;
  margin-bottom: 20rpx;
}

.skeleton-row-short {
  width: 40%;
}

.skeleton-divider {
  height: 2rpx;
  border-radius: 1rpx;
  background: $bg-color;
  margin-bottom: 20rpx;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 200rpx;
}

.empty-icon {
  width: 160rpx;
  height: 180rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32rpx;
}

.empty-icon-body {
  width: 120rpx;
  height: 140rpx;
  border-radius: 16rpx;
  background: $bg-color;
  border: 4rpx dashed $text-muted;
}

.empty-icon-line {
  width: 80rpx;
  height: 6rpx;
  border-radius: 3rpx;
  background: $text-muted;
  margin-top: 12rpx;
}

.empty-icon-line.short {
  width: 56rpx;
  margin-top: 8rpx;
}

.empty-text {
  font-size: 28rpx;
  color: $text-muted;
  margin-bottom: 40rpx;
}

.empty-btn {
  height: 72rpx;
  padding: 0 48rpx;
  border-radius: 36rpx;
  border: 2rpx solid $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}

.empty-btn:active {
  background: $primary-light;
}

.empty-btn-text {
  font-size: 26rpx;
  color: $primary;
}

/* Order list */
.order-list {
  padding: 24rpx 0;
}

/* Order card */
.order-card {
  position: relative;
  background: #fff;
  border-radius: 32rpx;
  padding: 32rpx;
  margin: 0 32rpx 24rpx;
  box-shadow: $shadow-sm;
  overflow: hidden;
}

.order-card.status-cancelled {
  opacity: 0.65;
}

/* Accent bar */
.accent-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 8rpx;
  background: $success;
  border-radius: 0 4rpx 4rpx 0;
  animation: accent-pulse 2s ease-in-out infinite;
}

@keyframes accent-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Card entrance animation */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.order-card.card-enter-0 { animation: fadeInUp 0.4s ease-out 0s both; }
.order-card.card-enter-1 { animation: fadeInUp 0.4s ease-out 0.06s both; }
.order-card.card-enter-2 { animation: fadeInUp 0.4s ease-out 0.12s both; }
.order-card.card-enter-3 { animation: fadeInUp 0.4s ease-out 0.18s both; }
.order-card.card-enter-4 { animation: fadeInUp 0.4s ease-out 0.24s both; }

/* Card header */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.store-name {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

/* Status badge */
.status-badge {
  padding: 6rpx 20rpx;
  border-radius: 24rpx;
}

.status-badge-text {
  font-size: 22rpx;
}

.badge-confirmed {
  background: rgba(7, 193, 96, 0.1);
}

.badge-confirmed .status-badge-text {
  color: $success;
}

.badge-cancelled {
  background: rgba(255, 107, 107, 0.1);
}

.badge-cancelled .status-badge-text {
  color: $danger;
}

.badge-completed {
  background: rgba(99, 110, 114, 0.1);
}

.badge-completed .status-badge-text {
  color: $text-secondary;
}

/* Dashed divider */
.dashed-divider {
  display: flex;
  justify-content: space-between;
  padding: 20rpx 0;
}

.dash {
  flex: 1;
  height: 2rpx;
  border-top: 2rpx dashed $border-color;
  margin-right: 4rpx;
}

.dash:last-child {
  margin-right: 0;
}

/* Info row */
.card-info-row {
  display: flex;
  align-items: center;
  margin-bottom: 14rpx;
}

.info-icon {
  width: 36rpx;
  height: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14rpx;
  flex-shrink: 0;
}

/* Seat icon (simplified couch shape) */
.seat-icon-shape {
  width: 28rpx;
  height: 20rpx;
  border-radius: 6rpx;
  background: $text-muted;
  position: relative;

  &::before,
  &::after {
    content: '';
    position: absolute;
    bottom: -6rpx;
    width: 8rpx;
    height: 6rpx;
    border-radius: 0 0 4rpx 4rpx;
    background: $text-muted;
  }

  &::before { left: 2rpx; }
  &::after { right: 2rpx; }
}

/* Clock icon */
.clock-icon-circle {
  width: 28rpx;
  height: 28rpx;
  border-radius: 50%;
  border: 3rpx solid $text-muted;
}

.clock-icon-hand {
  position: absolute;
  width: 3rpx;
  height: 10rpx;
  background: $text-muted;
  border-radius: 2rpx;
  bottom: 50%;
  left: 50%;
  transform-origin: bottom center;
  transform: translateX(-50%) rotate(-30deg);
}

.info-text {
  font-size: 26rpx;
  color: $text-secondary;
}

/* Bottom row: duration + price */
.card-bottom-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10rpx;
}

.duration-text {
  font-size: 24rpx;
  color: $text-muted;
}

.price-text {
  font-size: 32rpx;
  font-weight: 600;
  color: $primary;
}

.price-symbol {
  font-size: 22rpx;
}

/* Action row */
.card-action-row {
  display: flex;
  justify-content: flex-end;
  padding-top: 20rpx;
  border-top: 2rpx solid $bg-color;
  margin-top: 16rpx;
}

.action-btn {
  height: 56rpx;
  padding: 0 32rpx;
  border-radius: 28rpx;
  border: 2rpx solid $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}

.action-btn:active {
  background: $primary-light;
}

.action-btn-text {
  font-size: 24rpx;
  color: $primary;
}

/* Load more */
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
