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
              <view class="building-icon" />
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
              <view class="seat-shape-icon" />
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
                <view class="calendar-icon" />
              </view>
              <view class="info-text-wrap">
                <text class="info-title">{{ dateLabel }}</text>
                <text class="info-sub">{{ weekdayLabel }}</text>
              </view>
            </view>
            <view class="time-row">
              <view class="icon-wrap clock-icon">
                <view class="clock-shape-icon">
                  <view class="clock-hand hour" />
                  <view class="clock-hand minute" />
                </view>
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

        <!-- Coupon Card -->
        <view class="card coupon-card">
          <view class="coupon-header">
            <view class="coupon-title-wrap">
              <text class="coupon-title">卡券优惠</text>
              <text class="coupon-sub">{{ couponSummaryText }}</text>
            </view>
            <view v-if="couponLoading" class="coupon-loading">
              <view class="coupon-spinner" />
              <text class="coupon-loading-text">加载中</text>
            </view>
          </view>

          <view v-if="couponLoadError" class="coupon-error">
            <text class="coupon-error-text">{{ couponLoadError }}</text>
            <text class="coupon-retry" @tap="loadAvailableCoupons">重试</text>
          </view>

          <view
            :class="['coupon-option', { active: !selectedCouponId }]"
            @tap="clearCoupon"
          >
            <view class="coupon-option-main">
              <text class="coupon-option-name">不使用卡券</text>
              <text class="coupon-option-desc">按原价支付</text>
            </view>
            <view class="coupon-radio">
              <view v-if="!selectedCouponId" class="coupon-radio-dot" />
            </view>
          </view>

          <view v-if="availableCoupons.length" class="coupon-list">
            <view
              v-for="coupon in availableCoupons"
              :key="coupon.id"
              :class="['coupon-option', 'coupon-item', { active: selectedCouponId === coupon.id }]"
              @tap="selectCoupon(coupon)"
            >
              <view class="coupon-option-main">
                <view class="coupon-name-row">
                  <text class="coupon-option-name">{{ coupon.name }}</text>
                  <text class="coupon-discount">-¥{{ money(coupon.discount_amount) }}</text>
                </view>
                <text class="coupon-option-desc">{{ coupon.description || couponMetaText(coupon) }}</text>
                <text class="coupon-payable">使用后实付 ¥{{ money(coupon.payable_amount) }}</text>
              </view>
              <view class="coupon-radio">
                <view v-if="selectedCouponId === coupon.id" class="coupon-radio-dot" />
              </view>
            </view>
          </view>
        </view>

        <!-- Wallet Balance Card -->
        <view class="card wallet-card">
          <view class="wallet-card-main">
            <view class="wallet-copy">
              <text class="wallet-title">钱包余额</text>
            </view>
            <view class="wallet-amount-wrap">
              <text class="wallet-symbol">¥</text>
              <text class="wallet-amount">{{ walletBalanceText }}</text>
            </view>
          </view>
          <view class="wallet-footer">
            <text :class="['wallet-status', { error: walletLoadError }]">{{ walletStatusText }}</text>
            <text class="wallet-refresh" @tap="loadWalletBalance">刷新</text>
          </view>
        </view>

        <!-- Price Summary Card -->
        <view class="card price-card">
          <view class="price-row">
            <text class="price-label">座位费（{{ zoneLabel }} · {{ hours }}小时）</text>
            <text class="price-value">¥{{ originalPrice }}</text>
          </view>

          <view class="price-row">
            <text class="price-label">优惠券抵扣</text>
            <text :class="['price-value', { discount: discountAmountNum > 0 }]">
              {{ discountAmountNum > 0 ? '-¥' + discountAmount : '¥0.00' }}
            </text>
          </view>

          <view class="divider" />

          <view class="price-row total-row">
            <text class="total-label">实付金额</text>
            <text class="total-value">
              <text class="total-symbol">¥</text>{{ payableAmount }}
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
          <text class="bottom-total-symbol">¥</text>{{ payableAmount }}
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
            <text class="summary-label">订单编号</text>
            <text class="summary-value">#{{ bookingId }}</text>
          </view>
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
            <text class="summary-value">{{ bookingDate }} {{ bookingStartTime }} - {{ bookingEndTime }}</text>
          </view>
          <view class="summary-row">
            <text class="summary-label">原价</text>
            <text class="summary-value">¥{{ bookingOriginalPrice }}</text>
          </view>
          <view class="summary-row">
            <text class="summary-label">优惠抵扣</text>
            <text :class="['summary-value', { 'summary-discount': bookingDiscountAmountNum > 0 }]">
              {{ bookingDiscountAmountNum > 0 ? '-¥' + bookingDiscountAmount : '¥0.00' }}
            </text>
          </view>
          <view class="summary-row">
            <text class="summary-label">实付金额</text>
            <text class="summary-value summary-price">¥{{ bookingPayableAmount }}</text>
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
import { getRoom } from '@/api/rooms'
import { getAvailableCouponsForBooking } from '@/api/coupons'
import { getBalance } from '@/api/wallet'

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
      availableCoupons: [],
      selectedCouponId: null,
      selectedCoupon: null,
      couponLoading: false,
      couponLoadError: '',
      couponOriginalPrice: '',
      couponRequestId: 0,
      walletBalance: 0,
      walletLoading: false,
      walletLoadError: false,
      walletRequestId: 0,

      // Booking result for success modal
      bookingId: '',
      bookingRoomName: '',
      bookingSeatNumber: '',
      bookingZone: '',
      bookingDate: '',
      bookingStartTime: '',
      bookingEndTime: '',
      bookingOriginalPrice: '',
      bookingDiscountAmount: '',
      bookingPayableAmount: '',
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

    originalPrice() {
      return this.money(this.couponOriginalPrice || this.totalPrice)
    },

    discountAmountNum() {
      if (!this.selectedCoupon) return 0
      const value = Number(this.selectedCoupon.discount_amount)
      return Number.isFinite(value) ? value : 0
    },

    discountAmount() {
      return this.money(this.selectedCoupon?.discount_amount || 0)
    },

    payableAmount() {
      if (this.selectedCoupon) {
        return this.money(this.selectedCoupon.payable_amount)
      }
      return this.originalPrice
    },

    walletBalanceText() {
      return this.money(this.walletBalance)
    },

    walletStatusText() {
      if (this.walletLoading) return '正在更新余额'
      if (this.walletLoadError) return '余额加载失败'
      return '将使用钱包余额支付'
    },

    couponSummaryText() {
      if (this.couponLoading && !this.availableCoupons.length) return '正在匹配可用卡券'
      if (this.selectedCoupon) return `已选择：${this.selectedCoupon.name}`
      return `可用 ${this.availableCoupons.length} 张`
    },

    bookingDiscountAmountNum() {
      const value = Number(this.bookingDiscountAmount)
      return Number.isFinite(value) ? value : 0
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

        const room = await getRoom(this.room_id)
        this.roomName = room.name
        this.roomAddress = room.address || ''

        await Promise.all([
          this.loadAvailableCoupons(),
          this.loadWalletBalance(),
        ])
      } catch {
        uni.showToast({ title: '加载失败', icon: 'none' })
      } finally {
        this.pageLoading = false
      }
    },

    async loadAvailableCoupons() {
      const requestId = ++this.couponRequestId
      this.couponLoading = true
      this.couponLoadError = ''
      try {
        const res = await getAvailableCouponsForBooking({
          seat_id: this.seat_id,
          date: this.date,
          start_time: this.start_time,
          end_time: this.end_time,
        })
        if (requestId !== this.couponRequestId) return
        this.couponOriginalPrice = res?.original_price || this.totalPrice
        this.availableCoupons = Array.isArray(res?.items) ? res.items : []

        if (this.selectedCouponId) {
          const refreshed = this.availableCoupons.find(coupon => coupon.id === this.selectedCouponId)
          this.selectedCoupon = refreshed || null
          if (!refreshed) this.selectedCouponId = null
        }
      } catch {
        if (requestId !== this.couponRequestId) return
        this.availableCoupons = []
        this.clearCoupon()
        this.couponLoadError = '卡券加载失败，请重试'
      } finally {
        if (requestId === this.couponRequestId) {
          this.couponLoading = false
        }
      }
    },

    async loadWalletBalance() {
      const requestId = ++this.walletRequestId
      this.walletLoading = true
      this.walletLoadError = false
      try {
        const res = await getBalance()
        if (requestId !== this.walletRequestId) return
        this.walletBalance = res?.balance || 0
      } catch {
        if (requestId !== this.walletRequestId) return
        this.walletLoadError = true
      } finally {
        if (requestId === this.walletRequestId) {
          this.walletLoading = false
        }
      }
    },

    selectCoupon(coupon) {
      this.selectedCouponId = coupon.id
      this.selectedCoupon = coupon
    },

    clearCoupon() {
      this.selectedCouponId = null
      this.selectedCoupon = null
    },

    async onPay() {
      if (this.submitting) return
      this.submitting = true
      try {
        const payload = {
          seat_id: this.seat_id,
          date: this.date,
          start_time: this.start_time,
          end_time: this.end_time,
          payment_method: 'wallet',
        }
        if (this.selectedCouponId) {
          payload.coupon_id = this.selectedCouponId
        }

        const booking = await createBooking(payload)
        // Fill success modal data
        this.bookingId = booking.id || ''
        this.bookingRoomName = booking.room?.name || this.roomName
        this.bookingSeatNumber = booking.seat?.seat_number || this.seatNumber
        this.bookingZone = booking.seat?.zone ? (ZONE_LABELS[booking.seat.zone] || booking.seat.zone) : this.zoneLabel
        this.bookingDate = booking.date || this.date
        this.bookingStartTime = booking.start_time || this.start_time
        this.bookingEndTime = booking.end_time || this.end_time
        this.bookingOriginalPrice = this.money(booking.original_price != null ? booking.original_price : this.originalPrice)
        this.bookingDiscountAmount = this.money(booking.discount_amount != null ? booking.discount_amount : this.discountAmount)
        this.bookingPayableAmount = this.money(booking.total_price != null ? booking.total_price : this.payableAmount)
        this.showSuccess = true
        this.loadWalletBalance()
      } catch (err) {
        if (this.isCouponUnavailableError(err)) {
          uni.showToast({ title: '卡券不可用，请重新选择', icon: 'none' })
          this.clearCoupon()
          await this.loadAvailableCoupons()
        } else if (this.isBookingConflictError(err)) {
          uni.showToast({ title: '该座位该时段已被预约，请重新选择', icon: 'none' })
        } else if (this.isWalletBalanceInsufficientError(err)) {
          uni.showToast({ title: '钱包余额不足，请先充值', icon: 'none' })
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

    money(value) {
      const num = Number(value)
      return Number.isFinite(num) ? num.toFixed(2) : '0.00'
    },

    couponMetaText(coupon) {
      if (coupon.min_order_amount) {
        return `满 ¥${this.money(coupon.min_order_amount)} 可用`
      }
      return '当前预约可用'
    },

    errorText(err) {
      if (!err) return ''
      if (typeof err === 'string') return err
      return err.detail || err.message || err.errMsg || err.error || ''
    },

    isCouponUnavailableError(err) {
      const text = this.errorText(err)
      const code = err?.code || err?.status || err?.statusCode
      return code === 'coupon_unavailable' || /卡券|coupon|优惠券|不可用|重新选择/i.test(text)
    },

    isBookingConflictError(err) {
      const text = this.errorText(err)
      return err?.statusCode === 409 || err?.code === 'conflict' || /座位.*时段.*预约/.test(text)
    },

    isWalletBalanceInsufficientError(err) {
      const text = this.errorText(err)
      return err?.statusCode === 402 || /wallet balance is insufficient/i.test(text)
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

.coupon-card {
  animation-delay: 0.05s;
}

.wallet-card {
  border: 1rpx solid rgba(79, 110, 247, 0.12);
  background: #fff;
  animation-delay: 0.08s;
}

.wallet-card-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.wallet-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.wallet-title {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.wallet-amount-wrap {
  flex-shrink: 0;
  display: flex;
  align-items: baseline;
  color: $primary;
}

.wallet-symbol {
  font-size: 24rpx;
  font-weight: 600;
}

.wallet-amount {
  font-size: 28rpx;
  line-height: 1;
  font-weight: 600;
}

.wallet-footer {
  margin-top: 18rpx;
  padding-top: 16rpx;
  border-top: 1rpx solid rgba(79, 110, 247, 0.12);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.wallet-status {
  min-width: 0;
  font-size: 24rpx;
  color: $text-secondary;
}

.wallet-status.error {
  color: $danger;
}

.wallet-refresh {
  flex-shrink: 0;
  font-size: 24rpx;
  font-weight: 600;
  color: $primary;
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

.building-icon {
  width: 34rpx;
  height: 40rpx;
  border-radius: 6rpx;
  background: $primary;
  position: relative;
}

.building-icon::before,
.building-icon::after {
  content: '';
  position: absolute;
  width: 6rpx;
  height: 6rpx;
  border-radius: 2rpx;
  background: $white;
  left: 8rpx;
  box-shadow: 12rpx 0 0 $white;
}

.building-icon::before {
  top: 9rpx;
}

.building-icon::after {
  top: 22rpx;
}

.seat-shape-icon {
  width: 36rpx;
  height: 26rpx;
  border-radius: 8rpx 8rpx 5rpx 5rpx;
  background: $success;
  position: relative;
}

.seat-shape-icon::before,
.seat-shape-icon::after {
  content: '';
  position: absolute;
  bottom: -8rpx;
  width: 7rpx;
  height: 10rpx;
  border-radius: 0 0 4rpx 4rpx;
  background: $success;
}

.seat-shape-icon::before {
  left: 5rpx;
}

.seat-shape-icon::after {
  right: 5rpx;
}

.calendar-icon {
  width: 36rpx;
  height: 34rpx;
  border-radius: 7rpx;
  border: 4rpx solid #e67900;
  position: relative;
}

.calendar-icon::before {
  content: '';
  position: absolute;
  top: 8rpx;
  left: 0;
  right: 0;
  height: 4rpx;
  background: #e67900;
}

.clock-shape-icon {
  width: 38rpx;
  height: 38rpx;
  border-radius: 50%;
  border: 4rpx solid $purple;
  position: relative;
}

.clock-hand {
  position: absolute;
  left: 50%;
  bottom: 50%;
  width: 4rpx;
  border-radius: 4rpx;
  background: $purple;
  transform-origin: bottom center;
}

.clock-hand.hour {
  height: 11rpx;
  transform: translateX(-50%) rotate(-35deg);
}

.clock-hand.minute {
  height: 14rpx;
  transform: translateX(-50%) rotate(80deg);
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

/* Coupon card */
.coupon-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  margin-bottom: 24rpx;
}

.coupon-title-wrap {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.coupon-title {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-primary;
}

.coupon-sub {
  max-width: 480rpx;
  font-size: 24rpx;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.coupon-loading {
  display: flex;
  align-items: center;
  gap: 8rpx;
  flex-shrink: 0;
}

.coupon-spinner {
  width: 24rpx;
  height: 24rpx;
  border: 3rpx solid rgba(79, 110, 247, 0.18);
  border-top-color: $primary;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.coupon-loading-text {
  font-size: 22rpx;
  color: $text-muted;
}

.coupon-error {
  min-height: 64rpx;
  padding: 0 20rpx;
  margin-bottom: 16rpx;
  border-radius: 16rpx;
  background: #FFF3E0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.coupon-error-text {
  min-width: 0;
  flex: 1;
  font-size: 24rpx;
  color: #E67900;
}

.coupon-retry {
  flex-shrink: 0;
  font-size: 24rpx;
  font-weight: 600;
  color: $primary;
}

.coupon-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 16rpx;
}

.coupon-option {
  min-height: 96rpx;
  padding: 20rpx;
  border: 2rpx solid $border-color;
  border-radius: 20rpx;
  background: #FAFBFC;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  transition: all 0.2s;
}

.coupon-option.active {
  border-color: $primary;
  background: rgba(79, 110, 247, 0.06);
}

.coupon-item {
  align-items: flex-start;
}

.coupon-option-main {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.coupon-name-row {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.coupon-option-name {
  min-width: 0;
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.coupon-discount {
  flex-shrink: 0;
  font-size: 28rpx;
  font-weight: 700;
  color: #E64A19;
}

.coupon-option-desc,
.coupon-payable {
  max-width: 100%;
  font-size: 23rpx;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.coupon-payable {
  color: $primary;
}

.coupon-radio {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 3rpx solid $border-color;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.coupon-option.active .coupon-radio {
  border-color: $primary;
}

.coupon-radio-dot {
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  background: $primary;
}

/* Price card */
.price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  margin-bottom: 18rpx;
}

.price-row:last-child {
  margin-bottom: 0;
}

.price-label {
  min-width: 0;
  font-size: 28rpx;
  color: $text-secondary;
}

.price-value {
  flex-shrink: 0;
  font-size: 28rpx;
  color: $text-primary;
}

.price-value.discount {
  color: #E64A19;
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
  max-width: 440rpx;
  font-size: 26rpx;
  color: $text-primary;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-discount {
  font-weight: 600;
  color: #E64A19;
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
