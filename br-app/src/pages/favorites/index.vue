<template>
  <view class="page">
    <!-- 顶部导航 -->
    <view class="nav-overlay">
      <view :style="{ height: statusBarHeight + 'px' }" />
      <view class="nav-bar">
        <view class="nav-btn" @tap="onBack">
          <view class="nav-chevron" />
        </view>
        <text class="nav-title">我的关注</text>
        <view class="nav-placeholder" />
      </view>
    </view>

    <!-- Tab 栏 -->
    <view class="tab-bar">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-item', { 'tab-active': activeTab === tab.key }]"
        @tap="onTabChange(tab.key)"
      >
        <text class="tab-text">{{ tab.label }}</text>
      </view>
    </view>

    <!-- 内容区 -->
    <scroll-view class="content" scroll-y @scrolltolower="onReachBottom">
      <!-- 关注自习室 -->
      <view v-if="activeTab === 'room'" class="list-section">
        <view v-if="loading" class="skeleton-list">
          <view v-for="i in 3" :key="i" class="skeleton-card">
            <view class="skeleton-block skeleton-cover" />
            <view class="skeleton-info">
              <view class="skeleton-line skeleton-line-long" />
              <view class="skeleton-line skeleton-line-medium" />
              <view class="skeleton-line skeleton-line-short" />
            </view>
          </view>
        </view>
        <view v-else-if="studyRooms.length === 0" class="empty-state">
          <view class="empty-icon-wrap">
            <view class="empty-icon empty-icon-room" />
          </view>
          <text class="empty-title">还没有关注自习室</text>
          <text class="empty-desc">去首页发现你喜欢的自习室吧</text>
          <view class="empty-btn" @tap="goExploreRooms">
            <text class="empty-btn-text">去发现</text>
          </view>
        </view>
        <view v-else class="list">
          <view
            v-for="room in studyRooms"
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
      <view v-if="activeTab === 'training'" class="list-section">
        <view v-if="loading" class="skeleton-list">
          <view v-for="i in 3" :key="i" class="skeleton-card">
            <view class="skeleton-block skeleton-cover" />
            <view class="skeleton-info">
              <view class="skeleton-line skeleton-line-long" />
              <view class="skeleton-line skeleton-line-medium" />
            </view>
          </view>
        </view>
        <view v-else-if="trainingRooms.length === 0" class="empty-state">
          <view class="empty-icon-wrap">
            <view class="empty-icon empty-icon-training" />
          </view>
          <text class="empty-title">还没有关注培训室</text>
          <text class="empty-desc">去培训频道发现优质培训室</text>
          <view class="empty-btn" @tap="goExploreTraining">
            <text class="empty-btn-text">去发现</text>
          </view>
        </view>
        <view v-else class="list">
          <view
            v-for="room in trainingRooms"
            :key="room.id"
            class="room-card"
            @tap="onTapTrainingRoom(room)"
          >
            <image class="room-cover" :src="roomCover(room)" mode="aspectFill" />
            <view class="room-info">
              <text class="room-name">{{ room.name }}</text>
              <view class="room-address-row">
                <view class="icon icon-location room-address-icon" />
                <text class="room-address">{{ room.address || '地址待完善' }}</text>
              </view>
              <view class="room-meta">
                <text class="room-tag blue">培训室</text>
                <text :class="['room-price', { muted: !roomPriceText(room) }]">
                  {{ roomPriceText(room) || '查看详情' }}
                </text>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 关注课程 -->
      <view v-if="activeTab === 'course'" class="list-section">
        <view v-if="loading" class="skeleton-list">
          <view v-for="i in 3" :key="i" class="skeleton-card">
            <view class="skeleton-block skeleton-cover" />
            <view class="skeleton-info">
              <view class="skeleton-line skeleton-line-long" />
              <view class="skeleton-line skeleton-line-medium" />
              <view class="skeleton-line skeleton-line-short" />
            </view>
          </view>
        </view>
        <view v-else-if="courses.length === 0" class="empty-state">
          <view class="empty-icon-wrap">
            <view class="empty-icon empty-icon-course" />
          </view>
          <text class="empty-title">还没有关注课程</text>
          <text class="empty-desc">去培训频道发现优质课程</text>
          <view class="empty-btn" @tap="goExploreTraining">
            <text class="empty-btn-text">去发现</text>
          </view>
        </view>
        <view v-else class="list">
          <view
            v-for="course in courses"
            :key="course.id"
            class="course-card"
            @tap="onTapCourse(course)"
          >
            <image
              v-if="course.cover_image"
              class="course-cover"
              :src="course.cover_image"
              mode="aspectFill"
            />
            <view v-else class="course-cover-ph">
              <view class="course-cover-icon" />
            </view>
            <view class="course-info">
              <text class="course-name">{{ course.name }}</text>
              <text v-if="course.description" class="course-desc">{{ course.description }}</text>
              <view class="course-meta">
                <text v-if="Number(course.min_price) > 0" class="course-price">¥{{ course.min_price }}起</text>
                <text v-else class="course-price free">免费</text>
                <view class="icon icon-arrow-right course-arrow" />
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 关注教师 -->
      <view v-if="activeTab === 'teacher'" class="list-section">
        <view v-if="loading" class="skeleton-list">
          <view v-for="i in 3" :key="i" class="skeleton-card skeleton-teacher">
            <view class="skeleton-block skeleton-avatar" />
            <view class="skeleton-info">
              <view class="skeleton-line skeleton-line-long" />
              <view class="skeleton-line skeleton-line-short" />
            </view>
          </view>
        </view>
        <view v-else-if="teachers.length === 0" class="empty-state">
          <view class="empty-icon-wrap">
            <view class="empty-icon empty-icon-teacher" />
          </view>
          <text class="empty-title">还没有关注教师</text>
          <text class="empty-desc">去培训频道发现优秀讲师</text>
          <view class="empty-btn" @tap="goExploreTraining">
            <text class="empty-btn-text">去发现</text>
          </view>
        </view>
        <view v-else class="list">
          <view
            v-for="teacher in teachers"
            :key="teacher.id"
            class="teacher-card"
            @tap="onTapTeacher(teacher)"
          >
            <image
              v-if="teacher.cover_image"
              class="teacher-avatar"
              :src="teacher.cover_image"
              mode="aspectFill"
            />
            <view v-else class="teacher-avatar-ph">
              <text class="teacher-avatar-text">{{ (teacher.name || 'T').charAt(0) }}</text>
            </view>
            <view class="teacher-info">
              <text class="teacher-name">{{ teacher.name }}</text>
              <text v-if="teacher.description" class="teacher-desc">{{ teacher.description }}</text>
            </view>
            <view class="icon icon-arrow-right teacher-arrow" />
          </view>
        </view>
      </view>

      <view style="height: 60rpx;" />
    </scroll-view>
  </view>
</template>

<script>
import { getAllFollowedCategories } from '@/services/followedRooms'
import { formatRoomMinPrice } from '@/utils/formatters'

const ROOM_COVERS = [
  'https://images.unsplash.com/photo-1497366216548-37526070297c?w=720&h=520&fit=crop&q=85',
  'https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=720&h=520&fit=crop&q=85',
  'https://images.unsplash.com/photo-1527192491265-7e15c55b1ed2?w=720&h=520&fit=crop&q=85',
]

export default {
  data() {
    return {
      statusBarHeight: 0,
      loading: false,
      activeTab: 'room',
      studyRooms: [],
      trainingRooms: [],
      courses: [],
      teachers: [],
    }
  },
  computed: {
    tabs() {
      return [
        { key: 'room', label: '关注自习室' },
        { key: 'training', label: '关注培训室' },
        { key: 'course', label: '关注课程' },
        { key: 'teacher', label: '关注教师' },
      ]
    },
  },
  onLoad() {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
    this.loadData()
  },
  onPullDownRefresh() {
    this.loadData().finally(() => {
      uni.stopPullDownRefresh()
    })
  },
  methods: {
    onBack() {
      uni.navigateBack()
    },

    onTabChange(key) {
      this.activeTab = key
    },

    async loadData() {
      this.loading = true
      try {
        const categories = await getAllFollowedCategories()
        this.studyRooms = categories.studyRooms
        this.trainingRooms = categories.trainingRooms
        this.courses = categories.courses
        this.teachers = categories.teachers
      } catch {
        // keep current data on error
      } finally {
        this.loading = false
      }
    },

    roomCover(room) {
      if (room.cover_image) return room.cover_image
      const key = Number(room.id || 0)
      return ROOM_COVERS[key % ROOM_COVERS.length]
    },

    roomPriceText(room) {
      return formatRoomMinPrice(room)
    },

    onTapRoom(room) {
      if (!room?.id) return
      uni.navigateTo({ url: `/pages/booking/detail?room_id=${room.id}` })
    },

    onTapTrainingRoom(room) {
      if (!room?.id) return
      uni.navigateTo({ url: `/pages/booking/detail?room_id=${room.id}` })
    },

    onTapCourse(course) {
      if (!course?.id) return
      uni.navigateTo({ url: `/pages/training/course-detail?course_id=${course.id}` })
    },

    onTapTeacher(teacher) {
      if (!teacher?.id) return
      uni.navigateTo({ url: `/pages/teacher/profile?teacher_id=${teacher.id}` })
    },

    goExploreRooms() {
      uni.switchTab({ url: '/pages/booking/index' })
    },

    goExploreTraining() {
      uni.switchTab({ url: '/pages/training/index' })
    },

    onReachBottom() {},
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
}

/* Nav bar */
.nav-overlay {
  background: #fff;
}

.nav-bar {
  display: flex;
  align-items: center;
  height: 88rpx;
  padding: 0 16rpx;
}

.nav-btn {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.nav-btn:active {
  background: $bg-color;
}

.nav-chevron {
  width: 20rpx;
  height: 20rpx;
  border-left: 4rpx solid $text-primary;
  border-bottom: 4rpx solid $text-primary;
  transform: rotate(45deg);
  margin-left: 8rpx;
}

.nav-title {
  flex: 1;
  text-align: center;
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
}

.nav-placeholder {
  width: 72rpx;
}

/* Tab bar */
.tab-bar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  background: $surface;
  border-bottom: 1rpx solid $border-soft;
}

.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
  position: relative;
}

.tab-text {
  font-size: 26rpx;
  color: $text-secondary;
  letter-spacing: 1rpx;
}

.tab-active .tab-text {
  color: $primary;
  font-weight: 600;
}

.tab-active::after {
  content: '';
  position: absolute;
  bottom: 4rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 32rpx;
  height: 4rpx;
  background: $primary;
  border-radius: 2rpx;
}

/* Content */
.content {
  height: calc(100vh - var(--status-bar-height, 44px) - 88rpx - 84rpx);
}

.list-section {
  padding: 20rpx 28rpx 0;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

/* Room card */
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

.room-tag.blue {
  background: rgba(108, 92, 231, 0.08);
  color: $purple;
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

/* Course card */
.course-card {
  display: flex;
  min-height: 176rpx;
  overflow: hidden;
  border-radius: 26rpx;
  background: $surface;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  transition: transform 0.2s;
}

.course-card:active {
  transform: scale(0.98);
}

.course-cover {
  width: 176rpx;
  height: 176rpx;
  flex-shrink: 0;
  background: #eef1fb;
}

.course-cover-ph {
  width: 176rpx;
  height: 176rpx;
  flex-shrink: 0;
  background: linear-gradient(135deg, rgba(79, 110, 247, 0.08), rgba(108, 92, 231, 0.06));
  display: flex;
  align-items: center;
  justify-content: center;
}

.course-cover-icon {
  width: 56rpx;
  height: 56rpx;
  border: 4rpx solid $primary;
  border-radius: 12rpx;
  position: relative;
}

.course-cover-icon::after {
  content: '';
  position: absolute;
  left: 10rpx;
  right: 10rpx;
  top: 50%;
  height: 4rpx;
  background: $primary;
  border-radius: 2rpx;
}

.course-info {
  flex: 1;
  min-width: 0;
  padding: 20rpx 22rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.course-name {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-desc {
  font-size: 23rpx;
  color: $text-secondary;
  margin-top: 8rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14rpx;
}

.course-price {
  font-size: 28rpx;
  font-weight: 700;
  color: $danger;
}

.course-price.free {
  color: $success;
}

.course-arrow {
  font-size: 24rpx;
  color: $text-muted;
}

/* Teacher card */
.teacher-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx;
  border-radius: 26rpx;
  background: $surface;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  transition: transform 0.2s;
}

.teacher-card:active {
  transform: scale(0.98);
}

.teacher-avatar {
  width: 108rpx;
  height: 108rpx;
  border-radius: 50%;
  flex-shrink: 0;
  background: #eef1fb;
}

.teacher-avatar-ph {
  width: 108rpx;
  height: 108rpx;
  border-radius: 50%;
  flex-shrink: 0;
  background: linear-gradient(135deg, $primary, $purple);
  display: flex;
  align-items: center;
  justify-content: center;
}

.teacher-avatar-text {
  font-size: 40rpx;
  font-weight: 700;
  color: #fff;
}

.teacher-info {
  flex: 1;
  min-width: 0;
}

.teacher-name {
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
  display: block;
}

.teacher-desc {
  display: block;
  font-size: 24rpx;
  color: $text-secondary;
  margin-top: 8rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.teacher-arrow {
  font-size: 24rpx;
  color: $text-muted;
  flex-shrink: 0;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 40rpx;
}

.empty-icon-wrap {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background: $primary-soft;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32rpx;
}

.empty-icon {
  position: relative;
}

.empty-icon-room {
  width: 60rpx;
  height: 48rpx;
  border: 5rpx solid $primary;
  border-top: none;
  border-radius: 0 0 10rpx 10rpx;
}

.empty-icon-room::before {
  content: '';
  position: absolute;
  left: -8rpx;
  right: -8rpx;
  top: -22rpx;
  height: 22rpx;
  border-radius: 12rpx 12rpx 4rpx 4rpx;
  background: $primary;
}

.empty-icon-training {
  width: 56rpx;
  height: 56rpx;
  border: 5rpx solid $purple;
  border-radius: 12rpx;
}

.empty-icon-training::after {
  content: '';
  position: absolute;
  left: 12rpx;
  right: 12rpx;
  top: 50%;
  height: 5rpx;
  background: $purple;
  border-radius: 3rpx;
}

.empty-icon-course {
  width: 52rpx;
  height: 64rpx;
  border: 5rpx solid $success;
  border-radius: 8rpx;
}

.empty-icon-course::before,
.empty-icon-course::after {
  content: '';
  position: absolute;
  left: 10rpx;
  right: 10rpx;
  height: 4rpx;
  background: $success;
  border-radius: 2rpx;
}

.empty-icon-course::before { top: 16rpx; }
.empty-icon-course::after { top: 30rpx; }

.empty-icon-teacher {
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  border: 5rpx solid $orange;
}

.empty-icon-teacher::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  background: $orange;
}

.empty-title {
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
}

.empty-desc {
  font-size: 24rpx;
  color: $text-muted;
  margin-top: 10rpx;
}

.empty-btn {
  margin-top: 32rpx;
  padding: 16rpx 48rpx;
  border-radius: 999rpx;
  background: $gradient-primary;
  box-shadow: 0 8rpx 24rpx rgba(79, 110, 247, 0.25);
}

.empty-btn:active {
  opacity: 0.85;
}

.empty-btn-text {
  font-size: 26rpx;
  font-weight: 600;
  color: #fff;
}

/* Skeleton */
.skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.skeleton-card {
  display: flex;
  min-height: 188rpx;
  border-radius: 26rpx;
  background: $surface;
  overflow: hidden;
  box-shadow: $shadow-sm;
}

.skeleton-card.skeleton-teacher {
  align-items: center;
  padding: 24rpx;
  gap: 20rpx;
}

.skeleton-cover {
  width: 184rpx;
  height: 188rpx;
}

.skeleton-avatar {
  width: 108rpx;
  height: 108rpx;
  border-radius: 50%;
}

.skeleton-info {
  flex: 1;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  justify-content: center;
}

.skeleton-line {
  height: 24rpx;
  border-radius: 12rpx;
}

.skeleton-line-long { width: 70%; }
.skeleton-line-medium { width: 55%; }
.skeleton-line-short { width: 35%; }

.skeleton-block {
  background: linear-gradient(90deg, #eef1fb 0%, #f7f8ff 48%, #eef1fb 100%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.2s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
