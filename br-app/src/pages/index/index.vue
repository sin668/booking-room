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

      <!-- 关注自习室 -->
      <view v-if="followedStudyRooms.length > 0" class="section">
        <view class="section-header">
          <text class="section-title">关注自习室</text>
          <text class="section-more" @tap="onTapFavorites">查看更多</text>
        </view>
        <view class="room-list">
          <view
            v-for="room in followedStudyRooms"
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
                <text :class="['room-price', { muted: !roomPriceText(room) }]">
                  {{ roomPriceText(room) || '查看详情' }}
                </text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 关注培训室 -->
      <view v-if="followedTrainingRooms.length > 0" class="section">
        <view class="section-header">
          <text class="section-title">关注培训室</text>
          <text class="section-more" @tap="onTapFavorites">查看更多</text>
        </view>
        <view class="room-list">
          <view
            v-for="room in followedTrainingRooms"
            :key="'tr-' + room.id"
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
                <text class="room-tag purple">培训室</text>
                <text :class="['room-price', { muted: !roomPriceText(room) }]">
                  {{ roomPriceText(room) || '查看详情' }}
                </text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 关注课程 -->
      <view v-if="followedCourses.length > 0" class="section">
        <view class="section-header">
          <text class="section-title">关注课程</text>
          <text class="section-more" @tap="onTapFavorites">查看更多</text>
        </view>
        <view class="room-list">
          <view
            v-for="course in followedCourses"
            :key="'c-' + course.id"
            class="room-card"
            @tap="onTapCourse(course)"
          >
            <image
              v-if="course.cover_image"
              class="room-cover"
              :src="course.cover_image"
              mode="aspectFill"
            />
            <view v-else class="room-cover course-ph">
              <view class="course-ph-icon" />
            </view>
            <view class="room-info">
              <text class="room-name">{{ course.name }}</text>
              <text v-if="course.description" class="room-address">{{ course.description }}</text>
              <view class="room-meta">
                <text v-if="Number(course.min_price) > 0" class="room-price">¥{{ course.min_price }}起</text>
                <text v-else class="room-tag green">免费</text>
                <view class="icon icon-arrow-right room-arrow" />
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 关注教师 -->
      <view v-if="followedTeachers.length > 0" class="section">
        <view class="section-header">
          <text class="section-title">关注教师</text>
          <text class="section-more" @tap="onTapFavorites">查看更多</text>
        </view>
        <view class="teacher-mini-list">
          <view
            v-for="teacher in followedTeachers"
            :key="'t-' + teacher.id"
            class="teacher-mini-card"
            @tap="onTapTeacher(teacher)"
          >
            <image
              v-if="teacher.cover_image"
              class="teacher-mini-avatar"
              :src="teacher.cover_image"
              mode="aspectFill"
            />
            <view v-else class="teacher-mini-avatar-ph">
              <text class="teacher-mini-avatar-text">{{ (teacher.name || 'T').charAt(0) }}</text>
            </view>
            <view class="teacher-mini-info">
              <text class="teacher-mini-name">{{ teacher.name }}</text>
              <text v-if="teacher.description" class="teacher-mini-desc">{{ teacher.description }}</text>
            </view>
            <view class="icon icon-arrow-right teacher-mini-arrow" />
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
            v-for="activity in displayedActivities"
            :key="activity.id"
            class="activity-card"
            @tap="onTapActivity(activity)"
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
import { getNotificationUnreadSummary } from '@/api/notifications'
import { useCityStore } from '@/store/modules/city'
import { getAllFollowedCategories } from '@/services/followedRooms'
import { formatRoomMinPrice } from '@/utils/formatters'

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
      hasNotification: false,
      banners: [],
      currentBanner: 0,
      activities: [],
      followedStudyRooms: [],
      followedTrainingRooms: [],
      followedCourses: [],
      followedTeachers: [],
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

    displayedActivities() {
      return this.activities.slice(0, 4)
    },
  },
  methods: {
    async loadData() {
      const cityChanged = this.lastCityId !== this.currentCityId
      if (cityChanged) {
        this.lastCityId = this.currentCityId
      }
      this.loadFollowedRooms()
      await Promise.allSettled([
        this.loadNotificationUnreadSummary(),
        this.loadBanners(),
        this.loadActivities(),
      ])
    },

    async loadNotificationUnreadSummary() {
      try {
        const summary = await getNotificationUnreadSummary()
        this.hasNotification = Number(summary?.total_unread || 0) > 0
      } catch {
        this.hasNotification = false
      }
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

    async loadFollowedRooms() {
      const cityId = this.currentCityId == null ? null : Number(this.currentCityId)
      const cityName = this.currentCityName || ''
      try {
        const categories = await getAllFollowedCategories()
        this.followedStudyRooms = categories.studyRooms
          .filter((room) => {
            if (cityId !== null && room.city_id !== null && room.city_id !== undefined && room.city_id !== '') {
              return Number(room.city_id) === cityId
            }
            if (cityName && room.city_name) {
              return room.city_name === cityName
            }
            return !room.city_id && !room.city_name
          })
          .slice(0, 2)
        this.followedTrainingRooms = categories.trainingRooms.slice(0, 2)
        this.followedCourses = categories.courses.slice(0, 2)
        this.followedTeachers = categories.teachers.slice(0, 2)
      } catch {
        this.followedStudyRooms = []
        this.followedTrainingRooms = []
        this.followedCourses = []
        this.followedTeachers = []
      }
    },

    roomCover(room) {
      if (room.cover_image) return room.cover_image
      const key = Number(room.id || 0)
      return REAL_ROOM_COVERS[key % REAL_ROOM_COVERS.length]
    },

    roomPriceText(room) {
      return formatRoomMinPrice(room)
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

    onTapActivity(activity) {
      if (!activity?.id) return
      uni.navigateTo({ url: `/pages/activity/detail?id=${activity.id}` })
    },

    onTapMoreRooms() {
      uni.navigateTo({ url: '/pages/favorites/index' })
    },

    onTapFavorites() {
      uni.navigateTo({ url: '/pages/favorites/index' })
    },

    onTapCourse(course) {
      if (!course?.id) return
      uni.navigateTo({ url: `/pages/training/course-detail?course_id=${course.id}` })
    },

    onTapTeacher(teacher) {
      if (!teacher?.id) return
      uni.navigateTo({ url: `/pages/teacher/profile?teacher_id=${teacher.id}` })
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
      uni.navigateTo({ url: '/pages/notifications/index' })
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  background: linear-gradient(180deg, #fff 0, $bg-warm 180rpx, $bg-color 420rpx);
  min-height: 100vh;
}

/* Nav bar */
.nav-bar {
  display: flex;
  align-items: center;
  height: 88rpx;
  padding: 0 28rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 1rpx 0 0 rgba(79, 110, 247, 0.06);
  backdrop-filter: blur(18rpx);
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
  background: $primary-soft;
  border-radius: 32rpx;
  border: 1rpx solid $border-soft;
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
  background: $surface-soft;
  border: 1rpx solid $border-soft;
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
  border-radius: 32rpx;
  overflow: hidden;
  position: relative;
  box-shadow: $shadow-card;
  border: 1rpx solid rgba(255, 255, 255, 0.66);
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
  margin: 24rpx 28rpx 0;
  padding: 28rpx 8rpx 24rpx;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 28rpx;
  border: 1rpx solid $border-soft;
  box-shadow: $shadow-sm;
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
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 18rpx rgba(35, 41, 68, 0.06);
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
  margin: 24rpx 28rpx 0;
  padding: 32rpx;
  border-radius: 30rpx;
  background: $gradient-primary;
  box-shadow: $shadow-float;
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
  border-radius: 26rpx;
  background: $surface;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
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

.room-tag.purple {
  background: rgba(108, 92, 231, 0.08);
  color: $purple;
}

.room-tag.green {
  background: rgba(7, 193, 96, 0.08);
  color: $success;
}

.room-price {
  font-size: 26rpx;
  font-weight: 700;
  color: $danger;
}

.room-price.muted {
  font-size: 22rpx;
  font-weight: 600;
  color: $primary;
}

.room-arrow {
  font-size: 24rpx;
  color: $text-muted;
}

.course-ph {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(79, 110, 247, 0.08), rgba(108, 92, 231, 0.06));
}

.course-ph-icon {
  width: 56rpx;
  height: 56rpx;
  border: 4rpx solid $primary;
  border-radius: 12rpx;
  position: relative;
}

.course-ph-icon::after {
  content: '';
  position: absolute;
  left: 10rpx;
  right: 10rpx;
  top: 50%;
  height: 4rpx;
  background: $primary;
  border-radius: 2rpx;
}

/* Teacher mini list */
.teacher-mini-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  padding: 0 28rpx;
}

.teacher-mini-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 24rpx;
  border-radius: 24rpx;
  background: $surface;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  transition: transform 0.2s;
}

.teacher-mini-card:active {
  transform: scale(0.98);
}

.teacher-mini-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  flex-shrink: 0;
  background: #eef1fb;
}

.teacher-mini-avatar-ph {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  flex-shrink: 0;
  background: linear-gradient(135deg, $primary, $purple);
  display: flex;
  align-items: center;
  justify-content: center;
}

.teacher-mini-avatar-text {
  font-size: 34rpx;
  font-weight: 700;
  color: #fff;
}

.teacher-mini-info {
  flex: 1;
  min-width: 0;
}

.teacher-mini-name {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
  display: block;
}

.teacher-mini-desc {
  display: block;
  font-size: 22rpx;
  color: $text-secondary;
  margin-top: 6rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.teacher-mini-arrow {
  font-size: 24rpx;
  color: $text-muted;
  flex-shrink: 0;
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
  justify-content: space-between;
  padding: 0 28rpx;
  row-gap: 20rpx;
}

.activity-card {
  width: 337rpx;
  box-sizing: border-box;
  margin-bottom: 20rpx;
  background: $surface;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
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
