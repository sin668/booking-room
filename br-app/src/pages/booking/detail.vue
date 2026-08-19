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
            <text class="info-text">{{ displayAddress }}</text>
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

      <!-- 培训室简介（仅 training/comprehensive） -->
      <view v-if="isTrainingRoom || isComprehensiveRoom" class="section intro-section animate-in" style="animation-delay: 0.05s;">
        <view class="section-header">
          <view class="section-title-group">
            <view class="section-bar" />
            <text class="section-title">培训室简介</text>
          </view>
        </view>
        <text class="intro-text">{{ room.description || '暂无简介' }}</text>
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

      <!-- 座位概况（仅 study/comprehensive） -->
      <view v-if="isStudyRoom || isComprehensiveRoom" class="section seat-section animate-in" style="animation-delay: 0.2s;">
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

      <!-- 教室概况（仅 training/comprehensive） -->
      <view v-if="isTrainingRoom || isComprehensiveRoom" class="section classroom-section animate-in" style="animation-delay: 0.2s;">
        <view class="section-header">
          <view class="section-title-group">
            <view class="section-bar" />
            <text class="section-title">教室概况</text>
          </view>
        </view>
        <view class="stats-grid">
          <view class="stat-card">
            <view class="stat-icon stat-classroom">
              <view class="door-icon" />
            </view>
            <view class="stat-body">
              <text class="stat-count">{{ trainingStats?.classroom_count || 0 }}</text>
              <text class="stat-label">培训教室</text>
            </view>
          </view>
          <view class="stat-card">
            <view class="stat-icon stat-capacity">
              <view class="group-icon" />
            </view>
            <view class="stat-body">
              <text class="stat-count">{{ trainingStats?.class_capacity || '8-12' }}</text>
              <text class="stat-label">小班容量</text>
            </view>
          </view>
          <view class="stat-card">
            <view class="stat-icon stat-teacher">
              <view class="board-icon" />
            </view>
            <view class="stat-body">
              <text class="stat-count">{{ trainingStats?.teacher_count || 0 }}</text>
              <text class="stat-label">认证讲师</text>
            </view>
          </view>
          <view class="stat-card">
            <view class="stat-icon stat-students">
              <view class="cap-icon" />
            </view>
            <view class="stat-body">
              <text class="stat-count">{{ trainingStats?.total_students || 0 }}</text>
              <text class="stat-label">累计学员</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 名师团队（仅 training/comprehensive） -->
      <view v-if="isTrainingRoom || isComprehensiveRoom" class="section animate-in" style="animation-delay: 0.3s;">
        <view class="section-header">
          <view class="section-title-group">
            <view class="section-bar" />
            <text class="section-title">名师团队</text>
          </view>
        </view>
        <view v-if="teachers.length === 0" class="empty-state">
          <text class="empty-text">暂无讲师</text>
        </view>
        <scroll-view v-else scroll-x :show-scrollbar="false" class="teacher-scroll">
          <view class="teacher-list">
            <view v-for="teacher in teachers" :key="teacher.id" class="teacher-card">
              <image class="teacher-avatar" :src="teacher.avatar || ''" mode="aspectFill" />
              <text class="teacher-name">{{ teacher.name }}</text>
              <text class="teacher-title">{{ teacher.title || '' }}</text>
              <view class="teacher-rating">
                <text class="star">★</text>
                <text class="rating-text">{{ teacher.rating }}</text>
              </view>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 本培训室课程（仅 training/comprehensive） -->
      <view v-if="isTrainingRoom || isComprehensiveRoom" class="section animate-in" style="animation-delay: 0.4s;">
        <view class="section-header">
          <view class="section-title-group">
            <view class="section-bar" />
            <text class="section-title">本培训室课程</text>
          </view>
          <text class="section-sub">共{{ trainingCourses.length }}门</text>
        </view>
        <view v-if="trainingCourses.length === 0" class="empty-state">
          <text class="empty-text">暂无课程</text>
        </view>
        <view v-else class="course-list">
          <view v-for="course in trainingCourses" :key="course.id" class="course-card" @tap="onCourseDetail(course)">
            <image class="course-cover" :src="course.cover_image || ''" mode="aspectFill" />
            <view class="course-body">
              <view class="course-top">
                <text class="course-name">{{ course.name }}</text>
                <view v-if="courseDetailBadge(course)" :class="['course-tag', `ctag-${courseDetailBadge(course).type}`]">
                  <text class="tag-text">{{ courseDetailBadge(course).text }}</text>
                </view>
              </view>
              <view v-if="course.teacher" class="course-teacher">
                <image
                  v-if="course.teacher.avatar"
                  class="course-teacher-avatar"
                  :src="course.teacher.avatar"
                  mode="aspectFill"
                />
                <view v-else class="course-teacher-avatar-ph">
                  <view class="icon icon-user course-teacher-avatar-icon" />
                </view>
                <text class="teacher-name-sm">{{ course.teacher.name }}</text>
              </view>
              <view v-if="startDateText(course)" class="course-start-date">
                <view class="icon icon-book course-start-icon" />
                <text class="start-date-text">{{ startDateText(course) }}</text>
              </view>
              <view class="course-schedule">
                <view class="icon icon-clock course-clock-icon" />
                <view class="schedule-wrap" @tap.stop="toggleSchedule(course)">
                  <text :class="['schedule-text', { expanded: isScheduleExpanded(course) }]">{{ scheduleText(course) }}</text>
                </view>
                <text class="schedule-dot">·</text>
                <text class="schedule-status">可预约</text>
              </view>
              <view class="course-bottom">
                <view class="course-price-wrap">
                  <text class="course-price">¥{{ course.price }}</text>
                  <text class="price-unit">/课时</text>
                </view>
                <view class="book-pill">
                  <text class="book-pill-text">预约</text>
                </view>
              </view>
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
      <!-- 心状关注按钮（所有类型通用） -->
      <view class="fav-btn" @tap="onToggleFav">
        <text :class="['heart-icon', { active: isFav }]">♥</text>
      </view>

      <!-- 自习室：立即预约 -->
      <view v-if="isStudyRoom" class="book-btn" @tap="onBook">
        <text class="book-btn-sub">{{ seatStats.available }} 个座位可选</text>
        <text class="book-btn-text">立即预约</text>
      </view>

      <!-- 培训室：返回课程 -->
      <view v-else-if="isTrainingRoom" class="back-btn" @tap="onBackToCourses">
        <text class="back-btn-text">返回课程</text>
      </view>

      <!-- 综合室：预约自习室 -->
      <view v-else-if="isComprehensiveRoom" class="book-btn" @tap="onBookStudy">
        <text class="book-btn-sub">{{ seatStats.available }} 个座位可选</text>
        <text class="book-btn-text">预约自习室</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getSeatStats } from '@/api/seats'
import { getTrainingRoomDetail } from '@/api/training'
import { followRoom, isRoomFollowed, unfollowRoom } from '@/services/followedRooms'
import { fetchBookingRoom } from '@/services/bookingPageService'
import { formatCourseSchedule, formatCourseStartDate } from '@/utils/formatters'

const SCHEDULE_TRUNCATE_THRESHOLD = 12

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
      seatStatsData: null,
      trainingData: null,
      roomType: '',
      loading: true,
      expandedScheduleIds: {},
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

    displayAddress() {
      const address = this.room.address || '茂南区光谷大道88号3楼'
      return this.room.city_name ? `${this.room.city_name} ${address}` : address
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
      const stats = this.seatStatsData || {}
      return {
        total: Number(stats.total || 0),
        available: Number(stats.available || 0),
        occupied: Number(stats.occupied || 0),
        maintenance: Number(stats.maintenance || 0),
      }
    },

    isStudyRoom() {
      return this.roomType === 'study'
    },

    isTrainingRoom() {
      return this.roomType === 'training'
    },

    isComprehensiveRoom() {
      return this.roomType === 'comprehensive'
    },

    trainingStats() {
      if (!this.trainingData) return null
      return {
        classroom_count: this.trainingData.classroom_count || 0,
        class_capacity: this.trainingData.class_capacity || '8-12',
        teacher_count: this.trainingData.teacher_count || 0,
        total_students: this.trainingData.total_students || 0,
      }
    },

    teachers() {
      return this.trainingData?.teachers || []
    },

    trainingCourses() {
      return this.trainingData?.courses || []
    },
  },

  onLoad(options) {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0

    if (options.room_id) {
      this.roomId = options.room_id
      this.isFav = isRoomFollowed(this.roomId)
      this.loadData()
    }
  },

  methods: {
    async loadData() {
      this.loading = true
      try {
        await this.loadRoom()
        if (!this.room || !this.room.id) return
        this.roomType = this.room.room_type || 'study'
        const tasks = []
        if (this.roomType === 'study' || this.roomType === 'comprehensive') {
          tasks.push(this.loadSeatStats())
        }
        if (this.roomType === 'training' || this.roomType === 'comprehensive') {
          tasks.push(this.loadTrainingDetail())
        }
        await Promise.all(tasks)
      } finally {
        this.loading = false
      }
    },

    async loadTrainingDetail() {
      try {
        const data = await getTrainingRoomDetail(this.roomId)
        this.trainingData = data || null
      } catch {
        this.trainingData = null
      }
    },

    async loadRoom() {
      try {
        const data = await fetchBookingRoom(this.roomId)
        this.room = data || {}
        this.isFav = isRoomFollowed(this.roomId)
      } catch {
        // room stays empty
      }
    },

    async loadSeatStats() {
      try {
        const data = await getSeatStats(this.roomId)
        this.seatStatsData = data || null
      } catch {
        this.seatStatsData = null
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

    async onToggleFav() {
      if (!this.roomId) return

      if (this.isFav) {
        try {
          await unfollowRoom(this.roomId)
          this.isFav = false
          uni.showToast({ title: '已取消关注', icon: 'none' })
        } catch {
          uni.showToast({ title: '取消关注失败，请重试', icon: 'none' })
        }
        return
      }

      try {
        await followRoom({
          ...this.room,
          id: this.room.id || this.roomId,
          name: this.roomName,
          address: this.displayAddress,
          cover_image: this.heroImage,
          city_id: this.room.city_id,
          city_name: this.room.city_name,
          min_price: this.room.min_price,
          status: this.room.status,
        })
        this.isFav = true
        uni.showToast({ title: '已加入关注自习室', icon: 'none' })
      } catch {
        uni.showToast({ title: '关注失败，请重试', icon: 'none' })
      }
    },

    onBook() {
      uni.navigateTo({ url: '/pages/booking/seat-select?room_id=' + this.roomId })
    },

    onBackToCourses() {
      uni.navigateTo({ url: '/pages/training/index' })
    },

    onBookStudy() {
      uni.navigateTo({ url: '/pages/booking/seat-select?room_id=' + this.roomId })
    },

    onCourseDetail(course) {
      if (!course || !course.id) return
      uni.navigateTo({ url: '/pages/training/course-detail?course_id=' + course.id })
    },

    courseDetailBadge(course) {
      if (course.is_hot) return { type: 'hot', text: '热销' }
      const tags = course.tags || []
      if (tags.includes('新课')) return { type: 'new', text: '新课' }
      if (tags.includes('名师')) return { type: 'master', text: '名师' }
      if (tags.includes('推荐')) return { type: 'rec', text: '推荐' }
      return null
    },

    scheduleText(course) {
      return formatCourseSchedule(course?.schedule) || '排课待定'
    },

    isScheduleTruncated(course) {
      const text = formatCourseSchedule(course?.schedule)
      return Boolean(text && text.length > SCHEDULE_TRUNCATE_THRESHOLD)
    },

    startDateText(course) {
      return formatCourseStartDate(course?.start_date)
    },

    isScheduleExpanded(course) {
      return Boolean(this.expandedScheduleIds[course?.id])
    },

    toggleSchedule(course) {
      if (!this.isScheduleTruncated(course)) return
      this.expandedScheduleIds[course.id] = !this.expandedScheduleIds[course.id]
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  background: linear-gradient(180deg, #eef1fb 0, $bg-color 520rpx);
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
  background: rgba(255, 255, 255, 0.28);
  border: 1rpx solid rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(35, 41, 68, 0.16);
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
  background: rgba(255, 255, 255, 0.98);
  border-radius: 32rpx;
  padding: 30rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
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
  background: $gradient-card;
  border: 1rpx solid rgba(79, 110, 247, 0.05);
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
  background: $primary-soft;
  border: 1rpx solid rgba(79, 110, 247, 0.08);
}

.tag-blue .tag-text {
  color: $primary;
}

.tag-green {
  background: $success-light;
  border: 1rpx solid rgba(7, 193, 96, 0.08);
}

.tag-green .tag-text {
  color: $success;
}

.tag-orange {
  background: $orange-light;
  border: 1rpx solid rgba(255, 140, 0, 0.08);
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
  border-radius: 24rpx;
  overflow: hidden;
  flex-shrink: 0;
  background: #eef1fb;
  box-shadow: $shadow-card;
  border: 1rpx solid rgba(255, 255, 255, 0.8);
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
  background: $surface;
  border-radius: 32rpx;
  padding: 28rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18rpx;
}

.stat-card {
  border-radius: 24rpx;
  padding: 22rpx 18rpx;
  background: $surface-soft;
  border: 1rpx solid rgba(79, 110, 247, 0.05);
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
  background: rgba(255, 255, 255, 0.98);
  border-top: 1rpx solid rgba(45, 52, 54, 0.06);
  box-shadow: $shadow-bottom;
  backdrop-filter: blur(18rpx);
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
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  font-size: 50rpx;
  line-height: 56rpx;
  color: $white;
  -webkit-text-stroke: 3rpx $text-muted;
  font-family: Arial, Helvetica, sans-serif;
  transform: translateY(1rpx);
}

.heart-icon.active {
  color: $danger;
  -webkit-text-stroke-color: $danger;
}

.book-btn {
  flex: 1;
  height: 92rpx;
  background: $gradient-primary;
  border-radius: 44rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow-float;
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

.back-btn {
  flex: 1;
  height: 92rpx;
  border-radius: 44rpx;
  border: 2rpx solid $border-color;
  background: $white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow-card;
}

.back-btn:active {
  background: $surface-soft;
  transform: translateY(1rpx);
}

.back-btn-text {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-secondary;
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
/* === 培训室新增样式 === */

.section-title-group {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

/* === 培训室简介 === */
.intro-section {
  background: $surface;
  border-radius: 32rpx;
  padding: 28rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.intro-text {
  font-size: 26rpx;
  line-height: 1.6;
  color: $text-secondary;
}

/* === 教室概况 === */
.classroom-section {
  background: $surface;
  border-radius: 32rpx;
  padding: 28rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.section-bar {
  width: 6rpx;
  height: 28rpx;
  border-radius: 6rpx;
  background: $primary;
  margin-right: 12rpx;
}

.stat-classroom {
  background: rgba(79, 110, 247, 0.1);
}

.stat-capacity {
  background: rgba(7, 193, 96, 0.11);
}

.stat-teacher {
  background: rgba(255, 149, 0, 0.13);
}

.stat-students {
  background: rgba(168, 85, 247, 0.12);
}

.door-icon {
  width: 30rpx;
  height: 36rpx;
  border: 4rpx solid $primary;
  border-radius: 8rpx 8rpx 0 0;
}

.group-icon {
  width: 34rpx;
  height: 18rpx;
  border: 3rpx solid $success;
  border-radius: 10rpx;
  position: relative;
}

.group-icon::before,
.group-icon::after {
  content: '';
  position: absolute;
  bottom: -10rpx;
  width: 4rpx;
  height: 10rpx;
  background: $success;
}

.group-icon::before { left: 4rpx; }
.group-icon::after { right: 4rpx; }

.board-icon {
  width: 30rpx;
  height: 22rpx;
  border: 4rpx solid #e67900;
  border-radius: 4rpx;
}

.cap-icon {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50% 50% 50% 0;
  border: 4rpx solid #a855f7;
  transform: rotate(-45deg);
}

/* === 名师团队 === */
.teacher-scroll {
  white-space: nowrap;
}

.teacher-list {
  display: inline-flex;
  gap: 18rpx;
  padding-bottom: 4rpx;
}

.teacher-card {
  width: 200rpx;
  background: $surface;
  border-radius: 24rpx;
  padding: 24rpx 16rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.teacher-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  margin-bottom: 12rpx;
}

.teacher-name {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.teacher-title {
  font-size: 20rpx;
  color: $text-muted;
  margin-top: 4rpx;
  text-align: center;
}

.teacher-rating {
  display: flex;
  align-items: center;
  gap: 4rpx;
  margin-top: 8rpx;
}

.star {
  font-size: 20rpx;
  color: #ffc107;
}

.rating-text {
  font-size: 22rpx;
  font-weight: 500;
  color: $text-primary;
}

/* === 课程列表 === */
.course-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.course-card {
  display: flex;
  background: $surface;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.course-cover {
  width: 180rpx;
  height: 180rpx;
  flex-shrink: 0;
}

.course-body {
  flex: 1;
  padding: 18rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.course-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8rpx;
}

.course-name {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
  line-height: 1.3;
  flex: 1;
}

.course-tag {
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
}

.tag-hot {
  background: rgba(255, 107, 107, 0.12);
}

.tag-hot .tag-text {
  color: $danger;
  font-size: 20rpx;
}

.ctag-hot {
  background: rgba(255, 71, 87, 0.1);
}

.ctag-hot .tag-text {
  color: #FF4757;
  font-size: 20rpx;
}

.ctag-new {
  background: rgba(7, 193, 96, 0.1);
}

.ctag-new .tag-text {
  color: $success;
  font-size: 20rpx;
}

.ctag-master {
  background: rgba(255, 140, 0, 0.1);
}

.ctag-master .tag-text {
  color: #e67900;
  font-size: 20rpx;
}

.ctag-rec {
  background: $primary-soft;
}

.ctag-rec .tag-text {
  color: $primary;
  font-size: 20rpx;
}

.course-teacher {
  margin-top: 8rpx;
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.course-teacher-avatar {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.course-teacher-avatar-ph {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  background: $surface-soft;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.course-teacher-avatar-icon {
  font-size: 18rpx;
  color: $text-muted;
}

.teacher-name-sm {
  font-size: 22rpx;
  color: $text-secondary;
}

.course-schedule {
  margin-top: 6rpx;
  display: flex;
  align-items: center;
  gap: 6rpx;
  min-width: 0;
}

.course-clock-icon {
  font-size: 18rpx;
  color: $text-muted;
  flex-shrink: 0;
}

.schedule-wrap {
  position: relative;
  display: flex;
  align-items: center;
  max-width: 300rpx;
  min-width: 0;
}

.schedule-text {
  font-size: 22rpx;
  color: $text-muted;
  max-width: 300rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.schedule-text.expanded {
  white-space: normal;
  overflow: visible;
}

.course-start-date {
  display: flex;
  align-items: center;
  gap: 6rpx;
  margin-top: 6rpx;
}

.course-start-icon {
  font-size: 18rpx;
  color: $text-muted;
  flex-shrink: 0;
}

.start-date-text {
  font-size: 22rpx;
  color: $text-muted;
}

.schedule-dot {
  font-size: 18rpx;
  color: #DDE2E6;
}

.schedule-status {
  font-size: 22rpx;
  color: $success;
}

.course-bottom {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: 8rpx;
}

.course-price-wrap {
  display: flex;
  align-items: baseline;
}

.course-price {
  font-size: 28rpx;
  font-weight: 700;
  color: $primary;
}

.price-unit {
  font-size: 20rpx;
  color: $text-muted;
}

.book-pill {
  padding: 6rpx 20rpx;
  border-radius: 999rpx;
  background: $primary-soft;
}

.book-pill-text {
  font-size: 22rpx;
  font-weight: 500;
  color: $primary;
}

/* === 空状态 === */
.empty-state {
  padding: 40rpx 0;
  text-align: center;
}

.empty-text {
  font-size: 26rpx;
  color: $text-muted;
}
</style>
