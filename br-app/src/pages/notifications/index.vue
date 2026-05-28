<template>
  <view class="page">
    <view :style="{ height: statusBarHeight + 'px' }" class="status-spacer" />

    <view class="nav-bar">
      <view class="nav-back press-effect" @tap="goBack">
        <text class="nav-back-text">‹</text>
      </view>
      <text class="nav-title">消息通知</text>
      <view
        :class="['mark-all', { disabled: !hasUnreadInScope || markAllLoading }]"
        @tap="markAllRead"
      >
        <text class="mark-all-text">{{ markAllLoading ? '处理中' : '全部已读' }}</text>
      </view>
    </view>

    <view class="tabs">
      <view
        v-for="tab in tabs"
        :key="tab.value"
        :class="['tab-item', { active: currentType === tab.value }]"
        @tap="switchType(tab.value)"
      >
        <text class="tab-text">{{ tab.label }}</text>
        <view v-if="currentType === tab.value" class="tab-indicator" />
      </view>
    </view>

    <view v-if="disabledHint" class="disabled-hint">
      <text class="disabled-hint-text">该类通知已关闭，历史消息仍可查看</text>
    </view>

    <scroll-view
      class="content"
      scroll-y
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="refreshList"
      @scrolltolower="loadMore"
    >
      <view v-if="loading && notifications.length === 0" class="loading-state">
        <view v-for="i in 4" :key="i" class="skeleton-card">
          <view class="skeleton-top">
            <view class="skeleton-dot" />
            <view class="skeleton-line short" />
          </view>
          <view class="skeleton-line title" />
          <view class="skeleton-line content-line" />
          <view class="skeleton-line time" />
        </view>
      </view>

      <view v-else-if="loadError" class="state-wrap">
        <view class="state-icon error-icon">
          <text class="state-icon-text">!</text>
        </view>
        <text class="state-title">消息加载失败</text>
        <text class="state-desc">请检查网络后重试</text>
        <view class="retry-btn press-effect" @tap="retryLoad">
          <text class="retry-btn-text">重新加载</text>
        </view>
      </view>

      <view v-else-if="notifications.length === 0" class="state-wrap">
        <view class="state-icon empty-icon">
          <text class="state-icon-text">铃</text>
        </view>
        <text class="state-title">暂无消息</text>
        <text class="state-desc">{{ emptyText }}</text>
      </view>

      <view v-else class="notification-list">
        <view
          v-for="item in notifications"
          :key="item.id"
          :class="['notification-card', { read: item.is_read, pressing: readingId === item.id }]"
          @tap="openNotification(item)"
        >
          <view class="card-header">
            <view class="type-wrap">
              <view :class="['type-icon', typeMeta(item.type).tone]">
                <text class="type-icon-text">{{ typeMeta(item.type).icon }}</text>
              </view>
              <text :class="['type-label', typeMeta(item.type).tone]">{{ typeMeta(item.type).label }}</text>
            </view>
            <view class="right-wrap">
              <text class="time-text">{{ formatTime(item.created_at) }}</text>
              <view v-if="!item.is_read" class="unread-dot" />
            </view>
          </view>

          <text :class="['card-title', { read: item.is_read }]">{{ item.title || '通知消息' }}</text>
          <text :class="['card-content', { read: item.is_read }]">{{ item.content || '暂无消息内容' }}</text>
        </view>

        <view class="load-more">
          <text v-if="loading" class="load-more-text">加载中...</text>
          <text v-else-if="!hasMore" class="load-more-text">没有更多了</text>
        </view>
      </view>

      <view class="bottom-safe" />
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import {
  getNotifications,
  getNotificationPreferences,
  markNotificationRead,
  markAllNotificationsRead,
} from '@/api/notifications'
import { NOTIFICATION_TYPE_CONFIGS, NOTIFICATION_TYPE_MAP, getNotificationPreferenceField } from '@/utils/notificationTypes'

const PAGE_SIZE = 20

const tabs = [
  { value: 'all', label: '全部' },
  ...NOTIFICATION_TYPE_CONFIGS.map((item) => ({
    value: item.key,
    label: item.label,
  })),
]

const systemInfo = uni.getSystemInfoSync()
const statusBarHeight = systemInfo.statusBarHeight || 0

const currentType = ref('all')
const notifications = ref([])
const preferences = ref(null)
const page = ref(1)
const total = ref(0)
const hasMore = ref(true)
const loading = ref(false)
const refreshing = ref(false)
const loadError = ref(false)
const markAllLoading = ref(false)
const readingId = ref(null)
const listRequestId = ref(0)

const hasUnreadInScope = computed(() => notifications.value.some((item) => !item.is_read))

const disabledHint = computed(() => {
  if (currentType.value === 'all' || !preferences.value) return false
  const meta = NOTIFICATION_TYPE_MAP[currentType.value]
  if (!meta) return false
  return preferences.value[getNotificationPreferenceField(meta.key)] === false
})

const emptyText = computed(() => {
  if (currentType.value === 'all') return '还没有收到任何通知'
  const meta = NOTIFICATION_TYPE_MAP[currentType.value]
  return `暂无${meta ? meta.label : '该类'}消息`
})

onLoad(() => {
  loadInitialData()
})

onShow(() => {
  if (preferences.value) {
    loadPreferences()
  }
})

async function loadInitialData() {
  await Promise.all([
    loadPreferences(),
    loadList({ reset: true }),
  ])
}

async function loadPreferences() {
  try {
    preferences.value = await getNotificationPreferences()
  } catch {
    preferences.value = null
  }
}

async function loadList(options = {}) {
  if (loading.value && !options.reset) return
  const requestId = ++listRequestId.value
  if (options.reset) {
    page.value = 1
    total.value = 0
    hasMore.value = true
    notifications.value = []
  }

  loading.value = !options.silent
  loadError.value = false

  try {
    const params = {
      page: page.value,
      page_size: PAGE_SIZE,
    }
    if (currentType.value !== 'all') {
      params.type = currentType.value
    }

    const data = await getNotifications(params)
    if (requestId !== listRequestId.value) return

    const items = Array.isArray(data) ? data : ((data && data.items) || [])
    total.value = Number((data && data.total) || items.length || 0)
    notifications.value = page.value === 1 ? items : notifications.value.concat(items)
    hasMore.value = notifications.value.length < total.value && items.length >= PAGE_SIZE
  } catch {
    if (requestId !== listRequestId.value) return
    if (page.value === 1) {
      notifications.value = []
      loadError.value = true
    } else {
      uni.showToast({ title: '加载更多失败', icon: 'none' })
    }
  } finally {
    if (requestId === listRequestId.value) {
      loading.value = false
      refreshing.value = false
    }
  }
}

function retryLoad() {
  loadInitialData()
}

function refreshList() {
  refreshing.value = true
  Promise.all([
    loadPreferences(),
    loadList({ reset: true, silent: true }),
  ]).finally(() => {
    refreshing.value = false
  })
}

function loadMore() {
  if (loading.value || !hasMore.value || loadError.value) return
  page.value += 1
  loadList()
}

function switchType(type) {
  if (currentType.value === type) return
  currentType.value = type
  loadList({ reset: true })
}

async function markAllRead() {
  if (!hasUnreadInScope.value || markAllLoading.value) return
  markAllLoading.value = true
  try {
    const type = currentType.value === 'all' ? undefined : currentType.value
    await markAllNotificationsRead(type)
    notifications.value = notifications.value.map((item) => ({ ...item, is_read: true }))
    uni.showToast({ title: '已全部标记已读', icon: 'none' })
  } catch {
    uni.showToast({ title: '操作失败，请重试', icon: 'none' })
  } finally {
    markAllLoading.value = false
  }
}

async function openNotification(item) {
  if (!item || readingId.value) return
  readingId.value = item.id
  try {
    await markNotificationRead(item.id)
    notifications.value = notifications.value.map((message) => (
      message.id === item.id ? { ...message, is_read: true } : message
    ))
    navigateToTarget(item)
  } catch {
    uni.showToast({ title: '标记已读失败，请重试', icon: 'none' })
  } finally {
    readingId.value = null
  }
}

function navigateToTarget(item) {
  const url = normalizeTargetUrl(item.target_url || (NOTIFICATION_TYPE_MAP[item.type] && NOTIFICATION_TYPE_MAP[item.type].defaultTarget))
  if (!url) return
  if (isTabPage(url)) {
    uni.switchTab({ url })
  } else {
    uni.navigateTo({ url })
  }
}

function normalizeTargetUrl(url) {
  if (!url) return ''
  return url.startsWith('/') ? url : `/${url}`
}

function isTabPage(url) {
  return [
    '/pages/index/index',
    '/pages/booking/index',
    '/pages/orders/index',
    '/pages/profile/index',
  ].includes(url.split('?')[0])
}

function typeMeta(type) {
  const item = NOTIFICATION_TYPE_MAP[type]
  if (item) {
    return {
      label: item.label,
      icon: item.iconText,
      tone: item.key,
    }
  }
  return {
    label: '通知',
    icon: '通',
    tone: 'default',
  }
}

function formatTime(value) {
  if (!value) return ''
  const date = new Date(String(value).replace(/-/g, '/'))
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 16)

  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff >= 0 && diff < 60 * 1000) return '刚刚'
  if (diff >= 0 && diff < 60 * 60 * 1000) return `${Math.floor(diff / (60 * 1000))}分钟前`
  if (diff >= 0 && diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / (60 * 60 * 1000))}小时前`

  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
  } else {
    uni.switchTab({ url: '/pages/index/index' })
  }
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: #f5f6fa;
  color: #1f2933;
}

.status-spacer {
  background: #ffffff;
}

.nav-bar {
  height: 96rpx;
  padding: 0 28rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-bottom: 1rpx solid #edf0f5;
}

.nav-back {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
}

.nav-back-text {
  font-size: 56rpx;
  line-height: 56rpx;
  color: #263238;
}

.nav-title {
  flex: 1;
  text-align: center;
  font-size: 34rpx;
  font-weight: 700;
  color: #18212f;
}

.mark-all {
  width: 132rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 28rpx;
  background: #eef3ff;
}

.mark-all.disabled {
  opacity: 0.46;
}

.mark-all-text {
  font-size: 24rpx;
  font-weight: 600;
  color: #4f6ef7;
}

.tabs {
  height: 104rpx;
  padding: 0 20rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  background: #ffffff;
  overflow: hidden;
}

.tab-item {
  position: relative;
  min-width: 118rpx;
  height: 68rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 34rpx;
  background: #f4f6fb;
}

.tab-item.active {
  background: #edf2ff;
}

.tab-text {
  font-size: 24rpx;
  font-weight: 600;
  color: #667085;
}

.tab-item.active .tab-text {
  color: #4f6ef7;
}

.tab-indicator {
  position: absolute;
  bottom: 8rpx;
  width: 28rpx;
  height: 4rpx;
  border-radius: 4rpx;
  background: #4f6ef7;
}

.disabled-hint {
  margin: 20rpx 24rpx 0;
  padding: 18rpx 22rpx;
  border-radius: 16rpx;
  background: #fff7e8;
  border: 1rpx solid #ffe1ad;
}

.disabled-hint-text {
  font-size: 24rpx;
  color: #ad6800;
}

.content {
  height: calc(100vh - 200rpx);
}

.disabled-hint + .content {
  height: calc(100vh - 292rpx);
}

.notification-list,
.loading-state {
  padding: 24rpx;
}

.notification-card,
.skeleton-card {
  margin-bottom: 20rpx;
  padding: 26rpx;
  border-radius: 18rpx;
  background: #ffffff;
  box-shadow: 0 12rpx 32rpx rgba(31, 41, 55, 0.06);
}

.notification-card.read {
  box-shadow: none;
  background: #fbfcff;
}

.notification-card.pressing {
  opacity: 0.72;
}

.card-header,
.type-wrap,
.right-wrap,
.skeleton-top {
  display: flex;
  align-items: center;
}

.card-header {
  justify-content: space-between;
  margin-bottom: 18rpx;
}

.type-wrap {
  gap: 12rpx;
}

.type-icon {
  width: 42rpx;
  height: 42rpx;
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.type-icon-text {
  font-size: 22rpx;
  font-weight: 700;
}

.type-label {
  font-size: 23rpx;
  font-weight: 700;
}

.booking {
  color: #4f6ef7;
  background: #edf2ff;
}

.activity {
  color: #9b51e0;
  background: #f3e8ff;
}

.report {
  color: #0e9f6e;
  background: #e7f8f0;
}

.arrival {
  color: #f59e0b;
  background: #fff7e6;
}

.default {
  color: #667085;
  background: #eef2f7;
}

.right-wrap {
  gap: 12rpx;
}

.time-text {
  font-size: 22rpx;
  color: #98a2b3;
}

.unread-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #ff4d4f;
}

.card-title {
  display: block;
  margin-bottom: 12rpx;
  font-size: 31rpx;
  line-height: 42rpx;
  font-weight: 700;
  color: #1f2933;
}

.card-title.read {
  color: #667085;
}

.card-content {
  display: block;
  font-size: 26rpx;
  line-height: 38rpx;
  color: #4b5563;
}

.card-content.read {
  color: #98a2b3;
}

.state-wrap {
  min-height: 620rpx;
  padding: 80rpx 48rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.state-icon {
  width: 108rpx;
  height: 108rpx;
  margin-bottom: 28rpx;
  border-radius: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-icon {
  background: #eef3ff;
}

.error-icon {
  background: #fff1f0;
}

.state-icon-text {
  font-size: 44rpx;
  font-weight: 700;
  color: #4f6ef7;
}

.error-icon .state-icon-text {
  color: #ff4d4f;
}

.state-title {
  margin-bottom: 10rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: #263238;
}

.state-desc {
  margin-bottom: 28rpx;
  font-size: 25rpx;
  color: #8a94a6;
}

.retry-btn {
  height: 68rpx;
  padding: 0 34rpx;
  border-radius: 34rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #4f6ef7;
}

.retry-btn-text {
  font-size: 26rpx;
  font-weight: 700;
  color: #ffffff;
}

.skeleton-card {
  overflow: hidden;
}

.skeleton-top {
  gap: 14rpx;
  margin-bottom: 24rpx;
}

.skeleton-dot,
.skeleton-line {
  border-radius: 999rpx;
  background: linear-gradient(90deg, #eef1f6 25%, #f7f8fb 37%, #eef1f6 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
}

.skeleton-dot {
  width: 42rpx;
  height: 42rpx;
}

.skeleton-line {
  height: 24rpx;
}

.skeleton-line.short {
  width: 150rpx;
}

.skeleton-line.title {
  width: 72%;
  height: 34rpx;
  margin-bottom: 18rpx;
}

.skeleton-line.content-line {
  width: 92%;
  height: 28rpx;
  margin-bottom: 20rpx;
}

.skeleton-line.time {
  width: 180rpx;
}

.load-more {
  height: 70rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.load-more-text {
  font-size: 24rpx;
  color: #98a2b3;
}

.bottom-safe {
  height: 40rpx;
}

.press-effect:active {
  opacity: 0.72;
}

@keyframes shimmer {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: 0 0;
  }
}
</style>
