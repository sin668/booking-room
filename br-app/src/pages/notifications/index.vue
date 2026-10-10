<template>
  <view class="page">
    <view :style="{ height: statusBarHeight + 'px' }" class="status-spacer" />

    <view class="nav-bar">
      <view class="nav-back press-effect" @tap="goBack">
        <view class="nav-back-arrow" />
      </view>
      <text class="nav-title">消息通知</text>
      <view :class="['mark-all', { disabled: !hasUnreadInScope || markAllLoading }]"
        @tap="markAllRead">
        <!-- <text class="mark-all-text">{{ markAllLoading ? '处理中' : '全部已读' }}</text> -->
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
      <block v-if="isConversationTab">
        <view v-if="conversationLoading" class="conversation-list">
          <view v-for="i in 5" :key="i" class="skeleton-row">
            <view class="skeleton-avatar" />
            <view class="skeleton-lines">
              <view class="skeleton-line title" />
              <view class="skeleton-line content-line" />
            </view>
          </view>
        </view>

        <view v-else-if="conversationError" class="state-wrap">
          <view class="state-icon error-icon">
            <text class="state-icon-text">!</text>
          </view>
          <text class="state-title">会话加载失败</text>
          <text class="state-desc">请检查网络后重试</text>
          <view class="retry-btn press-effect" @tap="loadConversations">
            <text class="retry-btn-text">重新加载</text>
          </view>
        </view>

        <view v-else-if="conversations.length === 0" class="state-wrap">
          <view class="state-icon empty-icon">
            <text class="state-icon-text">聊</text>
          </view>
          <text class="state-title">暂无会话</text>
          <text class="state-desc">在教培供需广场点击「咨询」即可发起聊天</text>
        </view>

        <view v-else class="conversation-list">
          <view
            v-for="item in conversations"
            :key="item.conversationID"
            class="conversation-item press-effect"
            @tap="openConversation(item)"
          >
            <image
              class="conv-avatar"
              :src="item.avatar || defaultAvatarUrl"
              mode="aspectFill"
            />

            <view class="conv-main">
              <view class="conv-line">
                <text class="conv-name">{{ item.name }}</text>
                <text class="conv-time">{{ item.time }}</text>
              </view>
              <view class="conv-line">
                <text class="conv-summary">{{ item.summary }}</text>
                <view v-if="item.unreadCount > 0" class="conv-badge">
                  <text class="conv-badge-text">{{ item.unreadCount > 99 ? '99+' : item.unreadCount }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>
      </block>

      <block v-else>
      <view v-if="showConversationEntry" class="conversation-entry-section">
        <view class="conversation-entry-card">
          <view class="conversation-entry-header" @tap="goConversationTab">
            <view class="type-wrap">
              <view class="type-icon conversation">
                <text class="type-icon-text">话</text>
              </view>
              <text class="type-label conversation">会话</text>
            </view>
            <view class="right-wrap">
              <text class="time-text">{{ conversationEntryTime }}</text>
              <view v-if="conversationSummary.hasUnread" class="unread-dot" />
            </view>
          </view>
          <view
            v-for="item in conversations"
            :key="item.conversationID"
            class="conversation-item press-effect"
            @tap="openConversation(item)"
          >
            <image
              class="conv-entry-avatar"
              :src="item.avatar || defaultAvatarUrl"
              mode="aspectFill"
            />
            <view class="conv-main">
              <view class="conv-line">
                <text class="conv-name">{{ item.name }}</text>
                <text class="conv-time">{{ item.time }}</text>
              </view>
              <view class="conv-line">
                <text class="conv-summary">{{ item.summary }}</text>
                <view v-if="item.unreadCount > 0" class="conv-badge">
                  <text class="conv-badge-text">{{ item.unreadCount > 99 ? '99+' : item.unreadCount }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>

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
      </block>

      <view class="bottom-safe" />
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { StoreName, TUIConversationService, TUIStore } from '@tencentcloud/chat-uikit-engine-lite'
import {
  getNotifications,
  getNotificationPreferences,
  markNotificationRead,
  markAllNotificationsRead,
} from '@/api/notifications'
import { NOTIFICATION_TYPE_CONFIGS, NOTIFICATION_TYPE_MAP, getNotificationPreferenceField } from '@/utils/notificationTypes'
import { isLoggedIn } from '@/utils/auth'
import { ensureIM } from '@/utils/im'

const PAGE_SIZE = 20
const CONVERSATION_TAB = 'conversation'
const defaultAvatarUrl = 'https://web.sdk.qcloud.com/component/TUIKit/assets/avatar_21.png'

const tabs = [
  { value: 'all', label: '全部' },
  { value: CONVERSATION_TAB, label: '会话' },
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
const conversations = ref([])
const conversationLoading = ref(false)
const conversationError = ref(false)

let conversationWatched = false

const isConversationTab = computed(() => currentType.value === CONVERSATION_TAB)

const conversationSummary = computed(() => {
  const list = conversations.value
  if (!list.length) return null
  const latest = list[0]
  return {
    name: latest.name,
    time: latest.time,
    summary: latest.summary,
    hasUnread: list.some((item) => item.unreadCount > 0),
  }
})

const conversationEntryTime = computed(() => {
  const list = conversations.value
  if (!list.length) return ''
  return formatAbsoluteTime(list[0].rawTime)
})

const showConversationEntry = computed(
  () => currentType.value === 'all' && !!conversationSummary.value,
)

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
  if (!requireLogin()) return
  loadInitialData()
})

onShow(() => {
  if (!requireLogin()) return
  if (isConversationTab.value) {
    loadConversations()
    return
  }
  if (currentType.value === 'all') {
    loadConversations()
  }
  if (preferences.value) {
    loadPreferences()
  }
})

onUnmounted(() => {
  if (!conversationWatched) return
  TUIStore.unwatch(StoreName.CONV, { conversationList: onConversationListUpdated })
  conversationWatched = false
})

function requireLogin() {
  if (isLoggedIn()) return true
  uni.showToast({ title: '请先登录', icon: 'none' })
  uni.navigateTo({ url: '/pages/login/login' })
  return false
}

async function loadInitialData() {
  await Promise.all([
    loadPreferences(),
    loadList({ reset: true }),
  ])
  if (currentType.value === 'all') {
    loadConversations()
  }
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
    if (currentType.value !== 'all' && currentType.value !== CONVERSATION_TAB) {
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
  if (isConversationTab.value) {
    loadConversations().finally(() => {
      refreshing.value = false
    })
    return
  }
  if (currentType.value === 'all') {
    loadConversations()
  }
  Promise.all([
    loadPreferences(),
    loadList({ reset: true, silent: true }),
  ]).finally(() => {
    refreshing.value = false
  })
}

function loadMore() {
  if (isConversationTab.value || loading.value || !hasMore.value || loadError.value) return
  page.value += 1
  loadList()
}

function switchType(type) {
  if (currentType.value === type) return
  currentType.value = type
  if (type === CONVERSATION_TAB) {
    loadConversations()
    return
  }
  if (type === 'all') {
    loadConversations()
  }
  loadList({ reset: true })
}

function goConversationTab() {
  switchType(CONVERSATION_TAB)
}

function toConversationRow(conversation) {
  const name = conversation.getShowName() || '会话'
  const lastMsg = conversation.lastMessage || {}
  return {
    conversationID: conversation.conversationID,
    name,
    initial: name.slice(0, 1),
    avatar: conversation.getAvatar() || '',
    summary: conversation.getLastMessage('text') || '',
    time: conversation.getLastMessage('time') || '',
    rawTime: lastMsg.lastTime || lastMsg.time || 0,
    unreadCount: conversation.unreadCount || 0,
  }
}

function onConversationListUpdated(list) {
  conversations.value = (Array.isArray(list) ? list : []).map(toConversationRow)
  conversationLoading.value = false
  conversationError.value = false
}

async function loadConversations() {
  conversationLoading.value = true
  conversationError.value = false

  const ok = await ensureIM()
  if (!ok) {
    conversationLoading.value = false
    conversationError.value = true
    return
  }

  if (!conversationWatched) {
    TUIStore.watch(StoreName.CONV, { conversationList: onConversationListUpdated })
    conversationWatched = true
  }

  try {
    await TUIConversationService.getConversationList()
  } catch {
    conversationError.value = conversations.value.length === 0
  } finally {
    conversationLoading.value = false
  }
}

function openConversation(item) {
  uni.navigateTo({
    url: `/TUIKit/components/TUIChat/index?conversationID=${item.conversationID}`,
  })
}

async function markAllRead() {
  if (isConversationTab.value) return
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
    '/pages/edu-market/index',
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

function formatAbsoluteTime(timestamp) {
  if (!timestamp) return ''
  const ms = timestamp > 1e12 ? timestamp : timestamp * 1000
  const d = new Date(ms)
  if (Number.isNaN(d.getTime())) return ''
  const Y = d.getFullYear()
  const M = String(d.getMonth() + 1).padStart(2, '0')
  const D = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${Y}-${M}-${D} ${h}:${m}`
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
  display: flex;
  align-items: center;
  height: 88rpx;
  padding: 0 28rpx;
  background: #fff;
  position: relative;
}

.nav-back {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-back-arrow {
  width: 20rpx;
  height: 20rpx;
  border-left: 4rpx solid #2D3436;
  border-bottom: 4rpx solid #2D3436;
  transform: rotate(45deg);
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
  /*background: #eef3ff;*/
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
  flex: 1;
  min-width: 0;
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

.conversation-entry-section {
  padding: 24rpx 24rpx 0;
}

.conversation-entry-card {
  margin-bottom: 20rpx;
  border-radius: 18rpx;
  background: #ffffff;
  box-shadow: 0 12rpx 32rpx rgba(31, 41, 55, 0.06);
  overflow: hidden;
}

.conversation-entry-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22rpx 26rpx;
  border-bottom: 1rpx solid #f1f3f7;
}

.conversation-entry-header:active {
  opacity: 0.72;
}

.conversation-entry-card .conversation-item {
  padding: 20rpx 26rpx;
}

.conversation-entry-card .conv-entry-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
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

.conversation {
  color: #07c160;
  background: #e7f8ef;
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

.conversation-list {
  margin: 24rpx;
  border-radius: 18rpx;
  overflow: hidden;
  background: #ffffff;
  box-shadow: 0 12rpx 32rpx rgba(31, 41, 55, 0.06);
}

.conversation-item,
.skeleton-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 26rpx;
}

.conversation-item + .conversation-item,
.skeleton-row + .skeleton-row {
  border-top: 1rpx solid #f1f3f7;
}

.conv-avatar {
  width: 88rpx;
  height: 88rpx;
  flex-shrink: 0;
  border-radius: 24rpx;
  background: #eef2f7;
}

.conv-entry-avatar {
  width: 76rpx;
  height: 76rpx;
  flex-shrink: 0;
  border-radius: 20rpx;
  background: #eef2f7;
}

.conv-main {
  flex: 1;
  min-width: 0;
}

.conv-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.conv-line + .conv-line {
  margin-top: 10rpx;
}

.conv-name {
  flex: 1;
  min-width: 0;
  font-size: 30rpx;
  font-weight: 700;
  color: #1f2933;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.conv-time {
  flex-shrink: 0;
  font-size: 22rpx;
  color: #98a2b3;
}

.conv-summary {
  flex: 1;
  min-width: 0;
  font-size: 26rpx;
  color: #6b7684;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.conv-badge {
  flex-shrink: 0;
  min-width: 34rpx;
  height: 34rpx;
  padding: 0 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 17rpx;
  background: #ff4d4f;
}

.conv-badge-text {
  font-size: 20rpx;
  font-weight: 700;
  color: #ffffff;
}

.skeleton-avatar {
  width: 88rpx;
  height: 88rpx;
  flex-shrink: 0;
  border-radius: 24rpx;
  background: linear-gradient(90deg, #eef1f6 25%, #f7f8fb 37%, #eef1f6 63%);
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
}

.skeleton-lines {
  flex: 1;
  min-width: 0;
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
