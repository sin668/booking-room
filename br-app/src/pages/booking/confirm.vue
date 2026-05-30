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
              <text class="info-sub">{{ floorLabel }}</text>
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

        <!-- Coupon Row -->
        <view class="card coupon-row-card" @tap="openCouponSheet">
          <view class="coupon-row-left">
            <view class="small-icon-wrap coupon-icon">
              <view class="ticket-icon" />
            </view>
            <text class="coupon-row-title">优惠券</text>
          </view>
          <view class="coupon-row-right">
            <text v-if="couponLoading" class="coupon-row-muted">加载中</text>
            <text v-else-if="selectedCoupon" class="coupon-row-discount">-¥{{ discountAmount }}</text>
            <text v-else-if="couponLoadError" class="coupon-row-muted">加载失败</text>
            <text v-else class="coupon-row-muted">{{ couponSummaryText }}</text>
            <text class="chevron">›</text>
          </view>
        </view>

        <!-- Payment Method Card -->
        <view class="card payment-card">
          <view class="payment-title">支付方式</view>
          <view class="payment-option" @tap="selectPaymentMethod('balance')">
            <view class="payment-option-left">
              <view class="small-icon-wrap balance-icon">
                <view class="wallet-shape-icon" />
              </view>
              <view class="payment-copy">
                <view class="payment-name-row">
                  <text class="payment-name">账户余额</text>
                  <text class="payment-balance">¥{{ walletBalanceText }}</text>
                </view>
              </view>
            </view>
            <view class="payment-option-right">
              <text v-if="isBalanceInsufficient" class="balance-warning">余额不足</text>
              <view :class="['payment-radio', { active: paymentMethod === 'balance' }]">
                <view v-if="paymentMethod === 'balance'" class="payment-radio-dot" />
              </view>
            </view>
          </view>
          <view class="payment-divider" />
          <view class="payment-option" @tap="selectPaymentMethod('wechat')">
            <view class="payment-option-left">
              <view class="small-icon-wrap wechat-icon">
                <text class="wechat-mark">微</text>
              </view>
              <text class="payment-name">微信支付</text>
            </view>
            <view :class="['payment-radio', { active: paymentMethod === 'wechat' }]">
              <view v-if="paymentMethod === 'wechat'" class="payment-radio-dot" />
            </view>
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
        <text class="success-order-id">订单编号：#{{ bookingId }}</text>

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
            <text class="summary-value">{{ bookingDate }} {{ bookingStartTime }} - {{ bookingEndTime }}</text>
          </view>
          <view class="summary-row">
            <text class="summary-label">支付金额</text>
            <text class="summary-value summary-price">¥{{ bookingPayableAmount }}</text>
          </view>
        </view>

        <view class="btn-done" @tap="onDone">
          <text class="btn-done-text">完成</text>
        </view>
      </view>
    </view>

    <!-- Coupon Bottom Sheet -->
    <view v-if="showCouponSheet" class="sheet-overlay" @tap="closeCouponSheet">
      <view class="coupon-sheet" @tap.stop>
        <view class="drag-handle" />
        <view class="sheet-header">
          <text class="sheet-title">选择优惠券</text>
          <text class="sheet-close" @tap="closeCouponSheet">×</text>
        </view>

        <view
          :class="['sheet-coupon-option', { active: !selectedCouponId }]"
          @tap="clearCouponAndClose"
        >
          <view class="sheet-coupon-main">
            <text class="sheet-coupon-name">不使用卡券</text>
            <text class="sheet-coupon-desc">按原价支付</text>
          </view>
          <view class="coupon-radio">
            <view v-if="!selectedCouponId" class="coupon-radio-dot" />
          </view>
        </view>

        <scroll-view class="sheet-coupon-list" scroll-y>
          <view v-if="!availableCoupons.length" class="coupon-empty">
            <text class="coupon-empty-text">暂无可用卡券</text>
          </view>
          <view
            v-for="coupon in availableCoupons"
            :key="coupon.id"
            :class="['sheet-coupon-option', 'sheet-coupon-item', { active: selectedCouponId === coupon.id }]"
            @tap="selectCoupon(coupon)"
          >
            <view class="sheet-coupon-main">
              <view class="coupon-name-row">
                <text class="sheet-coupon-name">{{ coupon.name }}</text>
                <text class="coupon-discount">-¥{{ money(coupon.discount_amount) }}</text>
              </view>
              <text class="sheet-coupon-desc">{{ coupon.description || couponMetaText(coupon) }}</text>
              <text class="coupon-payable">使用后实付 ¥{{ money(coupon.payable_amount) }}</text>
            </view>
            <view class="coupon-radio">
              <view v-if="selectedCouponId === coupon.id" class="coupon-radio-dot" />
            </view>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script>
import {
  createBookingOrder,
  fetchBookingCoupons,
  fetchBookingPaymentStatus,
  fetchBookingRoom,
  fetchBookingSeats,
  fetchWalletBalance,
} from '@/services/bookingPageService'
import { createPaymentStatusError, pollPaymentStatus } from '@/services/paymentPolling'
import { SEAT_ZONE_LABELS } from '@/constants/booking'
import {
  PAYMENT_POLL_INTERVAL,
  PAYMENT_POLL_MAX_ATTEMPTS,
} from '@/constants/wallet'
import { formatMoney } from '@/utils/formatters'

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
      roomFloor: '',
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
      showCouponSheet: false,
      couponOriginalPrice: '',
      couponRequestId: 0,
      walletBalance: 0,
      walletLoading: false,
      walletLoadError: false,
      walletRequestId: 0,
      paymentMethod: 'balance',
      paymentPollTimer: null,

      // Booking result for success modal
      bookingId: '',
      bookingRoomName: '',
      bookingSeatNumber: '',
      bookingZone: '',
      bookingDate: '',
      bookingStartTime: '',
      bookingEndTime: '',
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

    payableAmountNum() {
      const value = Number(this.payableAmount)
      return Number.isFinite(value) ? value : 0
    },

    isBalanceInsufficient() {
      if (this.walletLoading || this.walletLoadError) return false
      return Number(this.walletBalance) < this.payableAmountNum
    },

    walletBalanceText() {
      return this.money(this.walletBalance)
    },

    couponSummaryText() {
      if (this.selectedCoupon) return `已选择：${this.selectedCoupon.name}`
      if (this.availableCoupons.length) return `可用 ${this.availableCoupons.length} 张`
      return '暂无可用'
    },

    zoneLabel() {
      return SEAT_ZONE_LABELS[this.seatZone] || this.seatZone
    },

    floorLabel() {
      if (this.roomFloor !== '' && this.roomFloor != null) {
        return `${this.roomFloor}楼`
      }
      return this.roomAddress || '楼层待确认'
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

  onUnload() {
    this.clearPaymentPollTimer()
  },

  methods: {
    async loadData() {
      this.pageLoading = true
      try {
        // Fetch seat details
        const seats = await fetchBookingSeats(this.room_id, {
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
          this.roomFloor = seat.floor ?? ''
        }

        const room = await fetchBookingRoom(this.room_id)
        this.roomName = room.name
        this.roomAddress = room.address || ''
        if ((this.roomFloor === '' || this.roomFloor == null) && room.floor != null) {
          this.roomFloor = room.floor
        }

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
        const res = await fetchBookingCoupons({
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
        const res = await fetchWalletBalance()
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
      this.closeCouponSheet()
    },

    clearCoupon() {
      this.selectedCouponId = null
      this.selectedCoupon = null
    },

    clearCouponAndClose() {
      this.clearCoupon()
      this.closeCouponSheet()
    },

    openCouponSheet() {
      if (this.couponLoadError) {
        this.loadAvailableCoupons()
        return
      }
      if (!this.availableCoupons.length) {
        uni.showToast({ title: '暂无可用卡券', icon: 'none' })
        return
      }
      this.showCouponSheet = true
    },

    closeCouponSheet() {
      this.showCouponSheet = false
    },

    selectPaymentMethod(method) {
      if (method === 'balance' || method === 'wechat') {
        this.paymentMethod = method
      }
    },

    async onPay() {
      if (this.submitting) return
      if (this.paymentMethod === 'balance' && this.isBalanceInsufficient) {
        uni.showToast({ title: '余额不足，请切换微信支付或先充值', icon: 'none' })
        return
      }

      this.submitting = true
      try {
        const payload = {
          seat_id: this.seat_id,
          date: this.date,
          start_time: this.start_time,
          end_time: this.end_time,
          payment_method: this.paymentMethod,
        }
        if (this.selectedCouponId) {
          payload.coupon_id = this.selectedCouponId
        }

        const booking = await createBookingOrder(payload)

        if (this.paymentMethod === 'wechat') {
          const paymentParams = booking.payment_params || booking.paymentParams
          if (!paymentParams) {
            throw new Error('missing payment params')
          }
          await this.requestWechatPayment(paymentParams)
          const paidStatus = await this.pollBookingPaymentStatus(booking.id)
          if (!paidStatus) {
            uni.showToast({ title: '支付处理中，请稍后在订单中查看', icon: 'none' })
            return
          }
        }

        this.showBookingSuccess(booking)
        if (this.paymentMethod === 'balance') {
          this.loadWalletBalance()
        }
      } catch (err) {
        if (this.isCouponUnavailableError(err)) {
          uni.showToast({ title: '卡券不可用，请重新选择', icon: 'none' })
          this.clearCoupon()
          await this.loadAvailableCoupons()
        } else if (this.isBookingConflictError(err)) {
          uni.showToast({ title: '该座位该时段已被预约，请重新选择', icon: 'none' })
        } else if (this.isWalletBalanceInsufficientError(err)) {
          uni.showToast({ title: '余额不足，请切换微信支付或先充值', icon: 'none' })
        } else if (this.isPaymentCancel(err)) {
          uni.showToast({ title: '支付已取消', icon: 'none' })
        } else if (err?.paymentFailed) {
          uni.showToast({ title: '支付失败，请重试', icon: 'none' })
        } else if (err?.paymentStatus) {
          uni.showToast({ title: '支付失败，请重试', icon: 'none' })
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

    showBookingSuccess(booking) {
      this.bookingId = booking.id || ''
      this.bookingRoomName = booking.room?.name || this.roomName
      this.bookingSeatNumber = booking.seat?.seat_number || this.seatNumber
      this.bookingZone = booking.seat?.zone ? (SEAT_ZONE_LABELS[booking.seat.zone] || booking.seat.zone) : this.zoneLabel
      this.bookingDate = booking.date || this.date
      this.bookingStartTime = booking.start_time || this.start_time
      this.bookingEndTime = booking.end_time || this.end_time
      this.bookingPayableAmount = this.money(booking.total_price != null ? booking.total_price : this.payableAmount)
      this.showSuccess = true
    },

    requestWechatPayment(paymentParams) {
      return new Promise((resolve, reject) => {
        uni.requestPayment({
          ...paymentParams,
          success: resolve,
          fail: (err) => {
            if (!this.isPaymentCancel(err)) {
              err.paymentFailed = true
            }
            reject(err)
          },
        })
      })
    },

    async pollBookingPaymentStatus(bookingId) {
      return pollPaymentStatus({
        fetchStatus: () => fetchBookingPaymentStatus(bookingId),
        isSuccess: (status) => status === 'paid',
        wait: () => this.wait(PAYMENT_POLL_INTERVAL),
        maxAttempts: PAYMENT_POLL_MAX_ATTEMPTS,
      })
    },

    wait(ms) {
      return new Promise((resolve) => {
        this.clearPaymentPollTimer()
        this.paymentPollTimer = setTimeout(() => {
          this.paymentPollTimer = null
          resolve()
        }, ms)
      })
    },

    clearPaymentPollTimer() {
      if (this.paymentPollTimer) {
        clearTimeout(this.paymentPollTimer)
        this.paymentPollTimer = null
      }
    },

    createPaymentStatusError(status) {
      return createPaymentStatusError(status)
    },

    money(value) {
      return formatMoney(value)
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

    isPaymentCancel(err) {
      const text = this.errorText(err).toLowerCase()
      return text.includes('cancel')
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  background: linear-gradient(180deg, $bg-warm 0, $bg-color 420rpx);
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
  background: $surface;
  border-radius: 34rpx;
  padding: 32rpx;
  margin: 24rpx 28rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  animation: fadeInUp 0.3s ease both;
}

.info-card {
  animation-delay: 0s;
}

.price-card {
  animation-delay: 0.1s;
}

.coupon-row-card {
  animation-delay: 0.05s;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 32rpx;
}

.payment-card {
  animation-delay: 0.08s;
  padding: 0;
  overflow: hidden;
}

.payment-title {
  padding: 30rpx 32rpx 14rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
}

.payment-option {
  min-height: 104rpx;
  padding: 24rpx 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  transition: background 0.2s;
}

.payment-option:active,
.coupon-row-card:active {
  background: $surface-soft;
}

.payment-option-left,
.coupon-row-left,
.coupon-row-right,
.payment-option-right,
.payment-name-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.payment-option-left,
.coupon-row-left {
  min-width: 0;
  flex: 1;
}

.payment-copy {
  min-width: 0;
}

.payment-name,
.coupon-row-title {
  font-size: 28rpx;
  color: $text-primary;
}

.payment-balance,
.coupon-row-muted {
  font-size: 24rpx;
  color: $text-muted;
}

.balance-warning,
.coupon-row-discount {
  font-size: 24rpx;
  font-weight: 600;
  color: #E64A19;
}

.payment-divider {
  height: 1rpx;
  margin: 0 32rpx;
  background: $border-color;
}

.payment-radio {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 3rpx solid $border-color;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.payment-radio.active {
  border-color: $primary;
}

.payment-radio-dot {
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
  background: $primary;
}

.small-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.coupon-icon {
  background: #FFEBEE;
}

.balance-icon {
  background: $primary-light;
}

.wechat-icon {
  background: #E8F5E9;
}

.ticket-icon {
  width: 34rpx;
  height: 24rpx;
  border-radius: 6rpx;
  background: #EF5350;
  position: relative;
}

.ticket-icon::before,
.ticket-icon::after {
  content: '';
  position: absolute;
  top: 8rpx;
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: #fff;
}

.ticket-icon::before {
  left: -4rpx;
}

.ticket-icon::after {
  right: -4rpx;
}

.wallet-shape-icon {
  width: 34rpx;
  height: 28rpx;
  border-radius: 8rpx;
  border: 4rpx solid $primary;
  position: relative;
}

.wallet-shape-icon::after {
  content: '';
  position: absolute;
  right: -4rpx;
  top: 7rpx;
  width: 12rpx;
  height: 10rpx;
  border-radius: 6rpx 0 0 6rpx;
  background: $primary;
}

.wechat-mark {
  font-size: 24rpx;
  font-weight: 700;
  color: $success;
}

.chevron {
  font-size: 38rpx;
  line-height: 1;
  color: $text-muted;
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
  border-radius: 16rpx;
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

.sheet-coupon-option {
  min-height: 96rpx;
  padding: 20rpx;
  border: 2rpx solid $border-soft;
  border-radius: 20rpx;
  background: $surface-soft;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  transition: all 0.2s;
}

.sheet-coupon-option.active {
  border-color: $primary;
  background: $primary-soft;
}

.sheet-coupon-item {
  align-items: flex-start;
}

.sheet-coupon-main {
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

.sheet-coupon-name {
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

.sheet-coupon-desc,
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

.sheet-coupon-option.active .coupon-radio {
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
  background: rgba(255, 255, 255, 0.98);
  padding: 20rpx 28rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  box-shadow: $shadow-bottom;
  backdrop-filter: blur(18rpx);
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
  background: $gradient-primary;
  box-shadow: $shadow-float;
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
  background: $surface;
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
  margin-bottom: 8rpx;
}

.success-order-id {
  max-width: 100%;
  font-size: 24rpx;
  color: $text-muted;
  margin-bottom: 32rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Summary card */
.summary-card {
  width: 100%;
  background: $surface-soft;
  border: 1rpx solid $border-soft;
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

.summary-price {
  font-weight: 600;
  color: $primary;
}

/* Coupon sheet */
.sheet-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 210;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: flex-end;
}

.coupon-sheet {
  width: 100%;
  max-height: 76vh;
  background: $surface;
  border-radius: 48rpx 48rpx 0 0;
  padding: 24rpx 32rpx;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
}

.coupon-sheet .drag-handle {
  margin: 0 auto 28rpx;
}

.sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.sheet-title {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
}

.sheet-close {
  width: 56rpx;
  height: 56rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 38rpx;
  line-height: 1;
  color: $text-muted;
  background: #F8F9FA;
}

.sheet-coupon-list {
  max-height: 52vh;
  margin-top: 16rpx;
}

.sheet-coupon-list .sheet-coupon-option {
  margin-bottom: 16rpx;
}

.coupon-empty {
  min-height: 160rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.coupon-empty-text {
  font-size: 26rpx;
  color: $text-muted;
}

/* Done button */
.btn-done {
  width: 100%;
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 48rpx;
  background: $gradient-primary;
  box-shadow: $shadow-float;
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
