<template>
  <view class="page">
    <view class="search-header">
      <view class="search-back" @tap="goBack">
        <view class="icon icon-arrow-right back-icon" />
      </view>
      <view class="search-input-wrap">
        <view class="icon icon-search search-icon" />
        <input
          class="search-input"
          v-model="keyword"
          placeholder="搜索自习室、培训室、课程、老师"
          placeholder-class="search-placeholder"
          confirm-type="search"
          focus
          @confirm="doSearch"
          @input="onInput"
        />
        <view v-if="keyword" class="search-clear" @tap="clearSearch">
          <text class="clear-text">×</text>
        </view>
      </view>
    </view>

    <scroll-view class="content" scroll-y>
      <view v-if="searching" class="loading-state">
        <text class="loading-text">搜索中...</text>
      </view>

      <view v-else-if="hasSearched && !hasResults" class="empty-state">
        <view class="icon icon-search empty-icon" />
        <text class="empty-title">未找到相关结果</text>
        <text class="empty-subtitle">换个关键词试试</text>
      </view>

      <template v-else-if="hasResults">
        <view v-if="results.rooms.length > 0" class="section">
          <view class="section-header">
            <text class="section-title">自习室 / 培训室</text>
            <text class="section-count">{{ results.rooms.length }} 个结果</text>
          </view>
          <view class="room-list">
            <view
              v-for="room in results.rooms"
              :key="'r-' + room.id"
              class="room-card"
              @tap="goRoomDetail(room)"
            >
              <image
                v-if="room.cover_image"
                class="room-cover"
                :src="room.cover_image"
                mode="aspectFill"
              />
              <view v-else class="room-cover-ph">
                <view class="icon icon-location room-ph-icon" />
              </view>
              <view class="room-info">
                <text class="room-name">{{ room.name }}</text>
                <text class="room-address">{{ room.address || '地址待完善' }}</text>
                <view class="room-meta">
                  <text class="room-type-tag">{{ roomTypeLabel(room.room_type) }}</text>
                  <text v-if="room.min_price" class="room-price">¥{{ room.min_price }}起</text>
                </view>
              </view>
              <view class="icon icon-arrow-right room-arrow" />
            </view>
          </view>
        </view>

        <view v-if="results.courses.length > 0" class="section">
          <view class="section-header">
            <text class="section-title">课程</text>
            <text class="section-count">{{ results.courses.length }} 个结果</text>
          </view>
          <view class="course-list">
            <view
              v-for="course in results.courses"
              :key="'c-' + course.id"
              class="course-card"
              @tap="goCourseDetail(course)"
            >
              <image
                v-if="course.cover_image"
                class="course-cover"
                :src="course.cover_image"
                mode="aspectFill"
              />
              <view v-else class="course-cover-ph">
                <view class="icon icon-book course-ph-icon" />
              </view>
              <view class="course-info">
                <text class="course-name">{{ course.name }}</text>
                <view class="course-detail-row">
                  <text v-if="course.teacher_name" class="course-teacher">{{ course.teacher_name }} 老师</text>
                  <text v-if="course.room_name" class="course-room">{{ course.room_name }}</text>
                </view>
                <text v-if="course.price" class="course-price">¥{{ course.price }}/课时</text>
              </view>
              <view class="icon icon-arrow-right course-arrow" />
            </view>
          </view>
        </view>

        <view v-if="results.teachers.length > 0" class="section">
          <view class="section-header">
            <text class="section-title">老师</text>
            <text class="section-count">{{ results.teachers.length }} 个结果</text>
          </view>
          <view class="teacher-list">
            <view
              v-for="teacher in results.teachers"
              :key="'t-' + teacher.id"
              class="teacher-card"
              @tap="goTeacherDetail(teacher)"
            >
              <image
                v-if="teacher.avatar"
                class="teacher-avatar"
                :src="teacher.avatar"
                mode="aspectFill"
              />
              <view v-else class="teacher-avatar-ph">
                <view class="icon icon-user teacher-ph-icon" />
              </view>
              <view class="teacher-info">
                <text class="teacher-name">{{ teacher.name }}</text>
                <text v-if="teacher.title" class="teacher-title">{{ teacher.title }}</text>
                <text v-if="teacher.specialty" class="teacher-specialty">{{ teacher.specialty }}</text>
              </view>
              <view class="icon icon-arrow-right teacher-arrow" />
            </view>
          </view>
        </view>
      </template>

      <view v-else class="hint-state">
        <view class="icon icon-search hint-icon" />
        <text class="hint-title">输入关键词开始搜索</text>
        <text class="hint-subtitle">支持搜索自习室、培训室、课程、老师</text>
      </view>

      <view style="height: 120rpx;" />
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { searchAll } from '@/api/search'
import { useCityStore } from '@/store/modules/city'

const keyword = ref('')
const results = ref({ rooms: [], courses: [], teachers: [] })
const searching = ref(false)
const hasSearched = ref(false)
let searchTimer = null

const cityStore = useCityStore()

const hasResults = computed(() => {
  return results.value.rooms.length > 0
    || results.value.courses.length > 0
    || results.value.teachers.length > 0
})

function roomTypeLabel(type) {
  const map = { study: '自习室', training: '培训室', comprehensive: '综合室' }
  return map[type] || '自习室'
}

function onInput() {
  clearTimeout(searchTimer)
  if (!keyword.value.trim()) {
    results.value = { rooms: [], courses: [], teachers: [] }
    hasSearched.value = false
    return
  }
  searchTimer = setTimeout(() => {
    doSearch()
  }, 400)
}

async function doSearch() {
  const q = keyword.value.trim()
  if (!q) return
  searching.value = true
  hasSearched.value = true
  try {
    const params = { q }
    if (cityStore.currentCity?.id) {
      params.city_id = cityStore.currentCity.id
    }
    const data = await searchAll(params)
    results.value = {
      rooms: data.rooms || [],
      courses: data.courses || [],
      teachers: data.teachers || [],
    }
  } catch {
    results.value = { rooms: [], courses: [], teachers: [] }
  } finally {
    searching.value = false
  }
}

function clearSearch() {
  keyword.value = ''
  results.value = { rooms: [], courses: [], teachers: [] }
  hasSearched.value = false
}

function goBack() {
  uni.navigateBack()
}

function goRoomDetail(room) {
  uni.navigateTo({ url: `/pages/booking/detail?room_id=${room.id}` })
}

function goCourseDetail(course) {
  uni.navigateTo({ url: `/pages/training/course-detail?course_id=${course.id}` })
}

function goTeacherDetail(teacher) {
  uni.navigateTo({ url: `/pages/teacher/profile?teacher_id=${teacher.id}` })
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
}

.search-header {
  display: flex;
  align-items: center;
  padding: 16rpx 28rpx;
  background: $surface;
  box-shadow: 0 1rpx 0 rgba(0, 0, 0, 0.03);
}

.search-back {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.back-icon {
  font-size: 32rpx;
  color: $text-primary;
  transform: rotate(180deg);
}

.search-input-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  height: 72rpx;
  padding: 0 24rpx;
  background: $bg-color;
  border-radius: 36rpx;
  border: 1rpx solid $border-soft;
}

.search-icon {
  font-size: 28rpx;
  color: $text-muted;
  margin-right: 12rpx;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  font-size: 28rpx;
  color: $text-primary;
  min-width: 0;
}

.search-placeholder {
  color: $text-muted;
}

.search-clear {
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.08);
  margin-left: 12rpx;
  flex-shrink: 0;
}

.clear-text {
  font-size: 28rpx;
  color: $text-secondary;
  line-height: 1;
}

.content {
  height: calc(100vh - 104rpx - var(--status-bar-height, 44px));
}

.loading-state,
.empty-state,
.hint-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 0;
}

.loading-text {
  font-size: 28rpx;
  color: $text-muted;
}

.empty-icon,
.hint-icon {
  font-size: 80rpx;
  color: #ccd2dc;
}

.empty-title,
.hint-title {
  margin-top: 24rpx;
  font-size: 30rpx;
  font-weight: 600;
  color: $text-secondary;
}

.empty-subtitle,
.hint-subtitle {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: $text-muted;
}

.section {
  margin-top: 24rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28rpx 16rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
}

.section-count {
  font-size: 22rpx;
  color: $text-muted;
}

.room-list,
.course-list,
.teacher-list {
  padding: 0 28rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.room-card,
.course-card,
.teacher-card {
  display: flex;
  align-items: center;
  padding: 20rpx;
  background: $surface;
  border-radius: 20rpx;
  box-shadow: $shadow-sm;
  border: 1rpx solid $border-soft;
  transition: transform 0.15s;
}

.room-card:active,
.course-card:active,
.teacher-card:active {
  transform: scale(0.98);
}

.room-cover,
.course-cover {
  width: 120rpx;
  height: 120rpx;
  border-radius: 14rpx;
  flex-shrink: 0;
}

.room-cover-ph,
.course-cover-ph {
  width: 120rpx;
  height: 120rpx;
  border-radius: 14rpx;
  flex-shrink: 0;
  background: $primary-soft;
  display: flex;
  align-items: center;
  justify-content: center;
}

.room-ph-icon {
  font-size: 40rpx;
  color: $primary;
}

.course-ph-icon {
  font-size: 40rpx;
  color: $primary;
}

.room-info,
.course-info,
.teacher-info {
  flex: 1;
  min-width: 0;
  margin-left: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.room-name,
.course-name,
.teacher-name {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-address {
  font-size: 24rpx;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.room-meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 4rpx;
}

.room-type-tag {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  background: $primary-soft;
  color: $primary;
  border-radius: 12rpx;
  font-weight: 500;
}

.room-price,
.course-price {
  font-size: 26rpx;
  font-weight: 700;
  color: $danger;
}

.course-detail-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.course-teacher,
.course-room {
  font-size: 24rpx;
  color: $text-secondary;
}

.teacher-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.teacher-avatar-ph {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  flex-shrink: 0;
  background: $primary-soft;
  display: flex;
  align-items: center;
  justify-content: center;
}

.teacher-ph-icon {
  font-size: 36rpx;
  color: $primary;
}

.teacher-title,
.teacher-specialty {
  font-size: 24rpx;
  color: $text-secondary;
}

.room-arrow,
.course-arrow,
.teacher-arrow {
  font-size: 24rpx;
  color: $text-muted;
  flex-shrink: 0;
  margin-left: 12rpx;
}
</style>
