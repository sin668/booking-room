<template>
  <view class="page">
    <!-- 自定义导航栏 -->
    <view class="nav-bar">
      <text class="nav-title">培训课程</text>
    </view>

    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="search-input-wrap">
        <view class="icon icon-search search-icon" />
        <input
          class="search-input"
          type="text"
          placeholder="搜索课程、老师"
          placeholder-class="search-placeholder"
        />
      </view>
    </view>

    <!-- 分类 TAB -->
    <scroll-view class="tab-bar" scroll-x :show-scrollbar="false">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-item', { 'tab-active': activeTab === tab.key }]"
        @tap="switchTab(tab.key)"
      >
        <text class="tab-text">{{ tab.label }}</text>
      </view>
    </scroll-view>

    <!-- 内容区域 -->
    <view class="content">
      <!-- 加载骨架 -->
      <view v-if="loading && trainingRooms.length === 0 && courses.length === 0" class="skeleton-list">
        <view v-for="i in 3" :key="i" class="skeleton-card">
          <view class="skeleton-cover" />
          <view class="skeleton-info">
            <view class="skeleton-line long" />
            <view class="skeleton-line medium" />
            <view class="skeleton-line short" />
          </view>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-else-if="!loading && activeTab === 'all' && trainingRooms.length === 0" class="empty-state">
        <view class="empty-illustration">
          <view class="empty-icon-circle">
            <view class="icon icon-book empty-icon" />
          </view>
        </view>
        <text class="empty-title">暂无培训室</text>
        <text class="empty-subtitle">请稍后再来看看</text>
      </view>
      <view v-else-if="!loading && activeTab !== 'all' && courses.length === 0" class="empty-state">
        <view class="empty-illustration">
          <view class="empty-icon-circle">
            <view class="icon icon-book empty-icon" />
          </view>
        </view>
        <text class="empty-title">暂无课程</text>
        <text class="empty-subtitle">该分类下还没有课程</text>
      </view>

      <!-- 全部：培训室列表 -->
      <template v-else-if="activeTab === 'all'">
        <!-- 推广 Banner -->
        <view class="banner">
          <image
            class="banner-image"
            src="https://images.unsplash.com/photo-1522202176988-662241b9f3ee?w=800&h=400&fit=crop&q=85"
            mode="aspectFill"
          />
          <view class="banner-overlay" />
          <view class="banner-content">
            <text class="banner-title">名师一对一辅导</text>
            <text class="banner-subtitle">考研 / 公考 / 语言 全方位提升</text>
            <view class="banner-cta">
              <text class="banner-cta-text">立即查看</text>
            </view>
          </view>
        </view>

        <!-- 培训室卡片 -->
        <view class="room-list">
          <view
            v-for="(room, index) in trainingRooms"
            :key="room.id"
            :class="['room-card', 'animate-in', `delay-${Math.min(index + 1, 3)}`]"
          >
            <view class="room-header" @tap="goRoomDetail(room.id)">
              <view class="room-cover-wrap">
                <image
                  class="room-cover"
                  :src="roomCover(room, index)"
                  mode="aspectFill"
                  @tap.stop="previewRoomCover(room, index)"
                />
                <view :class="['cover-status', room.status === 'open' ? 'open' : 'closed']">
                  <text class="cover-status-text">{{ room.status === 'open' ? '可预约' : '休息中' }}</text>
                </view>
                <view class="cover-chip">
                  <text class="cover-chip-text">培训</text>
                </view>
              </view>
              <view class="room-info">
                <view class="room-info-top">
                  <view class="room-title-row">
                    <text class="room-name">{{ room.name }}</text>
                    <text :class="['room-status', room.status === 'open' ? 'status-open' : 'status-closed']">
                      {{ room.status === 'open' ? '营业中' : '休息中' }}
                    </text>
                  </view>
                  <view class="room-rating-row">
                    <view class="rating-wrap">
                      <view class="icon icon-star star-icon" />
                      <text class="rating-text">{{ room.rating || '5.0' }}</text>
                    </view>
                    <text v-if="room.business_hours" class="room-hours">{{ room.business_hours }}</text>
                  </view>
                  <view class="room-location-row">
                    <view class="icon icon-location room-location-icon" />
                    <text class="room-address">{{ room.address || '地址待完善' }}</text>
                  </view>
                  <view class="room-tags">
                    <text
                      v-for="tag in roomTags(room, index)"
                      :key="tag"
                      :class="['room-tag', isAccentTag(tag) ? 'accent' : '']"
                    >{{ tag }}</text>
                  </view>
                </view>
                <view class="room-meta" @tap.stop="toggleExpand(room.id)">
                  <text class="hot-label-text">热门推荐课程</text>
                  <view class="room-meta-right">
                    <view class="room-price-wrap">
                      <text class="room-price-symbol">¥</text>
                      <text class="room-price">{{ room.min_price || 0 }}</text>
                      <text class="room-price-unit">起</text>
                    </view>
                    <view :class="['icon icon-arrow-down', 'expand-icon', { 'expand-rotated': expandedRooms.has(room.id) }]" />
                  </view>
                </view>
              </view>
            </view>
            <view :class="['room-courses', { 'room-courses-expanded': expandedRooms.has(room.id) }]">
              <view
                v-for="course in room.hot_courses"
                :key="course.id"
                class="hot-course-item"
                @tap="goCourseDetail(course)"
              >
                <image
                  class="hot-course-cover"
                  :src="course.cover_image"
                  mode="aspectFill"
                  @tap.stop="previewCourseImage(course)"
                />
                <view class="hot-course-info">
                  <view class="hot-course-top">
                    <text class="hot-course-name">{{ course.name }}</text>
                    <text
                      v-if="hotCourseBadge(course)"
                      :class="['hot-course-tag', `htag-${hotCourseBadge(course).type}`]"
                    >{{ hotCourseBadge(course).text }}</text>
                  </view>
                  <view class="hot-course-teacher-row">
                    <image
                      v-if="course.teacher && course.teacher.avatar"
                      class="hot-teacher-avatar"
                      :src="course.teacher.avatar"
                      mode="aspectFill"
                    />
                    <view v-else class="hot-teacher-avatar-ph">
                      <view class="icon icon-user hot-teacher-avatar-icon" />
                    </view>
                    <text class="hot-course-teacher">{{ course.teacher ? course.teacher.name : '未知讲师' }}</text>
                  </view>
                  <view v-if="startDateText(course)" class="hot-course-start-row">
                    <view class="icon icon-book hot-start-icon" />
                    <text class="hot-course-start">{{ startDateText(course) }}</text>
                  </view>
                  <view class="hot-course-schedule-row">
                    <view class="icon icon-clock hot-schedule-icon" />
                    <text :class="['hot-course-schedule', { expanded: isScheduleExpanded(course) }]" @tap.stop="toggleSchedule(course)">{{ scheduleText(course) || '排课待定' }}</text>
                    <text class="hot-schedule-dot">·</text>
                    <text class="hot-course-status">可预约</text>
                  </view>
                  <view class="hot-course-bottom">
                    <view class="hot-course-price-wrap">
                      <text class="hot-course-price-symbol">¥</text>
                      <text class="hot-course-price">{{ course.price }}</text>
                      <text class="hot-course-price-unit">/课时</text>
                    </view>
                    <view class="hot-book-pill" @tap.stop="goCourseBooking(course)">
                      <text class="hot-book-pill-text">预约</text>
                    </view>
                  </view>
                </view>
              </view>
            </view>
          </view>
        </view>
      </template>

      <!-- 分类：课程列表 -->
      <template v-else>
        <view class="course-list">
          <view
            v-for="(course, index) in courses"
            :key="course.id"
            :class="['course-card', 'animate-in', `delay-${Math.min(index + 1, 3)}`]"
            @tap="onCourseDetail(course)"
          >
            <view class="course-cover-wrap">
              <image
                class="course-cover"
                :src="course.cover_image"
                mode="aspectFill"
              />
            </view>
            <view class="course-info">
              <view class="course-info-top">
                <view class="course-name-row">
                  <text class="course-name">{{ course.name }}</text>
                  <text
                    v-if="courseBadge(course)"
                    :class="['course-badge', `badge-${courseBadge(course).type}`]"
                  >{{ courseBadge(course).text }}</text>
                </view>
                <view class="course-teacher-row">
                  <image
                    v-if="course.teacher && course.teacher.avatar"
                    class="teacher-avatar"
                    :src="course.teacher.avatar"
                    mode="aspectFill"
                  />
                  <view v-else class="teacher-avatar-placeholder">
                    <view class="icon icon-user teacher-avatar-icon" />
                  </view>
                  <text class="teacher-name">{{ course.teacher ? course.teacher.name + ' 老师' : '待分配老师' }}</text>
                </view>
                <view v-if="startDateText(course)" class="course-start-row">
                  <view class="icon icon-book course-start-icon" />
                  <text class="course-start-text">{{ startDateText(course) }}</text>
                </view>
                <view v-if="scheduleText(course)" class="course-schedule-row">
                  <view class="icon icon-clock schedule-icon" />
                  <text :class="['course-schedule', { expanded: isScheduleExpanded(course) }]" @tap.stop="toggleSchedule(course)">{{ scheduleText(course) }}</text>
                </view>
                <view class="course-room-row">
                  <view class="icon icon-location course-location-icon" />
                  <text class="room-name-text">{{ course.room_name }}</text>
                </view>
                <!--
                <view class="course-stats">
                  <view class="stats-rating-wrap">
                    <view class="icon icon-star star-icon" />
                    <text class="stats-rating">{{ course.rating }}</text>
                  </view>
                  <text class="stats-count">{{ course.enrollment_count }}人已学</text>                 
                </view>
                -->
              </view>
              <view class="course-footer">
                <view class="course-price-wrap">
                  <text class="course-price-symbol">¥</text>
                  <text class="course-price">{{ course.price }}</text>
                  <text class="course-price-unit">/课时</text>
                </view>
                <view class="course-book-btn">
                  <text class="book-btn-text">预约</text>
                </view>
              </view>
            </view>
          </view>
        </view>
      </template>
    </view>
  </view>
</template>

<script setup>
import { ref, watch } from 'vue'
import { onMounted } from 'vue'
import { onReachBottom } from '@dcloudio/uni-app'
import { getTrainingRooms, getTrainingCourses } from '@/api/training'
import { formatCourseSchedule, formatCourseStartDate } from '@/utils/formatters'

const SCHEDULE_TRUNCATE_THRESHOLD = 12

const expandedScheduleIds = ref({})

function scheduleText(course) {
  return formatCourseSchedule(course?.schedule)
}

function startDateText(course) {
  return formatCourseStartDate(course?.start_date)
}

function isScheduleExpanded(course) {
  return Boolean(expandedScheduleIds.value[course?.id])
}

function toggleSchedule(course) {
  const text = formatCourseSchedule(course?.schedule)
  if (!text || text.length <= SCHEDULE_TRUNCATE_THRESHOLD) return
  expandedScheduleIds.value[course.id] = !expandedScheduleIds.value[course.id]
}

const REAL_ROOM_COVERS = [
  'https://images.unsplash.com/photo-1580582932705-ff3c3993141f?w=400&h=500&fit=crop&q=85',
  'https://images.unsplash.com/photo-1497366754035-f200968a6e72?w=400&h=500&fit=crop&q=85',
  'https://images.unsplash.com/photo-1531542151005-2ec0a6ca7680?w=400&h=500&fit=crop&q=85',
  'https://images.unsplash.com/photo-1522202176988-662241b9f3ee?w=400&h=500&fit=crop&q=85',
  'https://images.unsplash.com/photo-1581726609236-1c7c860c5e8f?w=400&h=500&fit=crop&q=85',
  'https://images.unsplash.com/photo-1568665630394-8f679e2c7a4f?w=400&h=500&fit=crop&q=85',
]

const ROOM_TAG_POOL = [
  ['多媒体', '小班', '1对1'],
  ['投影', '大班', '空调'],
  ['一对一', '隔音', 'WiFi'],
  ['多媒体', '小班', '空调'],
  ['投影', '1对1', 'WiFi'],
]

const ACCENT_TAGS = ['1对1', '一对一', '多媒体']

const activeTab = ref('all')
const trainingRooms = ref([])
const courses = ref([])
const loading = ref(false)
const expandedRooms = ref(new Set())
const roomPage = ref(1)
const roomTotal = ref(0)
const coursePage = ref(1)
const courseTotal = ref(0)

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'primaryschool', label: '小学辅导' },
  { key: 'middleschool', label: '中学辅导' },
  { key: 'civil_service', label: '公考备考' },
  { key: 'skills', label: '技能提升' },
]

function switchTab(key) {
  activeTab.value = key
}

function toggleExpand(roomId) {
  if (expandedRooms.value.has(roomId)) {
    expandedRooms.value.delete(roomId)
  } else {
    expandedRooms.value.add(roomId)
  }
  expandedRooms.value = new Set(expandedRooms.value)
}

function roomCover(room, index = 0) {
  if (room.cover_image) return room.cover_image
  const key = Number(room.id || index)
  return REAL_ROOM_COVERS[key % REAL_ROOM_COVERS.length]
}

function previewRoomCover(room, index) {
  const url = roomCover(room, index)
  uni.previewImage({
    urls: [url],
    current: url,
  })
}

function previewCourseImage(course) {
  if (!course || !course.cover_image) return
  uni.previewImage({
    urls: [course.cover_image],
    current: course.cover_image,
  })
}

function roomTags(room, index = 0) {
  if (room.tags && Array.isArray(room.tags)) return room.tags
  const key = Number(room.id || index)
  return ROOM_TAG_POOL[key % ROOM_TAG_POOL.length]
}

function isAccentTag(tag) {
  return ACCENT_TAGS.includes(tag)
}

function goRoomDetail(roomId) {
  uni.navigateTo({ url: `/pages/booking/detail?room_id=${roomId}` })
}

function onCourseDetail(course) {
  if (!course || !course.id) return
  uni.navigateTo({ url: '/pages/training/course-detail?course_id=' + course.id })
}

function goCourseDetail(course) {
  if (!course || !course.id) return
  uni.navigateTo({ url: '/pages/training/course-detail?course_id=' + course.id })
}

function goCourseBooking(course) {
  if (!course || !course.id) return
  uni.navigateTo({ url: '/pages/training/course-booking?course_id=' + course.id })
}

function hotCourseBadge(course) {
  if (course.is_hot) return { type: 'hot', text: '热销' }
  const tags = course.tags || []
  if (tags.includes('新课')) return { type: 'new', text: '新课' }
  if (tags.includes('名师')) return { type: 'master', text: '名师' }
  if (tags.includes('推荐')) return { type: 'rec', text: '推荐' }
  return null
}

function courseBadge(course) {
  if (course.is_hot) return { type: 'hot', text: '热销' }
  const tags = course.tags || []
  if (tags.includes('新课')) return { type: 'new', text: '新课' }
  if (tags.includes('名师')) return { type: 'master', text: '名师' }
  if (tags.includes('推荐')) return { type: 'rec', text: '推荐' }
  return null
}

async function fetchTrainingRooms(reset = false) {
  if (loading.value) return
  if (reset) {
    roomPage.value = 1
    trainingRooms.value = []
  }
  loading.value = true
  try {
    const data = await getTrainingRooms({
      page: roomPage.value,
      page_size: 10,
    })
    trainingRooms.value = reset ? data.items : trainingRooms.value.concat(data.items)
    roomTotal.value = data.total || 0
    if (!reset) roomPage.value++
  } catch {
    if (reset) trainingRooms.value = []
  } finally {
    loading.value = false
  }
}

async function fetchCourses(reset = false) {
  if (loading.value) return
  if (reset) {
    coursePage.value = 1
    courses.value = []
  }
  loading.value = true
  try {
    const data = await getTrainingCourses({
      page: coursePage.value,
      page_size: 10,
      category: activeTab.value !== 'all' ? activeTab.value : undefined,
    })
    courses.value = reset ? data.items : courses.value.concat(data.items)
    courseTotal.value = data.total || 0
    if (!reset) coursePage.value++
  } catch {
    if (reset) courses.value = []
  } finally {
    loading.value = false
  }
}

watch(activeTab, (newTab) => {
  if (newTab === 'all') {
    fetchTrainingRooms(true)
  } else {
    fetchCourses(true)
  }
})

onMounted(() => {
  fetchTrainingRooms(true)
})

onReachBottom(() => {
  if (activeTab.value === 'all') {
    if (trainingRooms.value.length < roomTotal.value) {
      fetchTrainingRooms(false)
    }
  } else {
    if (courses.value.length < courseTotal.value) {
      fetchCourses(false)
    }
  }
})
</script>

<style lang="scss" scoped>
/* ── Page scaffold ── */
.page {
  min-height: 100vh;
  background: $bg-color;
  padding-bottom: 140rpx;
}

/* ── Nav bar ── */
.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 88rpx;
  background: $surface;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1rpx 0 rgba(0, 0, 0, 0.03);
}

.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: $text-primary;
  letter-spacing: 0.5rpx;
}

/* ── Search bar ── */
.search-bar {
  position: fixed;
  top: 88rpx;
  left: 0;
  right: 0;
  z-index: 90;
  background: $surface;
  padding: 14rpx 28rpx 16rpx;
  border-bottom: 1rpx solid $border-soft;
}

.search-input-wrap {
  background: $surface-soft;
  border-radius: 999rpx;
  padding: 14rpx 24rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.search-icon {
  font-size: 28rpx;
  color: $text-muted;
}

.search-input {
  flex: 1;
  font-size: 27rpx;
  color: $text-primary;
  line-height: 1.4;
}

.search-placeholder {
  color: #C8C9CB;
}

/* ── Category tabs ── */
.tab-bar {
  position: fixed;
  top: 168rpx;
  left: 0;
  right: 0;
  z-index: 80;
  background: $surface;
  white-space: nowrap;
  border-bottom: 1rpx solid $border-soft;
}

.tab-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
  margin: 0 22rpx;
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

/* ── Content ── */
.content {
  padding-top: 244rpx;
}

/* ── Banner ── */
.banner {
  margin: 20rpx 28rpx 24rpx;
  border-radius: 24rpx;
  overflow: hidden;
  height: 256rpx;
  position: relative;
  box-shadow: $shadow-md;
}

.banner-image {
  width: 100%;
  height: 100%;
}

.banner-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, rgba(79, 110, 247, 0.82) 0%, rgba(79, 110, 247, 0.25) 70%);
}

.banner-content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 0 40rpx;
}

.banner-title {
  font-size: 32rpx;
  font-weight: 700;
  color: $white;
  letter-spacing: 1rpx;
}

.banner-subtitle {
  font-size: 23rpx;
  color: rgba(255, 255, 255, 0.78);
  margin-top: 8rpx;
  letter-spacing: 0.5rpx;
}

.banner-cta {
  background: $white;
  border-radius: 999rpx;
  padding: 8rpx 22rpx;
  margin-top: 16rpx;
  align-self: flex-start;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.12);
}

.banner-cta-text {
  font-size: 23rpx;
  font-weight: 600;
  color: $primary;
}

/* ── Animations ── */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-in {
  opacity: 0;
  animation: fadeInUp 0.42s $ease-out forwards;
}

.delay-1 { animation-delay: 0.06s; }
.delay-2 { animation-delay: 0.13s; }
.delay-3 { animation-delay: 0.2s; }

/* ── Room list ── */
.room-list {
  padding: 0 28rpx;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

/* ── Room card ── */
.room-card {
  background: $surface;
  border-radius: 28rpx;
  overflow: hidden;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  transition: transform 0.18s $ease-out, box-shadow 0.18s $ease-out;
}

.room-card:active {
  transform: scale(0.985);
  box-shadow: 0 4rpx 14rpx rgba(45, 52, 54, 0.07);
}

.room-header {
  display: flex;
}

.room-cover-wrap {
  position: relative;
  width: 236rpx;
  min-height: 268rpx;
  flex-shrink: 0;
  overflow: hidden;
  background: #eef1fb;
}

.room-cover {
  width: 100%;
  height: 268rpx;
}

.cover-status {
  position: absolute;
  top: 14rpx;
  left: 14rpx;
  padding: 7rpx 13rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 4rpx 12rpx rgba(35, 41, 68, 0.08);
}

.cover-status.open .cover-status-text {
  color: $success;
}

.cover-status.closed .cover-status-text {
  color: $danger;
}

.cover-status-text {
  font-size: 20rpx;
  font-weight: 700;
}

.cover-chip {
  position: absolute;
  right: 14rpx;
  bottom: 14rpx;
  padding: 6rpx 12rpx;
  border-radius: 16rpx;
  background: rgba(45, 52, 54, 0.54);
}

.cover-chip-text {
  font-size: 19rpx;
  font-weight: 600;
  color: #fdfdff;
}

.room-info {
  flex: 1;
  min-width: 0;
  padding: 20rpx 22rpx 18rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 268rpx;
}

.room-info-top {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.room-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12rpx;
}

.room-name {
  flex: 1;
  min-width: 0;
  font-size: 29rpx;
  font-weight: 700;
  color: $text-primary;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-status {
  font-size: 19rpx;
  font-weight: 500;
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
  letter-spacing: 0.5rpx;
}

.status-open {
  background: $success-light;
  color: $success;
}

.status-closed {
  background: $orange-light;
  color: $orange;
}

.room-rating-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.rating-wrap {
  display: flex;
  align-items: center;
  gap: 4rpx;
}

.star-icon {
  font-size: 22rpx;
  color: #FFC107;
}

.rating-text {
  font-size: 24rpx;
  font-weight: 600;
  color: $text-primary;
}

.room-hours {
  font-size: 21rpx;
  color: $text-muted;
}

.room-location-row {
  display: flex;
  align-items: center;
  gap: 6rpx;
  min-width: 0;
}

.room-location-icon {
  flex-shrink: 0;
  font-size: 22rpx;
  color: $text-muted;
}

.room-address {
  flex: 1;
  min-width: 0;
  font-size: 21rpx;
  line-height: 1.35;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-tags {
  display: flex;
  align-items: center;
  gap: 8rpx;
  min-width: 0;
  flex-wrap: wrap;
}

.room-tag {
  padding: 6rpx 12rpx;
  border-radius: 18rpx;
  background: $surface-soft;
  border: 1rpx solid rgba(99, 110, 114, 0.06);
  color: $text-secondary;
  font-size: 20rpx;
  line-height: 1;
}

.room-tag.accent {
  background: $primary-light;
  color: $primary;
}

.room-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  margin-top: 8rpx;
  padding-top: 10rpx;
  border-top: 1rpx solid $border-soft;
}

.room-meta-right {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-shrink: 0;
}

.hot-label-text {
  font-size: 22rpx;
  color: $primary;
  font-weight: 500;
  background: $primary-soft;
  padding: 5rpx 14rpx;
  border-radius: 8rpx;
}

.room-price-wrap {
  display: flex;
  align-items: baseline;
  gap: 2rpx;
}

.room-price-symbol {
  font-size: 22rpx;
  font-weight: 800;
  color: $danger;
  line-height: 1;
}

.room-price {
  font-size: 34rpx;
  font-weight: 800;
  color: $danger;
  line-height: 1;
}

.room-price-unit {
  font-size: 20rpx;
  font-weight: 400;
  color: $text-muted;
}

.expand-icon {
  font-size: 24rpx;
  color: $text-muted;
  transition: transform 0.32s $ease-out;
}

.expand-rotated {
  transform: rotate(180deg);
}

/* ── Room courses (expandable) ── */
.room-courses {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.36s $ease-out;
}

.room-courses-expanded {
  max-height: 2400rpx;
}

.hot-course-item {
  display: flex;
  gap: 16rpx;
  padding: 18rpx 22rpx;
  border-top: 1rpx solid $border-soft;
}

.hot-course-item:active {
  background: $surface-soft;
}

.hot-course-cover {
  width: 160rpx;
  height: 160rpx;
  border-radius: 18rpx;
  flex-shrink: 0;
}

.hot-course-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 4rpx;
}

.hot-course-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8rpx;
}

.hot-course-name {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
  flex: 1;
  min-width: 0;
}

.hot-course-tag {
  font-size: 18rpx;
  font-weight: 500;
  padding: 3rpx 10rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
  line-height: 1.2;
}

.htag-hot {
  background: rgba(255, 71, 87, 0.1);
  color: #FF4757;
}

.htag-new {
  background: rgba(7, 193, 96, 0.1);
  color: $success;
}

.htag-master {
  background: rgba(255, 140, 0, 0.1);
  color: #e67900;
}

.htag-rec {
  background: $primary-soft;
  color: $primary;
}

.hot-course-teacher-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.hot-teacher-avatar {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.hot-teacher-avatar-ph {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  background: $surface-soft;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hot-teacher-avatar-icon {
  font-size: 18rpx;
  color: $text-muted;
}

.hot-course-teacher {
  font-size: 22rpx;
  color: $text-secondary;
}

.hot-course-start-row {
  display: flex;
  align-items: center;
  gap: 4rpx;
}

.hot-start-icon {
  font-size: 18rpx;
  color: $text-muted;
}

.hot-course-start {
  font-size: 20rpx;
  color: $text-muted;
}

.hot-course-schedule-row {
  display: flex;
  align-items: center;
  gap: 4rpx;
  min-width: 0;
}

.hot-schedule-icon {
  font-size: 18rpx;
  color: $text-muted;
}

.hot-course-schedule {
  font-size: 20rpx;
  color: $text-muted;
  max-width: 300rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-course-schedule.expanded {
  white-space: normal;
  overflow: visible;
}

.hot-schedule-dot {
  font-size: 18rpx;
  color: #DDE2E6;
}

.hot-course-status {
  font-size: 20rpx;
  color: $success;
}

.hot-course-bottom {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}

.hot-course-price-wrap {
  display: flex;
  align-items: baseline;
  gap: 2rpx;
}

.hot-course-price-symbol {
  font-size: 20rpx;
  font-weight: 700;
  color: $primary;
  line-height: 1;
}

.hot-course-price {
  font-size: 28rpx;
  font-weight: 700;
  color: $primary;
  line-height: 1;
}

.hot-course-price-unit {
  font-size: 18rpx;
  color: $text-muted;
}

.hot-book-pill {
  padding: 5rpx 18rpx;
  border-radius: 999rpx;
  background: $primary-soft;
}

.hot-book-pill-text {
  font-size: 20rpx;
  font-weight: 500;
  color: $primary;
}

/* ── Course list ── */
.course-list {
  padding: 24rpx 28rpx 0;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

/* ── Course card ── */
.course-card {
  display: flex;
  min-height: 244rpx;
  background: $surface;
  border-radius: 28rpx;
  overflow: hidden;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  transition: transform 0.18s $ease-out, box-shadow 0.18s $ease-out;
}

.course-card:active {
  transform: scale(0.985);
  box-shadow: 0 4rpx 14rpx rgba(45, 52, 54, 0.07);
}

.course-cover-wrap {
  position: relative;
  width: 236rpx;
  min-height: 244rpx;
  flex-shrink: 0;
  overflow: hidden;
  background: #eef1fb;
}

.course-cover {
  width: 100%;
  height: 244rpx;
}

.course-badge {
  position: absolute;
  top: 14rpx;
  right: 14rpx;
  font-size: 19rpx;
  font-weight: 500;
  padding: 5rpx 12rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
  letter-spacing: 0.5rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 4rpx 12rpx rgba(35, 41, 68, 0.08);
}

.badge-hot {
  background: rgba(255, 255, 255, 0.94);
  color: #FF4757;
}

.badge-new {
  background: rgba(255, 255, 255, 0.94);
  color: $success;
}

.badge-master {
  background: rgba(255, 255, 255, 0.94);
  color: #e67900;
}

.badge-rec {
  background: rgba(255, 255, 255, 0.94);
  color: $primary;
}

.course-info {
  flex: 1;
  min-width: 0;
  padding: 20rpx 22rpx 18rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 244rpx;
}

.course-info-top {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.course-name-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10rpx;
}

.course-name {
  flex: 1;
  min-width: 0;
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.course-teacher-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.teacher-avatar {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.teacher-avatar-placeholder {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  background: $surface-soft;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.teacher-avatar-icon {
  font-size: 22rpx;
  color: $text-muted;
}

.teacher-name {
  font-size: 23rpx;
  color: $text-secondary;
}

.course-start-row {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.course-start-icon {
  font-size: 18rpx;
  color: $text-muted;
}

.course-start-text {
  font-size: 21rpx;
  color: $text-muted;
}

.course-schedule-row {
  display: flex;
  align-items: center;
  gap: 6rpx;
  min-width: 0;
}

.schedule-icon {
  font-size: 18rpx;
  color: $text-muted;
}

.course-schedule {
  font-size: 21rpx;
  color: $text-muted;
  max-width: 360rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-schedule.expanded {
  white-space: normal;
  overflow: visible;
}

.course-dot {
  font-size: 20rpx;
  color: #DDE2E6;
}

.course-location-icon {
  font-size: 20rpx;
  color: $text-muted;
}

.room-name-text {
  font-size: 21rpx;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.course-stats {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.stats-rating-wrap {
  display: flex;
  align-items: center;
  gap: 4rpx;
}

.stats-rating {
  font-size: 24rpx;
  font-weight: 600;
  color: $text-primary;
}

.stats-count {
  font-size: 21rpx;
  color: $text-muted;
}

.course-footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: 4rpx;
}

.course-price-wrap {
  display: flex;
  align-items: baseline;
  gap: 2rpx;
}

.course-price-symbol {
  font-size: 22rpx;
  font-weight: 800;
  color: $danger;
  line-height: 1;
}

.course-price {
  font-size: 34rpx;
  font-weight: 800;
  color: $danger;
  line-height: 1;
}

.course-price-unit {
  font-size: 20rpx;
  font-weight: 400;
  color: $text-muted;
}

.course-book-btn {
  background: $primary-light;
  border-radius: 999rpx;
  padding: 10rpx 28rpx;
}

.course-book-btn:active {
  background: rgba(79, 110, 247, 0.18);
  transform: scale(0.96);
  transition: all 0.12s;
}

.book-btn-text {
  font-size: 24rpx;
  color: $primary;
  font-weight: 600;
  letter-spacing: 1rpx;
}

/* ── Loading skeleton ── */
.skeleton-list {
  padding: 24rpx 28rpx 0;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.skeleton-card {
  display: flex;
  min-height: 244rpx;
  background: $surface;
  border-radius: 28rpx;
  overflow: hidden;
  border: 1rpx solid $border-soft;
}

.skeleton-cover {
  width: 236rpx;
  min-height: 244rpx;
  flex-shrink: 0;
  background: linear-gradient(90deg, #F0F1F5 25%, #F7F8FA 50%, #F0F1F5 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.4s ease-in-out infinite;
}

.skeleton-info {
  flex: 1;
  padding: 24rpx 22rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14rpx;
}

.skeleton-line {
  height: 22rpx;
  border-radius: 8rpx;
  background: linear-gradient(90deg, #F0F1F5 25%, #F7F8FA 50%, #F0F1F5 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.4s ease-in-out infinite;
}

.skeleton-line.long {
  width: 70%;
}

.skeleton-line.medium {
  width: 56%;
}

.skeleton-line.short {
  width: 40%;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ── Empty state ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 24rpx 28rpx 0;
  padding: 132rpx 0;
  border-radius: 24rpx;
  background: $surface;
  border: 1rpx solid $border-soft;
  box-shadow: $shadow-card;
}

.empty-illustration {
  margin-bottom: 28rpx;
}

.empty-icon-circle {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: $primary-soft;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon {
  font-size: 52rpx;
  color: $text-muted;
}

.empty-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-secondary;
}

.empty-subtitle {
  font-size: 23rpx;
  color: $text-muted;
  margin-top: 6rpx;
}
</style>
