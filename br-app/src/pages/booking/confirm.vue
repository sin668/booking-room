<template>
  <view class="page">
    <scroll-view class="content" scroll-y>
      <!-- Loading state -->
      <view v-if="pageLoading" class="loading-wrap">
        <text class="loading-text">加载中...</text>
      </view>

      <template v-else>
        <!-- Order Info Card -->
        <view class="card info-card">
          <!-- Store header -->
          <view class="info-row">
            <view class="icon-wrap store-icon">
              <text class="icon-text">🏢</text>
            </view>
            <view class="info-text-wrap">
              <text class="info-title">{{ roomName }}</text>
              <text class="info-sub">{{ roomAddress }}</text>
            </view>
          </view>

          <view class="divider" />

          <!-- Seat info -->
          <view class="info-row">
            <view class="icon-wrap seat-icon">
              <text class="icon-text">💺</text>
            </view>
            <view class="info-text-wrap">
              <text class="info-title">{{ seatNumber }}号座位</text>
              <text class="info-sub">{{ zoneLabel }} · {{ seatPosition }}</text>
            </view>
          </view>

          <view class="divider" />

          <!-- Date & Time -->
          <view class="time-section">
            <view class="time-row">
              <view class="icon-wrap date-icon">
                <text class="icon-text">📅</text>
              </view>
              <view class="info-text-wrap">
                <text class="info-title">{{ dateLabel }}</text>
                <text class="info-sub">{{ weekdayLabel }}</text>
              </view>
            </view>
            <view class="time-row">
              <view class="icon-wrap clock-icon">
                <text class="icon-text">🕐</text>
              </view>
              <view class="info-text-wrap">
                <text class="info-title">{{ start_time }} - {{ end_time }}</text>
                <view class="hours-badge">
                  <text class="hours-badge-text">{{ hours }}小时</text>
                </view>
              </view>
            </view>
          </view>
        </view>

        <!-- Price Summary Card -->
        <view class="card price-card">
          <view class="price-row">
            <text class="price-label">座位费（{{ zoneLabel }} · {{ hours }}小时）</text>
            <text class="price-value">¥{{ totalPrice }}</text>
          </view>

          <view class="divider" />

          <view class="price-row total-row">
            <text class="total-label">实付金额</text>
            <text class="total-value">
              <text class="total-symbol">¥</text>{{ totalPrice }}
            </text>
          </view>
        </view>

        <!-- Bottom spacing for fixed bar -->
        <view style="height: 140rpx;" />
      </template>
    </scroll-view>

    <!-- Fixed bottom bar -->
    <view v-if="!pageLoading" class="bottom-bar">
      <view class="bottom-left">
        <text class="bottom-total-label">合计</text>
        <text class="bottom-total-price">
          <text class="bottom-total-symbol">¥</text>{{ totalPrice }}
        </text>
      </view>
      <view :class="['btn-pay', { disabled: submitting }]" @tap="onPay">
        <view v-if="submitting" class="spinner" />
        <text class="btn-pay-text">{{ submitting ? '支付中...' : '立即支付' }}</text>
      </view>
    </view>

    <!-- Success Modal -->
    <view v-if="showSuccess" class="modal-overlay" @tap.stop>
      <view class="modal-sheet">
        <!-- Drag handle -->
        <view class="drag-handle" />

        <!-- Success icon -->
        <view class="success-icon-wrap">
          <view class="success-circle">
            <text class="success-check">✓</text>
          </view>
        </view>

        <text class="success-title">预约成功</text>

        <!-- Booking summary -->
        <view class="summary-card">
          <view class="summary-row">
            <text class="summary-label">门店</text>
            <text class="summary-value">{{ bookingRoomName }}</text>
          </view>
          <view class="summary-row">
            <text class="summary-label">座位</text>
            <text class="summary-value">{{ bookingSeatNumber }} · {{ bookingZone }}</text>
          </view>
          <view class="summary-row">
            <text class="summary-label">时间</text>
            <text class="summary-value">{{ bookingStartTime }} - {{ bookingEndTime }}</text>
          </view>
          <view class="summary-row">
            <text class="summary-label">支付金额</text>
            <text class="summary-value summary-price">¥{{ bookingPrice }}</text>
          </view>
        </view>

        <view class="btn-done" @tap="onDone">
          <text class="btn-done-text">完成</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getSeats } from '@/api/seats'
import { createBooking } from '@/api/bookings'
import { getRooms } from '@/api/rooms'

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const ZONE_LABELS = {
  quiet: '静音区',
  keyboard: '键盘区',
  vip: 'VIP区',
}

export default {
  data() {
    return {
      // Route params
      room_id: null,
      seat_id: null,
      date: '',
      start_time: '',
      end_time: '',

      // Fetched data
      roomName: '',
      roomAddress: '',
      seatNumber: '',
      seatZone: '',
      seatPosition: '',
      pricePerHour: 0,

      // UI state
      pageLoading: true,
      submitting: false,
      showSuccess: false,

      // Booking result for success modal
      bookingRoomName: '',
      bookingSeatNumber: '',
      bookingZone: '',
      bookingStartTime: '',
      bookingEndTime: '',
      bookingPrice: '',
    }
  },

  computed: {
    hours() {
      const [sh, sm] = this.start_time.split(':').map(Number)
      const [eh, em] = this.end_time.split(':').map(Number)
      return (eh * 60 + em - sh * 60 - sm) / 60
    },

    totalPrice() {
      return (this.pricePerHour * this.hours).toFixed(2)
    },

    zoneLabel() {
      return ZONE_LABELS[this.seatZone] || this.seatZone
    },

    dateLabel() {
      if (!this.date) return ''
      const parts = this.date.split('-')
      return `${parts[1]}月${parts[2]}日`
    },

    weekdayLabel() {
      if (!this.date) return ''
      const d = new Date(this.date)
      return WEEKDAYS[d.getDay()]
    },
  },

  onLoad(options) {
    this.room_id = Number(options.room_id)
    this.seat_id = Number(options.seat_id)
    this.date = options.date || ''
    this.start_time = options.start_time || ''
    this.end_time = options.end_time || ''
    this.loadData()
  },

  methods: {
    async loadData() {
      this.pageLoading = true
      try {
        // Fetch seat details
        const seats = await getSeats(this.room_id, {
          date: this.date,
          start_time: this.start_time,
          end_time: this.end_time,
        })
        const seat = (seats || []).find(s => s.id === this.seat_id)
        if (seat) {
          this.seatNumber = seat.seat_number
          this.seatZone = seat.zone
          this.seatPosition = seat.position
          this.pricePerHour = seat.price_per_hour
        }

        // Fetch room info
        const roomsData = await getRooms({ page: 1, page_size: 100 })
        const room = (roomsData.items || []).find(r => r.id === this.room_id)
        if (room) {
          this.roomName = room.name
          this.roomAddress = room.address || ''
        }
      } catch {
        uni.showToast({ title: '加载失败', icon: 'none' })
      } finally {
        this.pageLoading = false
      }
    },

    async onPay() {
      if (this.submitting) return
      this.submitting = true
      try {
        const booking = await createBooking({
          seat_id: this.seat_id,
          date: this.date,
          start_time: this.start_time,
          end_time: this.end_time,
        })
        // Fill success modal data
        this.bookingRoomName = booking.room?.name || this.roomName
        this.bookingSeatNumber = booking.seat?.seat_number || this.seatNumber
        this.bookingZone = booking.seat?.zone ? (ZONE_LABELS[booking.seat.zone] || booking.seat.zone) : this.zoneLabel
        this.bookingStartTime = booking.start_time || this.start_time
        this.bookingEndTime = booking.end_time || this.end_time
        this.bookingPrice = booking.total_price != null ? Number(booking.total_price).toFixed(2) : this.totalPrice
        this.showSuccess = true
      } catch (err) {
        if (err && (err.statusCode === 409 || err.code === 'conflict')) {
          uni.showToast({ title: '该座位该时段已被预约', icon: 'none' })
        } else {
          uni.showToast({ title: '预约失败，请重试', icon: 'none' })
        }
      } finally {
        this.submitting = false
      }
    },

    onDone() {
      uni.switchTab({ url: '/pages/orders/index' })
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  background: $bg-color;
  min-height: 100vh;
  position: relative;
}

.content {
  height: 100vh;
  padding-bottom: 0;
}

/* Loading */
.loading-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400rpx;
}

.loading-text {
  font-size: 28rpx;
  color: $text-muted;
}

/* Cards */
.card {
  background: #fff;
  border-radius: 32rpx;
  padding: 32rpx;
  margin: 24rpx 28rpx;
  box-shadow: $shadow-sm;
  animation: fadeInUp 0.3s ease both;
}

.info-card {
  animation-delay: 0s;
}

.price-card {
  animation-delay: 0.1s;
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

/* Info rows */
.info-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.time-section {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.time-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.icon-wrap {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.store-icon {
  background: $primary-light;
}

.seat-icon {
  background: #E8F5E9;
}

.date-icon {
  background: #FFF8E1;
}

.clock-icon {
  background: #F3E5F5;
}

.icon-text {
  font-size: 32rpx;
}

.info-text-wrap {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.info-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.info-sub {
  font-size: 24rpx;
  color: $text-secondary;
}

/* Hours badge */
.hours-badge {
  display: inline-flex;
  align-items: center;
  height: 36rpx;
  padding: 0 14rpx;
  border-radius: 18rpx;
  background: rgba(79, 110, 247, 0.1);
  margin-top: 4rpx;
}

.hours-badge-text {
  font-size: 22rpx;
  color: $primary;
  font-weight: 500;
}

/* Divider */
.divider {
  border-top: 2rpx dashed $border-color;
  margin: 24rpx 0;
}

/* Price card */
.price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.price-label {
  font-size: 28rpx;
  color: $text-secondary;
}

.price-value {
  font-size: 28rpx;
  color: $text-primary;
}

.total-row {
  margin-top: 0;
}

.total-label {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.total-value {
  font-size: 40rpx;
  font-weight: 700;
  color: $primary;
}

.total-symbol {
  font-size: 26rpx;
}

/* Fixed bottom bar */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #fff;
  padding: 20rpx 28rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -4rpx 16rpx rgba(0, 0, 0, 0.06);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.bottom-left {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.bottom-total-label {
  font-size: 28rpx;
  color: $text-secondary;
}

.bottom-total-price {
  font-size: 40rpx;
  font-weight: 700;
  color: $primary;
}

.bottom-total-symbol {
  font-size: 26rpx;
}

.btn-pay {
  height: 88rpx;
  padding: 0 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  border-radius: 44rpx;
  background: $primary;
  transition: all 0.2s;
}

.btn-pay.disabled {
  opacity: 0.6;
}

.btn-pay:active {
  background: $primary-dark;
}

.btn-pay-text {
  font-size: 30rpx;
  font-weight: 600;
  color: #fff;
}

.spinner {
  width: 32rpx;
  height: 32rpx;
  border: 4rpx solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Success Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 200;
  display: flex;
  align-items: flex-end;
}

.modal-sheet {
  width: 100%;
  background: #fff;
  border-radius: 48rpx 48rpx 0 0;
  padding: 32rpx 48rpx;
  padding-bottom: calc(48rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  align-items: center;
}

.drag-handle {
  width: 80rpx;
  height: 8rpx;
  border-radius: 4rpx;
  background: #E0E0E0;
  margin-bottom: 48rpx;
}

/* Success icon */
.success-icon-wrap {
  margin-bottom: 24rpx;
}

.success-circle {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: $success;
  display: flex;
  align-items: center;
  justify-content: center;
}

.success-check {
  font-size: 48rpx;
  color: #fff;
  font-weight: 700;
}

.success-title {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 32rpx;
}

/* Summary card */
.summary-card {
  width: 100%;
  background: #F8F9FA;
  border-radius: 32rpx;
  padding: 28rpx 32rpx;
  margin-bottom: 40rpx;
}

.summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 0;
}

.summary-label {
  font-size: 26rpx;
  color: $text-muted;
}

.summary-value {
  font-size: 26rpx;
  color: $text-primary;
}

.summary-price {
  font-weight: 600;
  color: $primary;
}

/* Done button */
.btn-done {
  width: 100%;
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 48rpx;
  background: $primary;
}

.btn-done:active {
  background: $primary-dark;
}

.btn-done-text {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}
</style>
