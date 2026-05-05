<template>
  <view class="page">
    <!-- Custom nav bar over hero -->
    <view class="nav-overlay">
      <view :style="{ height: statusBarHeight + 'px' }" />
      <view class="nav-bar">
        <view class="nav-btn" @tap="onBack">
          <text class="nav-icon">&#xe60d;</text>
        </view>
        <view class="nav-placeholder" />
        <view class="nav-btn" @tap="onShare">
          <text class="nav-icon">&#xe60e;</text>
        </view>
      </view>
    </view>

    <scroll-view class="content" scroll-y>
      <!-- Hero image -->
      <view class="hero">
        <image
          class="hero-image"
          :src="room.cover_image || '/static/images/placeholder.png'"
          mode="aspectFill"
        />
        <view class="hero-gradient" />
        <view class="hero-counter">
          <text class="hero-counter-text">1/{{ roomPhotos.length || 1 }}</text>
        </view>
      </view>

      <!-- Store info card -->
      <view class="info-card animate-in">
        <view class="info-top">
          <text class="info-name">{{ room.name || '' }}</text>
          <view :class="['status-badge', room.status === 'open' ? 'open' : 'closed']">
            <text class="status-text">{{ room.status === 'open' ? '营业中' : '已打烊' }}</text>
          </view>
        </view>

        <!-- Rating -->
        <view class="info-rating">
          <view v-if="room.rating" class="rating-score">
            <text class="rating-star">&#9733;</text>
            <text class="rating-num">{{ room.rating }}</text>
            <text class="rating-count">{{ reviewCount }}条评价</text>
          </view>
          <text v-else class="rating-none">暂无评价</text>
        </view>

        <!-- Address -->
        <view class="info-row">
          <text class="info-icon">&#x1F4CD;</text>
          <text class="info-text">{{ room.address || '' }}</text>
        </view>

        <!-- Business hours -->
        <view class="info-row">
          <text class="info-icon">&#x1F552;</text>
          <text class="info-text">{{ room.business_hours || '暂无营业时间' }}</text>
        </view>

        <!-- Tags -->
        <view class="info-tags">
          <view class="tag tag-blue">
            <text class="tag-text">静音区</text>
          </view>
          <view class="tag tag-blue">
            <text class="tag-text">键盘区</text>
          </view>
          <view class="tag tag-blue">
            <text class="tag-text">VIP区</text>
          </view>
          <view class="tag tag-green">
            <text class="tag-text">免费WiFi</text>
          </view>
          <view class="tag tag-orange">
            <text class="tag-text">充电插座</text>
          </view>
        </view>
      </view>

      <!-- Environment photos -->
      <view class="section animate-in" style="animation-delay: 0.1s;">
        <view class="section-header">
          <text class="section-title">环境照片</text>
          <text class="section-sub">共{{ roomPhotos.length }}张</text>
        </view>
        <scroll-view class="photo-scroll" scroll-x :show-scrollbar="false">
          <view class="photo-list">
            <view v-for="(photo, idx) in displayPhotos" :key="idx" class="photo-card">
              <image class="photo-image" :src="photo" mode="aspectFill" />
            </view>
            <view v-if="roomPhotos.length > 3" class="photo-card photo-more" @tap="onViewAllPhotos">
              <text class="photo-more-text">+{{ roomPhotos.length - 3 }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- Seat stats -->
      <view class="section animate-in" style="animation-delay: 0.2s;">
        <text class="section-title">座位概况</text>
        <view class="stats-grid">
          <view class="stat-card stat-total">
            <text class="stat-icon">&#x1FA91;</text>
            <text class="stat-count">{{ seatStats.total }}</text>
            <text class="stat-label">总座位</text>
          </view>
          <view class="stat-card stat-available">
            <text class="stat-icon">&#x2705;</text>
            <text class="stat-count">{{ seatStats.available }}</text>
            <text class="stat-label">可用</text>
          </view>
          <view class="stat-card stat-occupied">
            <text class="stat-icon">&#x1F464;</text>
            <text class="stat-count">{{ seatStats.occupied }}</text>
            <text class="stat-label">已占</text>
          </view>
          <view class="stat-card stat-maintenance">
            <text class="stat-icon">&#x1F527;</text>
            <text class="stat-count">{{ seatStats.maintenance }}</text>
            <text class="stat-label">维护中</text>
          </view>
        </view>
      </view>

      <!-- Loading state -->
      <view v-if="loading" class="loading-section">
        <text class="loading-text">加载中...</text>
      </view>

      <!-- Bottom spacing for fixed bar -->
      <view style="height: 140rpx;" />
    </scroll-view>

    <!-- Bottom action bar -->
    <view class="bottom-bar">
      <view class="fav-btn" @tap="onToggleFav">
        <text :class="['fav-icon', isFav ? 'fav-active' : '']">{{ isFav ? '&#x2764;' : '&#x2661;' }}</text>
      </view>
      <view class="book-btn" @tap="onBook">
        <text class="book-btn-text">立即预约</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getRooms } from '@/api/rooms'
import { getSeats } from '@/api/seats'

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
      if (this.room.cover_image) {
        return [this.room.cover_image]
      }
      return ['/static/images/placeholder.png']
    },

    displayPhotos() {
      return this.roomPhotos.slice(0, 3)
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
        const data = await getRooms({ page: 1, page_size: 100 })
        const items = data.items || []
        const found = items.find(r => r.id === Number(this.roomId))
        if (found) {
          this.room = found
        }
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

/* Custom nav overlay */
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
  width: 68rpx;
  height: 68rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-icon {
  font-size: 32rpx;
  color: #fff;
}

.nav-placeholder {
  flex: 1;
}

/* Content */
.content {
  height: 100vh;
}

/* Hero image */
.hero {
  position: relative;
  height: 448rpx;
  overflow: hidden;
}

.hero-image {
  width: 100%;
  height: 100%;
}

.hero-gradient {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 200rpx;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.3), transparent);
}

.hero-counter {
  position: absolute;
  bottom: 20rpx;
  right: 24rpx;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 32rpx;
  padding: 4rpx 20rpx;
}

.hero-counter-text {
  font-size: 22rpx;
  color: #fff;
}

/* Info card */
.info-card {
  margin: -48rpx 28rpx 0;
  background: #fff;
  border-radius: $radius-lg;
  padding: 32rpx;
  box-shadow: $shadow-md;
  position: relative;
  z-index: 10;
}

.info-top {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.info-name {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-primary;
  flex: 1;
}

.status-badge {
  padding: 6rpx 20rpx;
  border-radius: 24rpx;
  flex-shrink: 0;
}

.status-badge.open {
  background: rgba(7, 193, 96, 0.1);
}

.status-badge.closed {
  background: rgba(255, 107, 107, 0.1);
}

.status-text {
  font-size: 22rpx;
  font-weight: 500;
}

.status-badge.open .status-text {
  color: $success;
}

.status-badge.closed .status-text {
  color: $danger;
}

/* Rating */
.info-rating {
  margin-bottom: 20rpx;
}

.rating-score {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.rating-star {
  font-size: 28rpx;
  color: #FFB800;
}

.rating-num {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.rating-count {
  font-size: 24rpx;
  color: $text-muted;
}

.rating-none {
  font-size: 26rpx;
  color: $text-muted;
}

/* Info rows */
.info-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.info-icon {
  font-size: 28rpx;
}

.info-text {
  font-size: 26rpx;
  color: $text-secondary;
}

/* Tags */
.info-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 20rpx;
}

.tag {
  padding: 8rpx 24rpx;
  border-radius: 24rpx;
}

.tag-blue {
  background: $primary-light;
}

.tag-green {
  background: rgba(7, 193, 96, 0.1);
}

.tag-orange {
  background: rgba(255, 165, 0, 0.1);
}

.tag-text {
  font-size: 22rpx;
  color: $text-secondary;
}

/* Section */
.section {
  margin: 28rpx 28rpx 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.section-sub {
  font-size: 24rpx;
  color: $text-muted;
}

/* Photo scroll */
.photo-scroll {
  white-space: nowrap;
}

.photo-list {
  display: inline-flex;
  gap: 16rpx;
}

.photo-card {
  width: 160rpx;
  height: 224rpx;
  border-radius: $radius-md;
  overflow: hidden;
  flex-shrink: 0;
}

.photo-image {
  width: 100%;
  height: 100%;
}

.photo-more {
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.photo-more-text {
  font-size: 36rpx;
  font-weight: 600;
  color: #fff;
}

/* Seat stats */
.stats-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.stat-card {
  width: calc(50% - 8rpx);
  border-radius: $radius-lg;
  padding: 28rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.stat-icon {
  font-size: 40rpx;
}

.stat-count {
  font-size: 36rpx;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

.stat-total {
  background: $primary;
}

.stat-available {
  background: $success;
}

.stat-occupied {
  background: $danger;
}

.stat-maintenance {
  background: #FF9500;
}

/* Loading */
.loading-section {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60rpx 0;
}

.loading-text {
  font-size: 28rpx;
  color: $text-muted;
}

/* Bottom bar */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 16rpx 28rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: #fff;
  box-shadow: 0 -2rpx 12rpx rgba(0, 0, 0, 0.06);
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
}

.fav-icon {
  font-size: 40rpx;
  color: $text-muted;
}

.fav-active {
  color: $danger;
}

.book-btn {
  flex: 1;
  height: 88rpx;
  background: $primary;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.book-btn:active {
  background: $primary-dark;
}

.book-btn-text {
  font-size: 30rpx;
  font-weight: 600;
  color: #fff;
}

/* Animation */
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
</style>
