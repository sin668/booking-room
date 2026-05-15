<template>
  <view class="page">
    <!-- Status bar spacer -->
    <view :style="{ height: statusBarHeight + 'px', background: '#fff' }" />

    <!-- Custom nav bar -->
    <view class="nav-bar">
      <view class="nav-location" @tap="onTapLocation">
        <view class="icon icon-location nav-location-icon" />
        <text class="nav-location-text">{{ currentCityName }}</text>
        <view class="icon icon-arrow-down nav-location-arrow" />
      </view>
      <view class="nav-search" @tap="onTapSearch">
        <view class="icon icon-search nav-search-icon" />
        <text class="nav-search-placeholder">搜索自习室</text>
      </view>
      <view class="nav-bell" @tap="onTapBell">
        <view class="icon icon-bell nav-bell-icon" />
        <view v-if="hasNotification" class="nav-bell-dot" />
      </view>
    </view>

    <!-- Main content -->
    <scroll-view
      class="content"
      scroll-y
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onPullDownRefresh"
      @scrolltolower="onReachBottom"
    >
      <!-- Banner carousel -->
      <view v-if="banners.length > 0" class="banner-section">
        <swiper
          class="banner-swiper"
          :autoplay="true"
          :interval="3500"
          :circular="true"
          :indicator-dots="false"
          @change="onBannerChange"
        >
          <swiper-item v-for="banner in banners" :key="banner.id">
            <view class="banner-slide" @tap="onTapBanner(banner)">
              <image class="banner-image" :src="banner.image_url" mode="aspectFill" />
              <view class="banner-overlay">
                <view class="banner-text">
                  <text class="banner-title">{{ banner.title }}</text>
                  <text v-if="banner.subtitle" class="banner-subtitle">{{ banner.subtitle }}</text>
                </view>
                <view v-if="banner.cta_text" class="banner-cta">
                  <text class="banner-cta-text">{{ banner.cta_text }}</text>
                </view>
              </view>
            </view>
          </swiper-item>
        </swiper>
        <view class="banner-dots">
          <view
            v-for="(_, index) in banners"
            :key="index"
            :class="['banner-dot', { active: currentBanner === index }]"
          />
        </view>
      </view>

      <!-- Quick entry grid -->
      <view class="quick-entry">
        <view
          v-for="entry in quickEntries"
          :key="entry.label"
          class="quick-entry-item"
          @tap="onTapQuickEntry(entry)"
        >
          <view class="quick-entry-icon" :style="{ background: entry.bgColor }">
            <view :class="['icon', entry.iconClass]" :style="{ color: entry.color }" />
          </view>
          <text class="quick-entry-label">{{ entry.label }}</text>
        </view>
      </view>

      <!-- Study code card -->
      <view class="code-card" @tap="onTapStudyCode">
        <view class="code-card-content">
          <text class="code-card-title">我的学习码</text>
          <text class="code-card-desc">到店出示即可核销</text>
          <text class="code-card-action">立即查看</text>
        </view>
        <view class="code-card-qr">
          <view class="icon icon-qrcode code-card-qr-icon" />
        </view>
      </view>

      <view class="section">
        <view class="section-header">
          <text class="section-title">附近自习室</text>
          <text class="section-more" @tap="onTapMoreRooms">查看更多</text>
        </view>

        <view v-if="roomsLoading && rooms.length === 0" class="room-list">
          <view v-for="i in 2" :key="i" class="room-card room-card-skeleton">
            <view class="room-cover skeleton-block" />
            <view class="room-info">
              <view class="skeleton-line long" />
              <view class="skeleton-line short" />
              <view class="skeleton-line medium" />
            </view>
          </view>
        </view>

        <view v-else-if="rooms.length === 0" class="empty-rooms">
          <text class="empty-rooms-title">当前城市暂无自习室</text>
          <text class="empty-rooms-text">切换城市或稍后再试</text>
        </view>

        <view v-else class="room-list">
          <view
            v-for="room in rooms"
            :key="room.id"
            class="room-card"
            @tap="onTapRoom(room)"
          >
            <image class="room-cover" :src="roomCover(room)" mode="aspectFill" />
            <view class="room-info">
              <text class="room-name">{{ room.name }}</text>
              <view class="room-address-row">
                <view class="icon icon-location room-address-icon" />
                <text class="room-address">{{ room.address || '地址待完善' }}</text>
              </view>
              <view class="room-meta">
                <text class="room-tag">在线选座</text>
                <text class="room-price">¥{{ room.min_price || 0 }}起</text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- Hot activities -->
      <view v-if="activities.length > 0" class="section">
        <view class="section-header">
          <text class="section-title">热门活动</text>
          <text class="section-more" @tap="onTapMoreActivities">查看更多</text>
        </view>
        <view class="activity-grid">
          <view
            v-for="activity in activities"
            :key="activity.id"
            class="activity-card"
          >
            <image class="activity-cover" :src="activity.cover_image" mode="aspectFill" />
            <view class="activity-info">
              <text class="activity-title">{{ activity.title }}</text>
              <text class="activity-desc">{{ activity.description }}</text>
              <text class="activity-count">已有{{ activity.participant_count }}人参与</text>
            </view>
          </view>
        </view>
      </view>

      <!-- Bottom spacing for tab bar -->
      <view style="height: 120rpx;" />
    </scroll-view>
  </view>
</template>

<script>
import { getBanners } from '@/api/banners'
import { getActivities } from '@/api/activities'
import { getRooms } from '@/api/rooms'
import { useCityStore } from '@/store/modules/city'

const REAL_ROOM_COVERS = [
  'https://images.unsplash.com/photo-1497366216548-37526070297c?w=720&h=520&fit=crop&q=85',
  'https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=720&h=520&fit=crop&q=85',
  'https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?w=720&h=520&fit=crop&q=85',
]

export default {
  data() {
    return {
      statusBarHeight: 0,
      refreshing: false,
      hasNotification: true,
      banners: [],
      currentBanner: 0,
      activities: [],
      rooms: [],
      roomsLoading: false,
      lastCityId: null,
      quickEntries: [
        { label: '钱包充值', iconClass: 'icon-wallet', bgColor: 'rgba(79,110,247,0.1)', color: '#4F6EF7', path: '/pages/recharge/index' },
        { label: '卡券套餐', iconClass: 'icon-ticket', bgColor: 'rgba(255,165,0,0.1)', color: '#FF8C00', path: '/pages/coupon/index' },
        { label: '学习记录', iconClass: 'icon-book', bgColor: 'rgba(7,193,96,0.1)', color: '#07C160', path: '/pages/study-record/index' },
        { label: '自习室', iconClass: 'icon-location', bgColor: 'rgba(108,92,231,0.1)', color: '#6C5CE7', path: '/pages/booking/index', openType: 'switchTab' },
      ],
    }
  },
  onShow() {
    this.loadData()
  },
  onLoad() {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
  },
  computed: {
    cityStore() {
      return useCityStore()
    },

    currentCityName() {
      return this.cityStore.currentCityName
    },

    currentCityId() {
      return this.cityStore.currentCity?.id || null
    },
  },
  methods: {
    async loadData() {
      const cityChanged = this.lastCityId !== this.currentCityId
      await Promise.allSettled([
        this.loadBanners(),
        this.loadActivities(),
        this.loadRooms(cityChanged || this.rooms.length === 0),
      ])
    },

    async loadBanners() {
      try {
        const data = await getBanners()
        this.banners = data || []
      } catch {
        this.banners = []
      }
    },

    async loadActivities() {
      try {
        const data = await getActivities()
        this.activities = data || []
      } catch {
        this.activities = []
      }
    },

    async loadRooms(force = false) {
      if (this.roomsLoading) return
      if (!force && this.rooms.length > 0) return

      this.roomsLoading = true
      try {
        if (!this.cityStore.initialized) {
          await this.cityStore.initCity()
        }
        const params = { page: 1, page_size: 6 }
        if (this.currentCityId) {
          params.city_id = this.currentCityId
        }
        const data = await getRooms(params)
        this.rooms = data.items || []
        this.lastCityId = this.currentCityId
      } catch {
        this.rooms = []
      } finally {
        this.roomsLoading = false
      }
    },

    roomCover(room) {
      if (room.cover_image) return room.cover_image
      const key = Number(room.id || 0)
      return REAL_ROOM_COVERS[key % REAL_ROOM_COVERS.length]
    },

    onBannerChange(e) {
      this.currentBanner = e.detail.current
    },

    onPullDownRefresh() {
      this.refreshing = true
      this.loadData().finally(() => {
        this.refreshing = false
      })
    },

    onReachBottom() {},

    onTapBanner(banner) {
      if (!banner.link_type || banner.link_type === 'none') return
      if (banner.link_type === 'page' && banner.link_value) {
        uni.navigateTo({ url: banner.link_value })
      }
    },

    onTapQuickEntry(entry) {
      if (entry.path) {
        const navigate = entry.openType === 'switchTab' ? uni.switchTab : uni.navigateTo
        navigate({ url: entry.path })
      }
    },

    onTapStudyCode() {
      uni.navigateTo({ url: '/pages/qrcode/index' })
    },

    onTapMoreActivities() {
      // Future: navigate to activity list page
    },

    onTapMoreRooms() {
      uni.switchTab({ url: '/pages/booking/index' })
    },

    onTapRoom(room) {
      uni.navigateTo({ url: `/pages/booking/detail?room_id=${room.id}` })
    },

    onTapLocation() {
      uni.navigateTo({ url: '/pages/city-select/index' })
    },

    onTapSearch() {
      // Future: search page
    },

    onTapBell() {
      // Future: notifications
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  background: $bg-color;
  min-height: 100vh;
}

/* Nav bar */
.nav-bar {
  display: flex;
  align-items: center;
  height: 88rpx;
  padding: 0 28rpx;
  background: #fff;
  box-shadow: 0 1rpx 0 0 rgba(0, 0, 0, 0.04);
}

.nav-location {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.nav-location-icon {
  font-size: 28rpx;
  color: $primary;
}

.nav-location-text {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
  margin-left: 6rpx;
}

.nav-location-arrow {
  font-size: 14rpx;
  color: $text-secondary;
  margin-left: 4rpx;
}

.nav-search {
  flex: 1;
  display: flex;
  align-items: center;
  height: 64rpx;
  margin: 0 20rpx;
  padding: 0 24rpx;
  background: $bg-color;
  border-radius: 32rpx;
}

.nav-search-icon {
  font-size: 26rpx;
  color: $text-muted;
  margin-right: 10rpx;
}

.nav-search-placeholder {
  font-size: 26rpx;
  color: $text-muted;
}

.nav-bell {
  position: relative;
  flex-shrink: 0;
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.nav-bell:active {
  background: $bg-color;
}

.nav-bell-icon {
  font-size: 38rpx;
  color: $text-primary;
}

.nav-bell-dot {
  position: absolute;
  top: 12rpx;
  right: 14rpx;
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #FF4757;
  border: 2rpx solid #fff;
}

/* Content */
.content {
  height: calc(100vh - var(--status-bar-height, 44px) - 88rpx - 100rpx);
}

/* Banner */
.banner-section {
  margin: 20rpx 28rpx 0;
  border-radius: 28rpx;
  overflow: hidden;
  position: relative;
  box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.06);
}

.banner-swiper {
  height: 340rpx;
}

.banner-slide {
  position: relative;
  width: 100%;
  height: 100%;
}

.banner-image {
  width: 100%;
  height: 100%;
}

.banner-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  padding: 28rpx;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.55), rgba(0, 0, 0, 0.1) 60%, transparent);
}

.banner-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5rpx;
}

.banner-subtitle {
  display: block;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 6rpx;
}

.banner-cta {
  flex-shrink: 0;
  padding: 10rpx 30rpx;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 30rpx;
  margin-left: 16rpx;
  backdrop-filter: blur(8rpx);
}

.banner-cta-text {
  font-size: 22rpx;
  font-weight: 600;
  color: $primary;
}

.banner-dots {
  position: absolute;
  bottom: 16rpx;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10rpx;
}

.banner-dot {
  width: 12rpx;
  height: 6rpx;
  border-radius: 3rpx;
  background: rgba(255, 255, 255, 0.5);
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.banner-dot.active {
  width: 36rpx;
  background: #fff;
}

/* Quick entry */
.quick-entry {
  display: flex;
  justify-content: space-around;
  padding: 36rpx 16rpx 28rpx;
}

.quick-entry-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: transform 0.2s;
}

.quick-entry-item:active {
  transform: scale(0.92);
}

.quick-entry-icon {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s;
}

.quick-entry-item:active .quick-entry-icon {
  box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.08);
}

.quick-entry-icon .icon {
  font-size: 42rpx;
}

.quick-entry-label {
  margin-top: 14rpx;
  font-size: 22rpx;
  color: $text-secondary;
}

/* Study code card */
.code-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 8rpx 28rpx 0;
  padding: 32rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, $primary, $purple);
  box-shadow: 0 8rpx 24rpx rgba(79, 110, 247, 0.25);
  transition: transform 0.2s;
}

.code-card:active {
  transform: scale(0.98);
}

.code-card-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #fff;
}

.code-card-desc {
  display: block;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.75);
  margin-top: 6rpx;
}

.code-card-action {
  display: inline-flex;
  align-items: center;
  gap: 4rpx;
  font-size: 22rpx;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.95);
  margin-top: 18rpx;
  padding: 6rpx 20rpx;
  background: rgba(255, 255, 255, 0.18);
  border-radius: 20rpx;
}

.code-card-qr {
  width: 108rpx;
  height: 108rpx;
  border: 3rpx dashed rgba(255, 255, 255, 0.35);
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.12);
}

.code-card-qr-icon {
  font-size: 52rpx;
  color: #fff;
}

/* Section */
.section {
  margin-top: 32rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28rpx 20rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
  position: relative;
  padding-left: 16rpx;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 4rpx;
    bottom: 4rpx;
    width: 6rpx;
    border-radius: 3rpx;
    background: linear-gradient(180deg, $primary, $purple);
  }
}

.section-more {
  font-size: 22rpx;
  color: $text-muted;
  display: flex;
  align-items: center;
  gap: 4rpx;
}

/* Room list */
.room-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  padding: 0 28rpx;
}

.room-card {
  display: flex;
  min-height: 188rpx;
  overflow: hidden;
  border-radius: 22rpx;
  background: #fff;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
  transition: transform 0.2s;
}

.room-card:active {
  transform: scale(0.98);
}

.room-cover {
  width: 184rpx;
  height: 188rpx;
  flex-shrink: 0;
  background: #eef1fb;
}

.room-info {
  flex: 1;
  min-width: 0;
  padding: 20rpx 22rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.room-name {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-address-row {
  display: flex;
  align-items: center;
  min-width: 0;
  margin-top: 10rpx;
}

.room-address-icon {
  flex-shrink: 0;
  margin-right: 6rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.room-address {
  flex: 1;
  min-width: 0;
  font-size: 23rpx;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-top: 14rpx;
}

.room-tag {
  flex-shrink: 0;
  padding: 6rpx 12rpx;
  border-radius: 14rpx;
  background: rgba(79, 110, 247, 0.08);
  font-size: 20rpx;
  color: $primary;
}

.room-price {
  font-size: 26rpx;
  font-weight: 700;
  color: $danger;
}

.empty-rooms {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200rpx;
  margin: 0 28rpx;
  border-radius: 22rpx;
  background: #fff;
}

.empty-rooms-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.empty-rooms-text {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.skeleton-block,
.skeleton-line {
  background: linear-gradient(90deg, #eef1fb 0%, #f7f8ff 48%, #eef1fb 100%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.2s ease-in-out infinite;
}

.room-card-skeleton .room-info {
  justify-content: center;
  gap: 16rpx;
}

.skeleton-line {
  height: 22rpx;
  border-radius: 11rpx;
}

.skeleton-line.long {
  width: 70%;
}

.skeleton-line.medium {
  width: 56%;
}

.skeleton-line.short {
  width: 42%;
}

@keyframes skeleton-loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* Activity grid */
.activity-grid {
  display: flex;
  flex-wrap: wrap;
  padding: 0 28rpx;
  gap: 20rpx;
}

.activity-card {
  width: calc(50% - 10rpx);
  background: #fff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
  transition: transform 0.2s;
}

.activity-card:active {
  transform: scale(0.97);
}

.activity-cover {
  width: 100%;
  height: 200rpx;
}

.activity-info {
  padding: 18rpx;
}

.activity-title {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.activity-desc {
  display: block;
  font-size: 22rpx;
  color: $text-secondary;
  margin-top: 6rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-count {
  display: block;
  font-size: 20rpx;
  color: $text-muted;
  margin-top: 10rpx;
}
</style>
