<template>
  <view class="page">
    <view class="nav-overlay">
      <view :style="{ height: statusBarHeight + 'px' }" />
      <view class="nav-bar">
        <view class="nav-btn" @tap="onBack">
          <view class="nav-chevron" />
        </view>
        <view class="nav-placeholder" />
        <view class="nav-btn" @tap="onShare">
          <view class="nav-share">
            <view class="nav-share-dot top" />
            <view class="nav-share-dot left" />
            <view class="nav-share-dot right" />
            <view class="nav-share-line one" />
            <view class="nav-share-line two" />
          </view>
        </view>
      </view>
    </view>

    <scroll-view class="content" scroll-y>
      <view class="hero">
        <image
          class="hero-image"
          :src="heroImage"
          mode="aspectFill"
        />
        <view class="hero-gradient" />
        <view class="hero-title">
          <text class="hero-kicker">学习室详情</text>
          <text class="hero-room-name">{{ roomName }}</text>
        </view>
        <view class="hero-counter">
          <view class="counter-icon" />
          <text class="hero-counter-text">1/{{ roomPhotos.length }}</text>
        </view>
      </view>

      <view class="info-card animate-in">
        <view class="info-top">
          <text class="info-name">{{ roomName }}</text>
          <view :class="['status-badge', room.status === 'open' ? 'open' : 'closed']">
            <text class="status-text">{{ room.status === 'open' ? '营业中' : '已打烊' }}</text>
          </view>
        </view>

        <view class="summary-strip">
          <view class="summary-item">
            <text class="summary-value">{{ ratingText }}</text>
            <text class="summary-label">评分</text>
          </view>
          <view class="summary-divider" />
          <view class="summary-item">
            <text class="summary-value">{{ availabilityPercent }}%</text>
            <text class="summary-label">空座率</text>
          </view>
          <view class="summary-divider" />
          <view class="summary-item">
            <text class="summary-value">¥{{ minPrice }}</text>
            <text class="summary-label">起步价</text>
          </view>
        </view>

        <view class="info-row">
          <view class="icon icon-location info-icon primary" />
          <view class="info-main">
            <text class="info-text">{{ room.address || '茂名市茂南区光谷大道88号3楼' }}</text>
            <text class="info-sub">距您约1.2km</text>
          </view>
          <view class="icon icon-arrow-right info-arrow" />
        </view>

        <view class="info-row">
          <view class="time-icon">
            <view class="time-hand hour" />
            <view class="time-hand minute" />
          </view>
          <text class="info-text">{{ room.business_hours || '营业时间 08:00 - 22:00' }}</text>
        </view>

        <view class="info-tags">
          <view
            v-for="tag in roomTags"
            :key="tag.label"
            :class="['tag', tag.tone]"
          >
            <text class="tag-text">{{ tag.label }}</text>
          </view>
        </view>
      </view>

      <view class="section animate-in" style="animation-delay: 0.1s;">
        <view class="section-header">
          <text class="section-title">环境照片</text>
          <view class="section-more" @tap="onViewAllPhotos">
            <text class="section-sub">共{{ roomPhotos.length }}张</text>
            <view class="icon icon-arrow-right section-more-icon" />
          </view>
        </view>
        <scroll-view class="photo-scroll" scroll-x :show-scrollbar="false">
          <view class="photo-list">
            <view v-for="(photo, idx) in displayPhotos" :key="idx" class="photo-card">
              <image class="photo-image" :src="photo" mode="aspectFill" />
            </view>
            <view v-if="roomPhotos.length > 3" class="photo-card photo-more" @tap="onViewAllPhotos">
              <image class="photo-image" :src="roomPhotos[3]" mode="aspectFill" />
              <view class="photo-more-mask">
                <text class="photo-more-text">+{{ roomPhotos.length - 3 }}</text>
              </view>
            </view>
          </view>
        </scroll-view>
      </view>

      <view class="section seat-section animate-in" style="animation-delay: 0.2s;">
        <view class="section-header">
          <text class="section-title">座位概况</text>
          <text class="availability-copy">{{ availabilityLabel }}</text>
        </view>
        <view class="stats-grid">
          <view class="stat-card">
            <view class="stat-icon stat-total">
              <view class="chair-icon" />
            </view>
            <view class="stat-body">
              <text class="stat-count">{{ seatStats.total }}</text>
              <text class="stat-label">总座位</text>
            </view>
          </view>
          <view class="stat-card">
            <view class="stat-icon stat-available">
              <view class="check-mark" />
            </view>
            <view class="stat-body">
              <text class="stat-count">{{ seatStats.available }}</text>
              <text class="stat-label">可用</text>
            </view>
          </view>
          <view class="stat-card">
            <view class="stat-icon stat-occupied">
              <view class="person-icon" />
            </view>
            <view class="stat-body">
              <text class="stat-count">{{ seatStats.occupied }}</text>
              <text class="stat-label">已占</text>
            </view>
          </view>
          <view class="stat-card">
            <view class="stat-icon stat-maintenance">
              <view class="wrench-icon" />
            </view>
            <view class="stat-body">
              <text class="stat-count">{{ seatStats.maintenance }}</text>
              <text class="stat-label">维护中</text>
            </view>
          </view>
        </view>
      </view>

      <view v-if="loading" class="loading-section">
        <view class="loading-pill" />
        <text class="loading-text">正在同步座位状态</text>
      </view>

      <view style="height: 140rpx;" />
    </scroll-view>

    <view class="bottom-bar">
      <view class="fav-btn" @tap="onToggleFav">
        <view :class="['heart-icon', { active: isFav }]" />
      </view>
      <view class="book-btn" @tap="onBook">
        <text class="book-btn-sub">{{ seatStats.available }} 个座位可选</text>
        <text class="book-btn-text">立即预约</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getRoom } from '@/api/rooms'
import { getSeats } from '@/api/seats'

const REAL_ROOM_PHOTOS = [
  'https://images.unsplash.com/photo-1497366216548-37526070297c?w=900&h=560&fit=crop&q=85',
  'https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=520&h=360&fit=crop&q=85',
  'https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?w=520&h=360&fit=crop&q=85',
  'https://images.unsplash.com/photo-1577720643272-265f09367456?w=520&h=360&fit=crop&q=85',
]

export default {
  data() {
    return {
      statusBarHeight: 0,
      roomId: null,
      room: {},
      seats: [],
      loading: true,
      isFav: false,
      reviewCount: 0,
    }
  },

  computed: {
    roomPhotos() {
      const photos = this.room.cover_image ? [this.room.cover_image, ...REAL_ROOM_PHOTOS] : REAL_ROOM_PHOTOS
      return [...new Set(photos)]
    },

    displayPhotos() {
      return this.roomPhotos.slice(0, 3)
    },

    heroImage() {
      return this.roomPhotos[0]
    },

    roomName() {
      return this.room.name || '光谷自习室'
    },

    ratingText() {
      return this.room.rating || '4.8'
    },

    minPrice() {
      return this.room.min_price || '8'
    },

    availabilityPercent() {
      if (!this.seatStats.total) return 0
      return Math.round((this.seatStats.available / this.seatStats.total) * 100)
    },

    availabilityLabel() {
      if (!this.seatStats.total) return '座位状态加载中'
      if (this.seatStats.available > 20) return '空座充足'
      if (this.seatStats.available > 0) return '建议尽快预约'
      return '暂时无空座'
    },

    roomTags() {
      return [
        { label: '静音区', tone: 'tag-blue' },
        { label: '键盘区', tone: 'tag-blue' },
        { label: 'VIP区', tone: 'tag-blue' },
        { label: '免费WiFi', tone: 'tag-green' },
        { label: '充电插座', tone: 'tag-orange' },
      ]
    },

    seatStats() {
      const total = this.seats.length
      const available = this.seats.filter(s => s.is_available).length
      const maintenance = this.seats.filter(s => s.status === 'maintenance').length
      const occupied = total - available - maintenance
      return {
        total,
        available,
        occupied: Math.max(0, occupied),
        maintenance,
      }
    },
  },

  onLoad(options) {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0

    if (options.room_id) {
      this.roomId = options.room_id
      this.loadData()
    }
  },

  methods: {
    async loadData() {
      this.loading = true
      try {
        await Promise.all([this.loadRoom(), this.loadSeats()])
      } finally {
        this.loading = false
      }
    },

    async loadRoom() {
      try {
        const data = await getRoom(this.roomId)
        this.room = data || {}
      } catch {
        // room stays empty
      }
    },

    async loadSeats() {
      try {
        const data = await getSeats(this.roomId)
        this.seats = data || []
      } catch {
        this.seats = []
      }
    },

    onBack() {
      uni.navigateBack()
    },

    onShare() {
      // placeholder
    },

    onViewAllPhotos() {
      // placeholder
    },

    onToggleFav() {
      this.isFav = !this.isFav
    },

    onBook() {
      uni.navigateTo({ url: '/pages/booking/seat-select?room_id=' + this.roomId })
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  background: $bg-color;
  min-height: 100vh;
}

.nav-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 28rpx;
}

.nav-btn {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: rgba(249, 250, 255, 0.28);
  border: 1rpx solid rgba(249, 250, 255, 0.4);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(35, 41, 68, 0.12);
}

.nav-btn:active {
  transform: scale(0.96);
}

.nav-chevron {
  width: 20rpx;
  height: 20rpx;
  border-left: 4rpx solid $white;
  border-bottom: 4rpx solid $white;
  transform: rotate(45deg);
  margin-left: 8rpx;
}

.nav-share {
  position: relative;
  width: 34rpx;
  height: 34rpx;
}

.nav-share-dot {
  position: absolute;
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: $white;
}

.nav-share-dot.top {
  top: 0;
  right: 2rpx;
}

.nav-share-dot.left {
  left: 2rpx;
  bottom: 4rpx;
}

.nav-share-dot.right {
  right: 0;
  bottom: 2rpx;
}

.nav-share-line {
  position: absolute;
  height: 3rpx;
  width: 22rpx;
  border-radius: 3rpx;
  background: $white;
  transform-origin: left center;
}

.nav-share-line.one {
  left: 9rpx;
  top: 12rpx;
  transform: rotate(152deg);
}

.nav-share-line.two {
  left: 11rpx;
  top: 24rpx;
  transform: rotate(12deg);
}

.nav-placeholder {
  flex: 1;
}

.content {
  height: 100vh;
}

.hero {
  position: relative;
  height: 480rpx;
  overflow: hidden;
  background: #eef1fb;
}

.hero-image {
  width: 100%;
  height: 100%;
}

.hero-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(24, 31, 54, 0.22) 0%, rgba(24, 31, 54, 0.02) 38%, rgba(24, 31, 54, 0.48) 100%);
}

.hero-title {
  position: absolute;
  left: 28rpx;
  right: 140rpx;
  bottom: 34rpx;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.hero-kicker {
  font-size: 22rpx;
  font-weight: 600;
  color: rgba(249, 250, 255, 0.82);
}

.hero-room-name {
  font-size: 38rpx;
  font-weight: 700;
  color: $white;
  line-height: 1.25;
}

.hero-counter {
  position: absolute;
  right: 28rpx;
  bottom: 36rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
  background: rgba(23, 29, 48, 0.58);
  border-radius: 32rpx;
  padding: 8rpx 18rpx;
}

.counter-icon {
  width: 20rpx;
  height: 16rpx;
  border: 2rpx solid rgba(249, 250, 255, 0.88);
  border-radius: 4rpx;
  position: relative;
}

.counter-icon::after {
  content: '';
  position: absolute;
  width: 6rpx;
  height: 6rpx;
  right: 2rpx;
  top: 2rpx;
  border-radius: 50%;
  background: rgba(249, 250, 255, 0.88);
}

.hero-counter-text {
  font-size: 22rpx;
  color: $white;
}

.info-card {
  margin: -42rpx 28rpx 0;
  background: $white;
  border-radius: 28rpx;
  padding: 30rpx;
  box-shadow: 0 8rpx 28rpx rgba(79, 110, 247, 0.1);
  position: relative;
  z-index: 10;
}

.info-top {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.info-name {
  font-size: 36rpx;
  line-height: 1.25;
  font-weight: 700;
  color: $text-primary;
  flex: 1;
}

.status-badge {
  padding: 7rpx 18rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
}

.status-badge.open {
  background: rgba(7, 193, 96, 0.11);
}

.status-badge.closed {
  background: rgba(255, 107, 107, 0.12);
}

.status-text {
  font-size: 22rpx;
  font-weight: 600;
}

.status-badge.open .status-text {
  color: $success;
}

.status-badge.closed .status-text {
  color: $danger;
}

.summary-strip {
  display: flex;
  align-items: center;
  margin: 24rpx 0 26rpx;
  padding: 18rpx 0;
  border-radius: 22rpx;
  background: #f7f8ff;
}

.summary-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
}

.summary-value {
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
}

.summary-label {
  font-size: 22rpx;
  color: $text-muted;
}

.summary-divider {
  width: 1rpx;
  height: 42rpx;
  background: rgba(99, 110, 114, 0.12);
}

.info-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 18rpx;
}

.info-icon {
  width: 30rpx;
  height: 30rpx;
  font-size: 30rpx;
  color: $text-muted;
}

.info-icon.primary {
  color: $primary;
}

.info-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5rpx;
}

.info-text {
  flex: 1;
  font-size: 26rpx;
  line-height: 1.45;
  color: $text-secondary;
}

.info-sub {
  font-size: 22rpx;
  color: $primary;
}

.info-arrow {
  width: 24rpx;
  height: 24rpx;
  font-size: 24rpx;
  color: $text-muted;
}

.time-icon {
  width: 30rpx;
  height: 30rpx;
  border: 3rpx solid $text-muted;
  border-radius: 50%;
  position: relative;
  flex-shrink: 0;
}

.time-hand {
  position: absolute;
  left: 0;
  top: 50%;
  height: 3rpx;
  border-radius: 3rpx;
  background: $text-muted;
  transform-origin: right center;
}

.time-hand.hour {
  width: 9rpx;
  margin-left: 4rpx;
  transform: rotate(0deg);
}

.time-hand.minute {
  width: 12rpx;
  margin-left: 2rpx;
  transform: rotate(90deg);
}

.info-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 24rpx;
}

.tag {
  padding: 9rpx 22rpx;
  border-radius: 999rpx;
}

.tag-blue {
  background: $primary-light;
}

.tag-blue .tag-text {
  color: $primary;
}

.tag-green {
  background: rgba(7, 193, 96, 0.1);
}

.tag-green .tag-text {
  color: $success;
}

.tag-orange {
  background: rgba(255, 149, 0, 0.12);
}

.tag-orange .tag-text {
  color: #e67900;
}

.tag-text {
  font-size: 22rpx;
  font-weight: 500;
}

.section {
  margin: 32rpx 28rpx 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 31rpx;
  font-weight: 700;
  color: $text-primary;
}

.section-more {
  display: flex;
  align-items: center;
  gap: 2rpx;
}

.section-sub,
.availability-copy {
  font-size: 24rpx;
  color: $text-muted;
}

.section-more-icon {
  width: 22rpx;
  height: 22rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.photo-scroll {
  white-space: nowrap;
}

.photo-list {
  display: inline-flex;
  gap: 18rpx;
  padding-bottom: 4rpx;
}

.photo-card {
  width: 250rpx;
  height: 176rpx;
  border-radius: 22rpx;
  overflow: hidden;
  flex-shrink: 0;
  background: #eef1fb;
  box-shadow: $shadow-sm;
}

.photo-image {
  width: 100%;
  height: 100%;
}

.photo-more {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.photo-more-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(24, 31, 54, 0.42);
}

.photo-more-text {
  font-size: 36rpx;
  font-weight: 600;
  color: $white;
}

.seat-section {
  background: $white;
  border-radius: 28rpx;
  padding: 28rpx;
  box-shadow: $shadow-sm;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18rpx;
}

.stat-card {
  border-radius: 22rpx;
  padding: 22rpx 18rpx;
  background: #f7f8ff;
  display: flex;
  align-items: center;
  gap: 16rpx;
  min-width: 0;
}

.stat-icon {
  width: 68rpx;
  height: 68rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-total {
  background: rgba(79, 110, 247, 0.1);
}

.stat-available {
  background: rgba(7, 193, 96, 0.11);
}

.stat-occupied {
  background: rgba(255, 107, 107, 0.12);
}

.stat-maintenance {
  background: rgba(255, 149, 0, 0.13);
}

.chair-icon {
  width: 28rpx;
  height: 30rpx;
  border: 4rpx solid $primary;
  border-top-left-radius: 8rpx;
  border-top-right-radius: 8rpx;
  position: relative;
}

.chair-icon::before,
.chair-icon::after {
  content: '';
  position: absolute;
  bottom: -14rpx;
  width: 4rpx;
  height: 14rpx;
  background: $primary;
}

.chair-icon::before {
  left: 2rpx;
}

.chair-icon::after {
  right: 2rpx;
}

.check-mark {
  width: 26rpx;
  height: 14rpx;
  border-left: 5rpx solid $success;
  border-bottom: 5rpx solid $success;
  transform: rotate(-45deg);
  margin-top: -6rpx;
}

.person-icon {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  background: $danger;
  position: relative;
}

.person-icon::after {
  content: '';
  position: absolute;
  left: -8rpx;
  right: -8rpx;
  top: 28rpx;
  height: 18rpx;
  border-radius: 18rpx 18rpx 6rpx 6rpx;
  background: $danger;
}

.wrench-icon {
  width: 38rpx;
  height: 8rpx;
  border-radius: 8rpx;
  background: #e67900;
  transform: rotate(-38deg);
  position: relative;
}

.wrench-icon::after {
  content: '';
  position: absolute;
  right: -8rpx;
  top: -6rpx;
  width: 14rpx;
  height: 14rpx;
  border: 4rpx solid #e67900;
  border-left-color: transparent;
  border-radius: 50%;
}

.stat-body {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.stat-count {
  display: block;
  font-size: 34rpx;
  line-height: 1.1;
  font-weight: 700;
  color: $text-primary;
}

.stat-label {
  display: block;
  margin-top: 4rpx;
  font-size: 23rpx;
  color: $text-muted;
}

.loading-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
  padding: 50rpx 0 8rpx;
}

.loading-pill {
  width: 36rpx;
  height: 12rpx;
  border-radius: 12rpx;
  background: linear-gradient(90deg, $primary-light, $primary);
  animation: loadingPulse 0.9s ease-out infinite;
}

.loading-text {
  font-size: 26rpx;
  color: $text-muted;
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 18rpx 28rpx;
  padding-bottom: calc(18rpx + env(safe-area-inset-bottom));
  background: rgba(249, 250, 255, 0.98);
  border-top: 1rpx solid rgba(45, 52, 54, 0.06);
  box-shadow: 0 -8rpx 24rpx rgba(45, 52, 54, 0.06);
  z-index: 100;
}

.fav-btn {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  border: 2rpx solid $border-color;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: $white;
}

.heart-icon {
  width: 32rpx;
  height: 28rpx;
  position: relative;
  transform: rotate(-45deg);
  border-radius: 0 0 0 6rpx;
  background: transparent;
  border-left: 4rpx solid $text-muted;
  border-bottom: 4rpx solid $text-muted;
}

.heart-icon::before,
.heart-icon::after {
  content: '';
  position: absolute;
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  border: 4rpx solid $text-muted;
  background: $white;
}

.heart-icon::before {
  left: -5rpx;
  top: -14rpx;
}

.heart-icon::after {
  left: 11rpx;
  top: 2rpx;
}

.heart-icon.active,
.heart-icon.active::before,
.heart-icon.active::after {
  background: $danger;
  border-color: $danger;
}

.book-btn {
  flex: 1;
  height: 92rpx;
  background: $primary;
  border-radius: 44rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10rpx 24rpx rgba(79, 110, 247, 0.24);
}

.book-btn:active {
  background: $primary-dark;
  transform: translateY(1rpx);
}

.book-btn-sub {
  font-size: 20rpx;
  color: rgba(249, 250, 255, 0.78);
  line-height: 1.1;
}

.book-btn-text {
  font-size: 30rpx;
  font-weight: 600;
  color: $white;
  line-height: 1.2;
}

.animate-in {
  animation: fadeInUp 0.4s ease both;
}

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

@keyframes loadingPulse {
  0% {
    opacity: 0.45;
    transform: scaleX(0.7);
  }
  100% {
    opacity: 1;
    transform: scaleX(1);
  }
}
</style>
