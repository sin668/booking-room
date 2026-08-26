<template>
  <view class="page">
    <!-- Status filter tabs -->
    <view class="tabs">
      <view
        v-for="tab in tabs"
        :key="tab.value"
        :class="['tab-item', { active: currentTab === tab.value }]"
        @tap="onSwitchTab(tab.value)"
      >
        <text class="tab-text">{{ tab.label }}</text>
        <view v-if="currentTab === tab.value" class="tab-indicator" />
      </view>
    </view>

    <!-- Order list -->
    <scroll-view
      class="order-scroll"
      scroll-y
      @scrolltolower="onLoadMore"
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onPullRefresh"
    >
      <!-- Loading skeleton -->
      <view v-if="loading && orders.length === 0" class="loading-state">
        <view v-for="i in 3" :key="i" class="skeleton-card">
          <view class="skeleton-row skeleton-row-header" />
          <view class="skeleton-divider" />
          <view class="skeleton-row" />
          <view class="skeleton-row" />
          <view class="skeleton-row skeleton-row-short" />
        </view>
      </view>

      <!-- Empty state -->
      <view v-else-if="!loading && orders.length === 0" class="empty-state">
        <view class="empty-icon">
          <view class="empty-icon-body" />
          <view class="empty-icon-line" />
          <view class="empty-icon-line short" />
        </view>
        <text class="empty-text">暂无预约记录</text>
        <view class="empty-btn" @tap="goBooking">
          <text class="empty-btn-text">去预约</text>
        </view>
      </view>

      <!-- Order cards -->
      <view v-else class="order-list">
        <view
          v-for="(order, index) in orders"
          :key="order.id"
          :class="['order-card', `status-${order.status}`, `card-enter-${index % 5}`]"
        >
          <!-- Top row: title + status badge -->
          <view class="card-header">
            <view class="store-title-wrap">
              <view :class="['status-dot', `dot-${displayStatus(order)}`]" />
              <text v-if="isCourseBooking(order)" class="store-name">{{ order.course_name || '课程预约' }}</text>
              <text v-else class="store-name">{{ order.room ? order.room.name : '未知门店' }}</text>
            </view>
            <view :class="['status-badge', `badge-${displayStatus(order)}`]">
              <text class="status-badge-text">{{ statusLabel(order) }}</text>
            </view>
          </view>

          <!-- Dashed divider -->
          <view class="dashed-divider">
            <view class="dash" v-for="i in 20" :key="i" />
          </view>

          <!-- Seat info (seat booking) -->
          <template v-if="!isCourseBooking(order)">
            <view class="card-info-row">
              <view class="info-icon seat-icon">
                <view class="seat-icon-shape" />
              </view>
              <text class="info-text">{{ seatInfoText(order) }}</text>
            </view>

            <!-- Time -->
            <view class="card-info-row">
              <view class="info-icon clock-icon">
                <view class="clock-icon-circle" />
                <view class="clock-icon-hand" />
              </view>
              <text class="info-text">{{ order.date }} {{ order.start_time }} - {{ order.end_time }}</text>
            </view>
          </template>

          <!-- Course info (course booking) -->
          <template v-else>
            <!-- Teacher row -->
            <view class="card-info-row">
              <view class="info-icon teacher-icon">
                <image
                  v-if="order.teacher_avatar"
                  class="teacher-avatar-img"
                  :src="order.teacher_avatar"
                  mode="aspectFill"
                />
                <view v-else class="teacher-avatar-placeholder">
                  <view class="icon icon-user teacher-avatar-icon" />
                </view>
              </view>
              <text class="info-text">{{ order.teacher_name ? order.teacher_name + ' 老师' : '待分配老师' }}</text>
            </view>
            <!-- Start date row (only for pending start) -->
            <view v-if="isOrderPendingStart(order) && startDateText(order)" class="card-info-row">
              <view class="info-icon start-icon">
                <view class="start-icon-dot" />
              </view>
              <text class="info-text">{{ startDateText(order) }}</text>
            </view>
            <!-- End date row (only for completed) -->
            <view v-if="order.status === 'completed' && endDateText(order)" class="card-info-row">
              <view class="info-icon start-icon">
                <view class="start-icon-dot" />
              </view>
              <text class="info-text">{{ endDateText(order) }}</text>
            </view>
            <!-- Schedule row (not for completed) -->
            <view v-if="order.status !== 'completed' && scheduleText(order)" class="card-info-row">
              <view class="info-icon lesson-icon">
                <view class="lesson-icon-dot" />
              </view>
              <text :class="['info-text', 'schedule-text', { expanded: isScheduleExpanded(order) }]" @tap.stop="toggleSchedule(order)">{{ scheduleText(order) }}</text>
            </view>
            <!-- Room row -->
            <view class="card-info-row">
              <view class="info-icon location-icon">
                <view class="icon icon-location location-icon-shape" />
              </view>
              <text class="info-text">{{ order.room ? order.room.name : '未知培训室' }}</text>
            </view>
            <!-- Lesson row: nearest lesson + expandable list (pending/in_progress) -->
            <template v-if="order.status !== 'completed' && order.lesson_schedules && order.lesson_schedules.length">
              <view class="card-info-row lesson-highlight-row" @tap.stop="toggleLessons(order)">
                <view class="info-icon lesson-icon">
                  <view class="lesson-icon-dot lesson-icon-dot-active" />
                </view>
                <text class="lesson-highlight-text">第{{ getNearestLesson(order).sort_order || '?' }}讲：{{ getNearestLesson(order).lesson_title }}   {{ getNearestLesson(order).lesson_date }} {{ formatLessonStartTime(getNearestLesson(order).lesson_time_slot) }}上课</text>
              </view>
              <view v-if="isLessonsExpanded(order)" class="lesson-expand-list">
                <view v-for="ls in order.lesson_schedules" :key="ls.id" class="lesson-expand-item">
                  <view class="lesson-expand-dot" />
                  <text class="lesson-expand-text">第{{ ls.sort_order }}讲：{{ ls.lesson_title }}   {{ ls.lesson_date }} {{ formatLessonStartTime(ls.lesson_time_slot) }}</text>
                </view>
              </view>
            </template>
            <!-- Lesson titles (fallback for completed or no lesson_schedules) -->
            <view v-if="order.status === 'completed' && order.lesson_titles && order.lesson_titles.length" class="card-info-row">
              <view class="info-icon lesson-icon">
                <view class="lesson-icon-dot" />
              </view>
              <text class="info-text lesson-titles">{{ order.lesson_titles.join('、') }}</text>
            </view>
          </template>

          <!-- Duration + Price -->
          <view class="card-bottom-row">
            <text v-if="!isCourseBooking(order)" class="duration-text">{{ calcHours(order) }}小时</text>
            <text v-else class="duration-text">{{ (order.lesson_titles || []).length }}课时</text>
            <text class="price-text">
              <text class="price-symbol">¥</text>{{ order.total_price || '0.00' }}
            </text>
          </view>

          <!-- Action row -->
          <view class="card-action-row">
            <view
              v-if="order.payment_status === 'pending' && order.status !== 'cancelled'"
              class="action-btn pay-action-btn"
              @tap="goPay(order)"
            >
              <text class="action-btn-text pay-action-text">去支付</text>
            </view>
            <view
              v-if="order.payment_status === 'pending' && order.status !== 'cancelled'"
              :class="['action-btn', 'cancel-action-btn', { disabled: cancellingOrderId === order.id }]"
              @tap.stop="confirmCancelBooking(order)"
            >
              <text class="action-btn-text cancel-action-text">
                {{ cancellingOrderId === order.id ? '取消中' : '取消' }}
              </text>
            </view>
            <view
              v-if="order.status === 'confirmed' && order.payment_status !== 'pending' && !isCourseBooking(order)"
              class="action-btn"
              @tap="viewSeat(order)"
            >
              <text class="action-btn-text">查看座位</text>
            </view>
            <view
              v-if="(order.status === 'confirmed' || order.status === 'in_progress') && order.payment_status !== 'pending' && isCourseBooking(order)"
              class="action-btn"
              @tap="viewCourse(order)"
            >
              <text class="action-btn-text">查看课程</text>
            </view>
            <view
              v-if="order.can_cancel === true && order.payment_status !== 'pending'"
              :class="['action-btn', 'cancel-action-btn', { disabled: cancellingOrderId === order.id }]"
              @tap.stop="confirmCancelBooking(order)"
            >
              <text class="action-btn-text cancel-action-text">
                {{ cancellingOrderId === order.id ? '取消中' : '取消' }}
              </text>
            </view>
            <view
              v-if="order.status === 'completed'"
              class="action-btn"
              @tap="rebook(order)"
            >
              <text class="action-btn-text">再来一单</text>
            </view>
            <view
              v-if="order.status === 'cancelled'"
              class="action-btn"
              @tap="rebook(order)"
            >
              <text class="action-btn-text">重新预约</text>
            </view>
          </view>
        </view>

        <!-- Load more indicator -->
        <view class="load-more">
          <text v-if="loading" class="load-more-text">加载中...</text>
          <text v-else-if="!hasMore" class="load-more-text">没有更多了</text>
        </view>
      </view>

      <!-- Bottom spacing for tab bar -->
      <view style="height: 120rpx;" />
    </scroll-view>
  </view>
</template>

<script>
import { cancelBookingOrder, fetchBookingsPage } from '@/services/bookingPageService'
import { cancelCourseBooking } from '@/api/courseBooking'
import { BOOKING_TABS, SEAT_ZONE_LABELS } from '@/constants/booking'
import { formatBookingStatus, formatCourseEndDate, formatCourseSchedule, formatCourseStartDate, formatHourCount, formatMoney } from '@/utils/formatters'

const TABS = [
  { label: '全部', value: 'all' },
  { label: '已确认', value: 'confirmed' },
  { label: '已取消', value: 'cancelled' },
  { label: '已完成', value: 'completed' },
]

const STATUS_MAP = {
  pending: '待确认',
  confirmed: '已确认',
  cancelled: '已取消',
  completed: '已完成',
}

const ZONE_MAP = {
  quiet: '静音区',
  keyboard: '键盘区',
  vip: 'VIP区',
}

const PAGE_SIZE = 20
const SCHEDULE_TRUNCATE_THRESHOLD = 12

export default {
  data() {
    return {
      tabs: BOOKING_TABS,
      currentTab: 'all',
      orders: [],
      page: 1,
      total: 0,
      loading: false,
      refreshing: false,
      hasMore: true,
      cancellingOrderId: null,
      expandedScheduleIds: {},
      expandedLessons: {},
    }
  },

  onShow() {
    this.resetAndLoad()
  },

  methods: {
    scheduleText(order) {
      return formatCourseSchedule(order?.schedule)
    },

    startDateText(order) {
      return formatCourseStartDate(order?.start_date)
    },

    isScheduleExpanded(order) {
      return Boolean(this.expandedScheduleIds[order?.id])
    },

    toggleSchedule(order) {
      const text = formatCourseSchedule(order?.schedule)
      if (!text || text.length <= SCHEDULE_TRUNCATE_THRESHOLD) return
      this.expandedScheduleIds[order.id] = !this.expandedScheduleIds[order.id]
    },

    isOrderStarted(order) {
      return order.status === 'in_progress' || (order.status === 'confirmed' && order.started === true)
    },

    isOrderPendingStart(order) {
      return order.status === 'confirmed' && !order.started
    },

    endDateText(order) {
      return formatCourseEndDate(order?.end_date)
    },

    getTodayStr() {
      const d = new Date()
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${y}-${m}-${day}`
    },

    getNearestLesson(order) {
      const schedules = order?.lesson_schedules
      if (!schedules || !schedules.length) return null
      const todayStr = this.getTodayStr()
      return schedules.find(s => s.lesson_date >= todayStr) || schedules[schedules.length - 1]
    },

    formatLessonStartTime(timeSlot) {
      if (!timeSlot || typeof timeSlot !== 'string') return ''
      return timeSlot.split('-')[0] || ''
    },

    isLessonsExpanded(order) {
      return Boolean(this.expandedLessons[order?.id])
    },

    toggleLessons(order) {
      this.expandedLessons[order.id] = !this.expandedLessons[order.id]
    },

    async resetAndLoad() {
      this.page = 1
      this.orders = []
      this.hasMore = true
      await this.loadOrders()
    },

    async loadOrders() {
      if (this.loading) return
      this.loading = true
      try {
        const params = { page: this.page, page_size: PAGE_SIZE }
        if (this.currentTab !== 'all') {
          params.status = this.currentTab
        }
        const data = await fetchBookingsPage(params)
        const items = data.items || []
        if (this.page === 1) {
          this.orders = items
        } else {
          this.orders = this.orders.concat(items)
        }
        this.total = data.total || 0
        this.hasMore = this.orders.length < this.total
      } catch {
        if (this.page === 1) this.orders = []
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },

    onSwitchTab(value) {
      if (this.currentTab === value) return
      this.currentTab = value
      this.resetAndLoad()
    },

    onPullRefresh() {
      this.refreshing = true
      this.resetAndLoad()
    },

    onLoadMore() {
      if (!this.hasMore || this.loading) return
      this.page++
      this.loadOrders()
    },

    displayStatus(order) {
      if (!order) return order?.status || ''
      if (order.status === 'confirmed' && order.booking_type === 'course' && order.started === true) {
        return 'in_progress'
      }
      return order.status
    },

    statusLabel(order) {
      if (!order) return ''
      return formatBookingStatus(this.displayStatus(order))
    },

    isCourseBooking(order) {
      return order.booking_type === 'course'
    },

    courseInfoText(order) {
      const count = (order.lesson_titles || []).length
      return count ? `${count}课时` : '课程预约'
    },

    seatInfoText(order) {
      if (!order.seat) return '暂无座位信息'
      const seat = order.seat
      const zone = SEAT_ZONE_LABELS[seat.zone] || seat.zone || ''
      return zone ? `${seat.seat_number}号座位 · ${zone}` : `${seat.seat_number}号座位`
    },

    calcHours(order) {
      return formatHourCount(order.start_time, order.end_time)
    },

    goPay(order) {
      uni.navigateTo({
        url: `/pages/booking/confirm?booking_id=${order.id}&room_id=${order.room_id}&seat_id=${order.seat_id}&date=${order.date}&start_time=${order.start_time}&end_time=${order.end_time}`,
      })
    },

    viewSeat(order) {
      if (!order.room_id || !order.seat_id) return
      uni.navigateTo({
        url: `/pages/booking/seat-select?room_id=${order.room_id}&seat_id=${order.seat_id}&date=${order.date}&start_time=${order.start_time}&end_time=${order.end_time}&mode=view`,
      })
    },

    confirmCancelBooking(order) {
      if (!order || this.cancellingOrderId === order.id) return
      const penaltyValue = order.cancel_penalty_amount !== undefined
        ? order.cancel_penalty_amount
        : order.penalty_amount
      const penaltyAmount = Number(penaltyValue || 0)
      const content = penaltyAmount > 0
        ? `取消后将扣款¥${this.formatMoney(penaltyValue)}，剩余退款将退回钱包，是否继续？`
        : '取消后退款将退回钱包，是否继续？'
      uni.showModal({
        title: '取消预约',
        content,
        confirmText: '取消预约',
        confirmColor: '#FF6B6B',
        success: (res) => {
          if (res.confirm) {
            this.handleCancelBooking(order)
          }
        },
      })
    },

    async handleCancelBooking(order) {
      if (!order || this.cancellingOrderId === order.id) return
      this.cancellingOrderId = order.id
      try {
        const result = order.booking_type === 'course'
          ? await cancelCourseBooking(order.id)
          : await cancelBookingOrder(order.id)
        const refund = result && result.refund_amount ? result.refund_amount : '0.00'
        uni.showToast({
          title: `已取消，退款¥${refund}`,
          icon: 'none',
        })
        await this.resetAndLoad()
      } catch (error) {
        const message = error && (error.detail || error.message)
        if (message && message.includes('已开始')) {
          uni.showToast({ title: '已开始不可取消', icon: 'none' })
          await this.resetAndLoad()
        } else {
          uni.showToast({ title: '取消失败，请重试', icon: 'none' })
        }
      } finally {
        this.cancellingOrderId = null
      }
    },

    formatMoney(value) {
      return formatMoney(value)
    },

    viewCourse(order) {
      if (!order.course_id) return
      uni.navigateTo({
        url: `/pages/training/course-detail?course_id=${order.course_id}`,
      })
    },

    rebook(order) {
      if (order.booking_type === 'course' && order.course_id) {
        uni.navigateTo({
          url: `/pages/training/course-booking?course_id=${order.course_id}`,
        })
        return
      }
      uni.switchTab({ url: '/pages/booking/index' })
    },

    goBooking() {
      uni.switchTab({ url: '/pages/booking/index' })
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(180deg, #fff 0, $bg-warm 180rpx, $bg-color 420rpx);
  display: flex;
  flex-direction: column;
}

/* Tabs */
.tabs {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.96);
  padding: 0 16rpx;
  height: 88rpx;
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 1rpx solid rgba(79, 110, 247, 0.06);
  backdrop-filter: blur(18rpx);
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  position: relative;
}

.tab-text {
  font-size: 28rpx;
  color: $text-secondary;
  transition: color 0.2s;
}

.tab-item.active .tab-text {
  font-weight: 600;
  color: $text-primary;
}

.tab-indicator {
  position: absolute;
  bottom: 8rpx;
  width: 48rpx;
  height: 6rpx;
  border-radius: 3rpx;
  background: $gradient-primary;
}

/* Scroll view */
.order-scroll {
  flex: 1;
  height: calc(100vh - 88rpx);
}

/* Loading skeleton */
.loading-state {
  padding: 24rpx 32rpx;
}

.skeleton-card {
  background: $surface;
  border-radius: 32rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: $shadow-sm;
  border: 1rpx solid $border-soft;
}

.skeleton-row {
  height: 32rpx;
  border-radius: 8rpx;
  background: $bg-color;
  margin-bottom: 16rpx;
  animation: skeleton-pulse 1.2s ease-in-out infinite;
}

.skeleton-row-header {
  width: 60%;
  margin-bottom: 20rpx;
}

.skeleton-row-short {
  width: 40%;
}

.skeleton-divider {
  height: 2rpx;
  border-radius: 1rpx;
  background: $bg-color;
  margin-bottom: 20rpx;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 200rpx;
}

.empty-icon {
  width: 160rpx;
  height: 180rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32rpx;
}

.empty-icon-body {
  width: 120rpx;
  height: 140rpx;
  border-radius: 16rpx;
  background: $bg-color;
  border: 4rpx dashed $text-muted;
}

.empty-icon-line {
  width: 80rpx;
  height: 6rpx;
  border-radius: 3rpx;
  background: $text-muted;
  margin-top: 12rpx;
}

.empty-icon-line.short {
  width: 56rpx;
  margin-top: 8rpx;
}

.empty-text {
  font-size: 28rpx;
  color: $text-muted;
  margin-bottom: 40rpx;
}

.empty-btn {
  height: 72rpx;
  padding: 0 48rpx;
  border-radius: 36rpx;
  border: 2rpx solid $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $surface;
  box-shadow: $shadow-sm;
}

.empty-btn:active {
  background: $primary-light;
}

.empty-btn-text {
  font-size: 26rpx;
  color: $primary;
}

/* Order list */
.order-list {
  padding: 24rpx 0;
}

/* Order card */
.order-card {
  position: relative;
  background: $surface;
  border-radius: 32rpx;
  padding: 30rpx;
  margin: 0 32rpx 24rpx;
  box-shadow: $shadow-card;
  overflow: hidden;
  border: 1rpx solid $border-soft;
}

.order-card.status-cancelled {
  opacity: 0.65;
}

/* Card entrance animation */
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

.order-card.card-enter-0 { animation: fadeInUp 0.4s ease-out 0s both; }
.order-card.card-enter-1 { animation: fadeInUp 0.4s ease-out 0.06s both; }
.order-card.card-enter-2 { animation: fadeInUp 0.4s ease-out 0.12s both; }
.order-card.card-enter-3 { animation: fadeInUp 0.4s ease-out 0.18s both; }
.order-card.card-enter-4 { animation: fadeInUp 0.4s ease-out 0.24s both; }

/* Card header */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.store-title-wrap {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
}

.status-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-confirmed {
  background: $success;
  box-shadow: 0 0 0 8rpx rgba(7, 193, 96, 0.1);
}

.dot-pending {
  background: #FFB800;
  box-shadow: 0 0 0 8rpx rgba(255, 184, 0, 0.12);
}

.dot-cancelled {
  background: $danger;
  box-shadow: 0 0 0 8rpx rgba(255, 107, 107, 0.1);
}

.dot-completed {
  background: $text-muted;
  box-shadow: 0 0 0 8rpx rgba(99, 110, 114, 0.08);
}

.store-name {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Status badge */
.status-badge {
  padding: 6rpx 20rpx;
  border-radius: 24rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.6);
}

.status-badge-text {
  font-size: 22rpx;
}

.badge-confirmed {
  background: rgba(7, 193, 96, 0.1);
}

.badge-confirmed .status-badge-text {
  color: $success;
}

.badge-pending {
  background: rgba(255, 184, 0, 0.12);
}

.badge-pending .status-badge-text {
  color: #B77900;
}

.badge-cancelled {
  background: rgba(255, 107, 107, 0.1);
}

.badge-cancelled .status-badge-text {
  color: $danger;
}

.badge-completed {
  background: rgba(99, 110, 114, 0.1);
}

.badge-completed .status-badge-text {
  color: $text-secondary;
}

/* Dashed divider */
.dashed-divider {
  display: flex;
  justify-content: space-between;
  padding: 20rpx 0;
}

.dash {
  flex: 1;
  height: 2rpx;
  border-top: 2rpx dashed $border-color;
  margin-right: 4rpx;
}

.dash:last-child {
  margin-right: 0;
}

/* Info row */
.card-info-row {
  display: flex;
  align-items: center;
  margin-bottom: 14rpx;
}

.info-icon {
  width: 36rpx;
  height: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 14rpx;
  flex-shrink: 0;
}

/* Seat icon (simplified couch shape) */
.seat-icon-shape {
  width: 28rpx;
  height: 20rpx;
  border-radius: 6rpx;
  background: $text-muted;
  position: relative;

  &::before,
  &::after {
    content: '';
    position: absolute;
    bottom: -6rpx;
    width: 8rpx;
    height: 6rpx;
    border-radius: 0 0 4rpx 4rpx;
    background: $text-muted;
  }

  &::before { left: 2rpx; }
  &::after { right: 2rpx; }
}

/* Course icon */
.course-icon {
  background: $primary-light;
  border-radius: 8rpx;
}

.course-icon-text {
  font-size: 22rpx;
  font-weight: 700;
  color: $primary;
}

/* Teacher icon */
.teacher-icon {
  background: $primary-light;
  border-radius: 50%;
}

.teacher-avatar-img {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
}

.teacher-avatar-placeholder {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  background: rgba(79, 110, 247, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.teacher-avatar-icon {
  font-size: 18rpx;
  color: $primary;
}

/* Location icon */
.location-icon {
  background: transparent;
}

.location-icon-shape {
  font-size: 28rpx;
  color: $text-muted;
}

/* Lesson icon */
.lesson-icon-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: $primary;
}

.lesson-titles {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Clock icon */
.clock-icon-circle {
  width: 28rpx;
  height: 28rpx;
  border-radius: 50%;
  border: 3rpx solid $text-muted;
}

.clock-icon-hand {
  position: absolute;
  width: 3rpx;
  height: 10rpx;
  background: $text-muted;
  border-radius: 2rpx;
  bottom: 50%;
  left: 50%;
  transform-origin: bottom center;
  transform: translateX(-50%) rotate(-30deg);
}

.info-text {
  font-size: 26rpx;
  color: $text-secondary;
}

.schedule-text {
  max-width: 420rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.schedule-text.expanded {
  white-space: normal;
  overflow: visible;
}

.start-icon-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 3rpx;
  background: $text-muted;
}

/* Lesson highlight row (nearest lesson) */
.lesson-icon-dot-active {
  background: $success;
}

.lesson-highlight-row {
  background: rgba(7, 193, 96, 0.06);
  border-radius: 12rpx;
  padding: 10rpx 14rpx;
  margin-bottom: 14rpx;
}

.lesson-highlight-text {
  font-size: 26rpx;
  font-weight: 500;
  color: $success;
}

/* Lesson expand list */
.lesson-expand-list {
  padding: 8rpx 0 8rpx 50rpx;
  margin-bottom: 14rpx;
}

.lesson-expand-item {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 8rpx 0;
}

.lesson-expand-dot {
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: $text-muted;
  flex-shrink: 0;
}

.lesson-expand-text {
  font-size: 24rpx;
  color: $text-secondary;
}

/* In-progress status dot & badge */
.dot-in_progress {
  background: $primary;
  box-shadow: 0 0 0 8rpx rgba(79, 110, 247, 0.1);
}

.badge-in_progress {
  background: $primary-light;
}

.badge-in_progress .status-badge-text {
  color: $primary;
}

/* Bottom row: duration + price */
.card-bottom-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10rpx;
}

.duration-text {
  font-size: 24rpx;
  color: $text-muted;
}

.price-text {
  font-size: 32rpx;
  font-weight: 600;
  color: $primary;
}

.price-symbol {
  font-size: 22rpx;
}

/* Action row */
.card-action-row {
  display: flex;
  justify-content: flex-end;
  gap: 16rpx;
  padding-top: 20rpx;
  border-top: 2rpx solid $bg-color;
  margin-top: 16rpx;
}

.action-btn {
  height: 56rpx;
  padding: 0 32rpx;
  border-radius: 28rpx;
  border: 2rpx solid $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $surface;
  box-shadow: 0 4rpx 10rpx rgba(79, 110, 247, 0.06);
}

.action-btn:active {
  background: $primary-light;
}

.action-btn.disabled {
  opacity: 0.55;
}

.action-btn-text {
  font-size: 24rpx;
  color: $primary;
}

.pay-action-btn {
  border: none;
  background: $gradient-primary;
}

.pay-action-btn:active {
  opacity: 0.85;
}

.pay-action-text {
  color: #fff;
}

.cancel-action-btn {
  border-color: $danger;
}

.cancel-action-btn:active {
  background: rgba(255, 107, 107, 0.08);
}

.cancel-action-text {
  color: $danger;
}

/* Load more */
.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 0;
}

.load-more-text {
  font-size: 24rpx;
  color: $text-muted;
}
</style>
