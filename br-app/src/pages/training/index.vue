<template>
  <view class="page">
    <!-- 自定义导航栏 -->
    <view class="nav-bar">
      <text class="nav-title">培训课程</text>
    </view>

    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="search-input-wrap">
        <text class="search-icon">🔍</text>
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
      <!-- 加载状态 -->
      <view v-if="loading && trainingRooms.length === 0 && courses.length === 0" class="loading-state">
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 空状态 -->
      <view v-else-if="!loading && activeTab === 'all' && trainingRooms.length === 0" class="empty-state">
        <text class="empty-text">暂无培训室</text>
      </view>
      <view v-else-if="!loading && activeTab !== 'all' && courses.length === 0" class="empty-state">
        <text class="empty-text">暂无课程</text>
      </view>

      <!-- 全部：培训室列表 -->
      <template v-else-if="activeTab === 'all'">
        <view
          v-for="room in trainingRooms"
          :key="room.id"
          class="room-card"
        >
          <view class="room-header" @tap="toggleExpand(room.id)">
            <image
              class="room-cover"
              :src="room.cover_image || 'https://images.unsplash.com/photo-1580582932705-ff3c3993141f?w=300&h=400&fit=crop'"
              mode="aspectFill"
            />
            <view class="room-info">
              <view class="room-name-row">
                <text class="room-name">{{ room.name }}</text>
                <text :class="['room-status', room.status === 'open' ? 'status-open' : 'status-closed']">
                  {{ room.status === 'open' ? '营业中' : '休息中' }}
                </text>
              </view>
              <view class="room-meta">
                <text class="meta-rating">★ {{ room.min_price }}起</text>
                <text class="meta-dot">·</text>
                <text class="meta-address">{{ room.address }}</text>
              </view>
              <view class="hot-courses-label">
                <text class="hot-label-text">热门推荐课程</text>
                <text :class="['expand-icon', { 'expand-icon-rotated': expandedRooms.has(room.id) }]">▼</text>
              </view>
            </view>
          </view>
          <view :class="['room-courses', { 'room-courses-expanded': expandedRooms.has(room.id) }]">
            <view
              v-for="course in room.hot_courses"
              :key="course.id"
              class="hot-course-item"
            >
              <image
                class="hot-course-cover"
                :src="course.cover_image || 'https://images.unsplash.com/photo-1546410531-bb4caa6b5cb9?w=100&h=100&fit=crop'"
                mode="aspectFill"
              />
              <view class="hot-course-info">
                <text class="hot-course-name">{{ course.name }}</text>
                <text class="hot-course-meta">
                  {{ course.teacher ? course.teacher.name : '未知讲师' }} · {{ course.enrollment_count }}人
                </text>
              </view>
              <text class="hot-course-price">¥{{ course.price }}</text>
            </view>
          </view>
        </view>
      </template>

      <!-- 分类：课程列表 -->
      <template v-else>
        <view
          v-for="course in courses"
          :key="course.id"
          class="course-card"
        >
          <image
            class="course-cover"
            :src="course.cover_image || 'https://images.unsplash.com/photo-1546410531-bb4caa6b5cb9?w=300&h=300&fit=crop'"
            mode="aspectFill"
          />
          <view class="course-info">
            <view class="course-name-row">
              <text class="course-name">{{ course.name }}</text>
              <text v-if="course.is_hot" class="course-badge badge-hot">热销</text>
            </view>
            <view class="course-teacher">
              <text class="teacher-name">{{ course.teacher ? course.teacher.name + ' 老师' : '未知老师' }}</text>
              <text class="course-dot">·</text>
              <text class="room-name-text">{{ course.room_name }}</text>
            </view>
            <view class="course-stats">
              <text class="stats-rating">★ {{ course.rating }}</text>
              <text class="stats-count">{{ course.enrollment_count }}人已学</text>
            </view>
            <view class="course-footer">
              <view class="course-price-wrap">
                <text class="course-price">¥{{ course.price }}</text>
                <text class="course-price-unit">/课时</text>
              </view>
              <view class="course-book-btn">
                <text class="book-btn-text">预约</text>
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
.page {
  min-height: 100vh;
  background: #F5F6FA;
  padding-bottom: 120rpx;
}

.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 88rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1rpx 0 rgba(0, 0, 0, 0.04);
}

.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #2D3436;
}

.search-bar {
  position: fixed;
  top: 88rpx;
  left: 0;
  right: 0;
  z-index: 90;
  background: #ffffff;
  padding: 16rpx 32rpx;
  border-bottom: 1rpx solid #F0F0F0;
}

.search-input-wrap {
  background: #F1F2F6;
  border-radius: 999rpx;
  padding: 16rpx 28rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.search-icon {
  font-size: 24rpx;
  color: #B2BEC3;
}

.search-input {
  flex: 1;
  font-size: 28rpx;
  color: #2D3436;
}

.search-placeholder {
  color: #C8C9CB;
}

.tab-bar {
  position: fixed;
  top: 176rpx;
  left: 0;
  right: 0;
  z-index: 80;
  background: #ffffff;
  white-space: nowrap;
  border-bottom: 1rpx solid #F0F0F0;
}

.tab-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx 0;
  margin: 0 24rpx;
  position: relative;
}

.tab-text {
  font-size: 28rpx;
  color: #636E72;
}

.tab-active .tab-text {
  color: #4F6EF7;
  font-weight: 600;
}

.tab-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40rpx;
  height: 4rpx;
  background: #4F6EF7;
  border-radius: 2rpx;
}

.content {
  padding-top: 248rpx;
}

.loading-state,
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 120rpx 0;
}

.loading-text,
.empty-text {
  font-size: 28rpx;
  color: #B2BEC3;
}

.room-card {
  margin: 24rpx 32rpx;
  background: #ffffff;
  border-radius: 28rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.room-header {
  display: flex;
  padding: 0;
}

.room-cover {
  width: 224rpx;
  height: 256rpx;
  flex-shrink: 0;
}

.room-info {
  flex: 1;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.room-name-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.room-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #2D3436;
  flex: 1;
}

.room-status {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
  margin-left: 12rpx;
}

.status-open {
  background: #E8F8E8;
  color: #00B894;
}

.status-closed {
  background: #FFF3E0;
  color: #FF9500;
}

.room-meta {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 12rpx;
}

.meta-rating {
  font-size: 24rpx;
  font-weight: 500;
  color: #2D3436;
}

.meta-dot {
  font-size: 20rpx;
  color: #B2BEC3;
}

.meta-address {
  font-size: 22rpx;
  color: #636E72;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-courses-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
}

.hot-label-text {
  font-size: 24rpx;
  color: #4F6EF7;
  background: #F0F1F8;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
}

.expand-icon {
  font-size: 20rpx;
  color: #B2BEC3;
  transition: transform 0.3s ease;
}

.expand-icon-rotated {
  transform: rotate(180deg);
}

.room-courses {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.35s ease;
}

.room-courses-expanded {
  max-height: 1000rpx;
}

.hot-course-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 12rpx 24rpx;
  border-top: 1rpx solid #F8F8F8;
}

.hot-course-cover {
  width: 72rpx;
  height: 72rpx;
  border-radius: 12rpx;
  flex-shrink: 0;
}

.hot-course-info {
  flex: 1;
  min-width: 0;
}

.hot-course-name {
  font-size: 26rpx;
  font-weight: 500;
  color: #2D3436;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-course-meta {
  font-size: 22rpx;
  color: #B2BEC3;
  margin-top: 4rpx;
}

.hot-course-price {
  font-size: 30rpx;
  font-weight: 600;
  color: #4F6EF7;
  flex-shrink: 0;
}

.course-card {
  margin: 24rpx 32rpx;
  background: #ffffff;
  border-radius: 28rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
  display: flex;
}

.course-cover {
  width: 224rpx;
  height: 224rpx;
  flex-shrink: 0;
}

.course-info {
  flex: 1;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.course-name-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.course-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #2D3436;
  flex: 1;
}

.course-badge {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
  margin-left: 12rpx;
}

.badge-hot {
  background: #FFEAEA;
  color: #FF4757;
}

.course-teacher {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 12rpx;
}

.teacher-name {
  font-size: 24rpx;
  color: #636E72;
}

.course-dot {
  font-size: 20rpx;
  color: #B2BEC3;
}

.room-name-text {
  font-size: 22rpx;
  color: #636E72;
}

.course-stats {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 12rpx;
}

.stats-rating {
  font-size: 24rpx;
  font-weight: 500;
  color: #2D3436;
}

.stats-count {
  font-size: 22rpx;
  color: #B2BEC3;
}

.course-footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: 12rpx;
}

.course-price-wrap {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
}

.course-price {
  font-size: 36rpx;
  font-weight: 700;
  color: #4F6EF7;
}

.course-price-unit {
  font-size: 22rpx;
  color: #B2BEC3;
}

.course-book-btn {
  background: rgba(79, 110, 247, 0.1);
  border-radius: 999rpx;
  padding: 10rpx 24rpx;
}

.book-btn-text {
  font-size: 24rpx;
  color: #4F6EF7;
  font-weight: 500;
}
</style>
