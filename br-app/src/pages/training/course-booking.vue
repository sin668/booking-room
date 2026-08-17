<template>
  <view class="page">
    <!-- Custom Navigation Bar -->
    <view class="nav-bar">
      <view class="nav-back" @tap="goBack">
        <text class="nav-back-icon">‹</text>
      </view>
      <text class="nav-title">预约课程</text>
      <view class="nav-placeholder" />
    </view>

    <scroll-view class="content" scroll-y>
      <!-- Loading state -->
      <view v-if="pageLoading" class="loading-wrap">
        <text class="loading-text">加载中...</text>
      </view>

      <template v-else>
        <!-- Course Info Summary -->
        <view class="card course-card">
          <view class="course-row">
            <image
              v-if="courseInfo.cover_image"
              class="course-cover"
              :src="courseInfo.cover_image"
              mode="aspectFill"
            />
            <view v-else class="course-cover course-cover-placeholder" />
            <view class="course-info">
              <text class="course-name">{{ courseInfo.name }}</text>
              <view class="teacher-row">
                <image
                  v-if="courseInfo.teacher && courseInfo.teacher.avatar"
                  class="teacher-avatar"
                  :src="courseInfo.teacher.avatar"
                  mode="aspectFill"
                />
                <view v-else class="teacher-avatar teacher-avatar-placeholder" />
                <text class="teacher-name">{{ teacherName }} 老师</text>
              </view>
            </view>
            <view class="course-price-wrap">
              <text class="course-price">¥{{ currentUnitPrice }}</text>
              <text class="course-price-unit">/课时</text>
            </view>
          </view>
        </view>

        <!-- Booking Type Selection -->
        <view class="card type-card">
          <view class="section-header">
            <view class="section-bar" />
            <text class="section-title">预约类型</text>
          </view>
          <view class="type-grid">
            <view
              :class="['type-item', { active: bookingType === 'fixed' }]"
              @tap="switchBookingType('fixed')"
            >
              <view class="type-item-header">
                <text class="type-item-name">固定班课</text>
                <view :class="['type-radio', { active: bookingType === 'fixed' }]">
                  <view v-if="bookingType === 'fixed'" class="type-radio-dot" />
                </view>
              </view>
              <text class="type-item-desc">{{ scheduleDesc || '按课表上课' }}</text>
              <view class="type-item-price-row">
                <text class="type-item-price">¥{{ courseInfo.price }}</text>
                <text class="type-item-unit">/课时</text>
              </view>
            </view>
            <view
              :class="['type-item', { active: bookingType === 'custom' }]"
              @tap="switchBookingType('custom')"
            >
              <view class="type-item-header">
                <text class="type-item-name">1V1私人定制</text>
                <view :class="['type-radio', { active: bookingType === 'custom' }]">
                  <view v-if="bookingType === 'custom'" class="type-radio-dot" />
                </view>
              </view>
              <text class="type-item-desc">自由选择时间</text>
              <view class="type-item-price-row">
                <text class="type-item-price">¥{{ courseInfo.custom_price }}</text>
                <text class="type-item-unit">/课时</text>
              </view>
            </view>
          </view>
        </view>

        <!-- Lesson Selection -->
        <view class="card lesson-card">
          <view class="lesson-header">
            <view class="section-header">
              <view class="section-bar" />
              <text class="section-title">选择课时</text>
            </view>
            <text class="lesson-count">已选 <text class="lesson-count-num">{{ selectedLessonIds.length }}</text> 节</text>
          </view>

          <view
            v-for="(lesson, index) in visibleLessons"
            :key="lesson.id"
            :class="['lesson-item', { selected: selectedLessonIds.includes(lesson.id) }]"
            @tap="toggleLesson(lesson.id)"
          >
            <view class="lesson-checkbox">
              <text v-if="selectedLessonIds.includes(lesson.id)" class="lesson-check-icon">✓</text>
            </view>
            <view class="lesson-icon-wrap">
              <text class="lesson-play-icon">▶</text>
            </view>
            <view class="lesson-info">
              <text class="lesson-title">{{ lesson.title }}</text>
              <view class="lesson-meta">
                <text class="lesson-duration">{{ formatDuration(lesson.duration_minutes) }}</text>
                <text class="lesson-status">可预约</text>
              </view>
            </view>
            <text class="lesson-price">¥{{ currentUnitPrice }}</text>
          </view>

          <!-- Full course promo -->
          <view
            v-if="!isFullPackage && courseInfo.full_package_price"
            class="full-package-bar"
            @tap="selectFullPackage"
          >
            <view class="full-package-left">
              <view class="full-package-icon-wrap">
                <text class="full-package-icon-text">¥</text>
              </view>
              <view class="full-package-text">
                <text class="full-package-title">全套{{ lessons.length }}课时更划算</text>
                <text class="full-package-save">立省¥{{ fullPackageSaveAmount }}</text>
              </view>
            </view>
            <text class="full-package-link">选择全套 ›</text>
          </view>

          <!-- Expand/collapse toggle -->
          <view
            v-if="lessons.length > 4 && !isFullPackage"
            class="lessons-expand-btn"
            @tap="lessonsExpanded = !lessonsExpanded"
          >
            <text class="lessons-expand-text">{{ lessonsExpanded ? '收起课时' : '查看全部' + lessons.length + '节课时' }}</text>
            <text class="lessons-expand-arrow">{{ lessonsExpanded ? '∧' : '›' }}</text>
          </view>
        </view>

        <!-- Schedule: Fixed -->
        <view v-if="scheduleType === 'fixed'" class="card schedule-card">
          <view class="section-header">
            <view class="section-bar" />
            <text class="section-title">上课时间</text>
          </view>
          <view class="schedule-fixed-box">
            <view class="schedule-icon-wrap">
              <text class="schedule-cal-icon">☑</text>
            </view>
            <view class="schedule-info">
              <text class="schedule-time-text">{{ scheduleDesc || '按课表上课' }}</text>
              <text class="schedule-desc">固定班课，按课表上课</text>
            </view>
          </view>
        </view>

        <!-- Schedule: Custom -->
        <view v-if="scheduleType === 'custom'" class="card schedule-card">
          <view class="section-header">
            <view class="section-bar" />
            <text class="section-title">选择上课时间</text>
          </view>
          <view class="schedule-custom-notice">
            <text class="schedule-custom-text">选择课时后可与老师协商上课时间</text>
          </view>
        </view>

        <!-- Coupon Row -->
        <view class="card coupon-card" @tap="openCouponSheet">
          <view class="coupon-row-left">
            <view class="small-icon-wrap coupon-icon">
              <view class="ticket-icon" />
            </view>
            <text class="coupon-row-title">优惠券</text>
          </view>
          <view class="coupon-row-right">
            <text v-if="couponLoading" class="coupon-row-muted">加载中</text>
            <text v-else-if="coupon" class="coupon-row-discount">-¥{{ couponDiscountText }}</text>
            <text v-else class="coupon-row-muted">{{ couponSummaryText }}</text>
            <text class="chevron">›</text>
          </view>
        </view>

        <!-- Payment Method -->
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

        <!-- Price Summary -->
        <view class="card price-card">
          <view class="price-row">
            <text class="price-label">{{ priceLabel }}</text>
            <text class="price-value">¥{{ priceSummary.originalPrice }}</text>
          </view>
          <view v-if="priceSummary.discountAmount > 0" class="price-row">
            <text class="price-label">套餐优惠</text>
            <text class="price-value discount">-¥{{ priceSummary.discountAmount }}</text>
          </view>
          <view class="price-row">
            <text class="price-label">优惠券</text>
            <text :class="['price-value', { discount: priceSummary.couponDiscount > 0 }]">
              {{ priceSummary.couponDiscount > 0 ? '-¥' + priceSummary.couponDiscount : '¥0.00' }}
            </text>
          </view>
          <view class="price-divider" />
          <view class="price-total-section">
            <text class="total-label">实付金额</text>
            <view class="total-value-wrap">
              <text class="total-symbol">¥</text>
              <text class="total-value">{{ priceSummary.totalPrice }}</text>
            </view>
          </view>
        </view>

        <!-- Bottom spacing -->
        <view style="height: 160rpx;" />
      </template>
    </scroll-view>

    <!-- Fixed bottom bar -->
    <view v-if="!pageLoading" class="bottom-bar">
      <view class="bottom-left">
        <text class="bottom-total-label">合计</text>
        <text class="bottom-total-price">
          <text class="bottom-total-symbol">¥</text>{{ priceSummary.totalPrice }}
        </text>
      </view>
      <view :class="['btn-pay', { disabled: submitting }]" @tap="submitOrder">
        <view v-if="submitting" class="spinner" />
        <text class="btn-pay-text">{{ submitting ? '支付中...' : '立即支付' }}</text>
      </view>
    </view>

    <!-- Success Modal -->
    <view v-if="showSuccessModal" class="modal-overlay" @tap.stop>
      <view class="modal-sheet">
        <view class="drag-handle" />
        <view class="success-icon-wrap">
          <view class="success-circle">
            <text class="success-check">✓</text>
          </view>
        </view>
        <text class="success-title">预约成功</text>
        <text class="success-order-id">订单编号：#{{ successInfo.booking_id }}</text>
        <view class="summary-card">
          <view class="summary-row">
            <text class="summary-label">课程</text>
            <text class="summary-value">{{ courseInfo.name }}</text>
          </view>
          <view class="summary-row">
            <text class="summary-label">老师</text>
            <text class="summary-value">{{ teacherName }}</text>
          </view>
          <view class="summary-row">
            <text class="summary-label">课时</text>
            <text class="summary-value">{{ selectedLessonIds.length }}课时</text>
          </view>
          <view class="summary-row">
            <text class="summary-label">支付金额</text>
            <text class="summary-value summary-price">¥{{ priceSummary.totalPrice }}</text>
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
          :class="['sheet-coupon-option', { active: !coupon }]"
          @tap="clearCouponAndClose"
        >
          <view class="sheet-coupon-main">
            <text class="sheet-coupon-name">不使用卡券</text>
            <text class="sheet-coupon-desc">按原价支付</text>
          </view>
          <view class="coupon-radio">
            <view v-if="!coupon" class="coupon-radio-dot" />
          </view>
        </view>

        <scroll-view class="sheet-coupon-list" scroll-y>
          <view v-if="!availableCoupons.length" class="coupon-empty">
            <text class="coupon-empty-text">暂无可用卡券</text>
          </view>
          <view
            v-for="c in availableCoupons"
            :key="c.id"
            :class="['sheet-coupon-option', { active: coupon && coupon.id === c.id }]"
            @tap="selectCoupon(c)"
          >
            <view class="sheet-coupon-main">
              <view class="coupon-name-row">
                <text class="sheet-coupon-name">{{ c.name }}</text>
                <text class="coupon-discount">-¥{{ money(c.discount_amount) }}</text>
              </view>
              <text class="sheet-coupon-desc">{{ c.description || couponMetaText(c) }}</text>
            </view>
            <view class="coupon-radio">
              <view v-if="coupon && coupon.id === c.id" class="coupon-radio-dot" />
            </view>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script>
import { getCourseLessons, createCourseBooking } from '@/api/courseBooking'
import { getBalance } from '@/api/wallet'
import { getAvailableCouponsForBooking } from '@/api/coupons'
import { formatMoney } from '@/utils/formatters'
import {
  PAYMENT_POLL_INTERVAL,
  PAYMENT_POLL_MAX_ATTEMPTS,
} from '@/constants/wallet'
import { pollPaymentStatus } from '@/services/paymentPolling'

export default {
  data() {
    return {
      courseId: null,
      courseInfo: {},
      lessons: [],
      selectedLessonIds: [],
      bookingType: 'fixed',
      scheduleType: 'fixed',
      isFullPackage: false,
      lessonsExpanded: false,

      // Coupon
      coupon: null,
      couponDiscount: 0,
      availableCoupons: [],
      couponLoading: false,
      showCouponSheet: false,

      // Payment
      paymentMethod: 'balance',
      walletBalance: 0,
      submitting: false,

      // UI
      pageLoading: true,
      showSuccessModal: false,
      successInfo: null,

      // Polling
      paymentPollTimer: null,
    }
  },

  computed: {
    teacherName() {
      if (this.courseInfo.teacher) {
        return this.courseInfo.teacher.name || ''
      }
      return ''
    },

    currentUnitPrice() {
      return this.bookingType === 'fixed'
        ? this.courseInfo.price
        : this.courseInfo.custom_price
    },

    scheduleDesc() {
      if (this.courseInfo.schedule) {
        return this.courseInfo.schedule
      }
      return ''
    },

    fullPackageSaveAmount() {
      if (!this.courseInfo.full_package_price) return '0.00'
      const standardTotal = this.lessons.length * this.courseInfo.price
      const save = standardTotal - this.courseInfo.full_package_price
      return money(save > 0 ? save : 0)
    },

    visibleLessons() {
      if (this.lessonsExpanded || this.isFullPackage) {
        return this.lessons
      }
      return this.lessons.slice(0, 4)
    },

    priceSummary() {
      const count = this.selectedLessonIds.length
      const totalLessons = this.lessons.length
      const unitPrice = this.currentUnitPrice
      const couponDiscount = this.couponDiscount

      if (this.isFullPackage && this.courseInfo.full_package_price) {
        const originalPrice = money(this.courseInfo.full_package_price)
        const standardPrice = totalLessons * unitPrice
        const discountAmount = money(Math.max(0, standardPrice - this.courseInfo.full_package_price))
        const totalPrice = money(Math.max(0, this.courseInfo.full_package_price - couponDiscount))
        return { originalPrice, discountAmount, couponDiscount, totalPrice, unitPrice }
      }

      const originalPrice = money(count * unitPrice)
      const discountAmount = '0.00'
      const totalPrice = money(Math.max(0, count * unitPrice - couponDiscount))
      return { originalPrice, discountAmount, couponDiscount, totalPrice, unitPrice }
    },

    priceLabel() {
      const count = this.selectedLessonIds.length
      const unitPrice = this.currentUnitPrice
      if (this.isFullPackage && this.courseInfo.full_package_price) {
        return `全套课时（${this.lessons.length}课时）`
      }
      return `课程费（${count}课时 × ¥${unitPrice}）`
    },

    couponDiscountText() {
      return money(this.couponDiscount)
    },

    walletBalanceText() {
      return money(this.walletBalance)
    },

    isBalanceInsufficient() {
      return Number(this.walletBalance) < Number(this.priceSummary.totalPrice)
    },

    couponSummaryText() {
      if (this.coupon) return `已选择：${this.coupon.name}`
      if (this.availableCoupons.length) return `可用 ${this.availableCoupons.length} 张`
      return '暂无可用'
    },
  },

  onLoad(options) {
    this.courseId = options.course_id || options.id
    if (this.courseId) {
      this.loadCourseData()
    } else {
      uni.showToast({ title: '缺少课程参数', icon: 'none' })
    }
  },

  onUnload() {
    this.clearPaymentPollTimer()
  },

  methods: {
    async loadCourseData() {
      this.pageLoading = true
      try {
        const res = await getCourseLessons(this.courseId)
        this.courseInfo = res.course || res
        this.lessons = res.lessons || []

        await Promise.all([
          this.loadWalletBalance(),
          this.loadAvailableCoupons(),
        ])
      } catch (err) {
        uni.showToast({ title: '加载失败', icon: 'none' })
      } finally {
        this.pageLoading = false
      }
    },

    async loadWalletBalance() {
      try {
        const res = await getBalance()
        this.walletBalance = res?.balance || 0
      } catch {
        // silent
      }
    },

    async loadAvailableCoupons() {
      this.couponLoading = true
      try {
        const res = await getAvailableCouponsForBooking({
          course_id: this.courseId,
          booking_type: this.bookingType,
        })
        this.availableCoupons = Array.isArray(res?.items) ? res.items : []
      } catch {
        this.availableCoupons = []
      } finally {
        this.couponLoading = false
      }
    },

    toggleLesson(lessonId) {
      const idx = this.selectedLessonIds.indexOf(lessonId)
      if (idx > -1) {
        this.selectedLessonIds.splice(idx, 1)
      } else {
        this.selectedLessonIds.push(lessonId)
      }
      this.isFullPackage = this.selectedLessonIds.length === this.lessons.length
    },

    selectFullPackage() {
      this.selectedLessonIds = this.lessons.map(l => l.id)
      this.isFullPackage = true
      this.lessonsExpanded = true
      uni.showToast({ title: `已选择全套${this.lessons.length}课时，立省¥${this.fullPackageSaveAmount}`, icon: 'none' })
    },

    switchBookingType(type) {
      this.bookingType = type
      this.scheduleType = type
      this.loadAvailableCoupons()
    },

    selectPaymentMethod(method) {
      this.paymentMethod = method
    },

    openCouponSheet() {
      if (!this.availableCoupons.length && !this.couponLoading) {
        uni.showToast({ title: '暂无可用卡券', icon: 'none' })
        return
      }
      this.showCouponSheet = true
    },

    closeCouponSheet() {
      this.showCouponSheet = false
    },

    selectCoupon(c) {
      this.coupon = c
      this.couponDiscount = Number(c.discount_amount) || 0
      this.closeCouponSheet()
    },

    clearCouponAndClose() {
      this.coupon = null
      this.couponDiscount = 0
      this.closeCouponSheet()
    },

    async submitOrder() {
      if (this.submitting) return
      if (this.selectedLessonIds.length === 0) {
        uni.showToast({ title: '请至少选择一节课时', icon: 'none' })
        return
      }
      if (this.paymentMethod === 'balance' && this.isBalanceInsufficient) {
        uni.showToast({ title: '余额不足，请切换微信支付或先充值', icon: 'none' })
        return
      }

      this.submitting = true
      try {
        const res = await createCourseBooking({
          course_id: this.courseId,
          booking_type: this.bookingType,
          lesson_ids: this.selectedLessonIds,
          schedule_type: this.scheduleType,
          payment_method: this.paymentMethod,
          coupon_id: this.coupon?.id || null,
        })

        if (this.paymentMethod === 'wechat' && res.payment_params) {
          await this.requestWechatPayment(res.payment_params)
          const paidStatus = await this.pollPaymentResult(res.booking_id)
          if (!paidStatus) {
            uni.showToast({ title: '支付处理中，请稍后在订单中查看', icon: 'none' })
            return
          }
        }

        this.successInfo = res
        this.showSuccessModal = true

        if (this.paymentMethod === 'balance') {
          this.loadWalletBalance()
        }
      } catch (err) {
        if (this.isPaymentCancel(err)) {
          uni.showToast({ title: '支付已取消', icon: 'none' })
        } else if (err?.paymentFailed) {
          uni.showToast({ title: '支付失败，请重试', icon: 'none' })
        } else {
          uni.showToast({ title: err?.message || err?.detail || '下单失败', icon: 'none' })
        }
      } finally {
        this.submitting = false
      }
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

    async pollPaymentResult(bookingId) {
      if (!bookingId) return null
      return pollPaymentStatus({
        fetchStatus: () => getCourseLessons(this.courseId),
        isSuccess: () => false,
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

    isPaymentCancel(err) {
      const text = (err?.errMsg || err?.message || '').toLowerCase()
      return text.includes('cancel')
    },

    onDone() {
      this.showSuccessModal = false
      uni.switchTab({ url: '/pages/orders/index' })
    },

    goBack() {
      uni.navigateBack()
    },

    formatDuration(minutes) {
      if (!minutes) return ''
      if (minutes >= 60) {
        const h = Math.floor(minutes / 60)
        const m = minutes % 60
        return m > 0 ? `${h}小时${m}分钟` : `${h}小时`
      }
      return `${minutes}分钟`
    },

    money(value) {
      return money(value)
    },

    couponMetaText(c) {
      if (c.min_order_amount) {
        return `满 ¥${money(c.min_order_amount)} 可用`
      }
      return '当前预约可用'
    },
  },
}

function money(value) {
  return formatMoney(value)
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

/* Navigation Bar */
.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 24rpx;
  padding-top: env(safe-area-inset-top);
  background: $surface;
  border-bottom: 1rpx solid $border-color;
  position: sticky;
  top: 0;
  z-index: 50;
}

.nav-back {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-back-icon {
  font-size: 44rpx;
  color: $text-primary;
  line-height: 1;
}

.nav-title {
  font-size: 32rpx;
  font-weight: 600;
  color: $text-primary;
}

.nav-placeholder {
  width: 64rpx;
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

.course-card { animation-delay: 0s; }
.type-card { animation-delay: 0.05s; }
.lesson-card { animation-delay: 0.1s; }
.schedule-card { animation-delay: 0.12s; }
.coupon-card { animation-delay: 0.15s; }
.payment-card { animation-delay: 0.18s; }
.price-card { animation-delay: 0.2s; }

/* Section header */
.section-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 20rpx;
}

.section-bar {
  width: 8rpx;
  height: 28rpx;
  background: $primary;
  border-radius: 4rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
}

/* Course Info */
.course-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.course-cover {
  width: 112rpx;
  height: 112rpx;
  border-radius: 20rpx;
  flex-shrink: 0;
}

.course-cover-placeholder {
  background: $primary-light;
}

.course-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.course-name {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.teacher-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.teacher-avatar {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.teacher-avatar-placeholder {
  background: $primary-light;
}

.teacher-name {
  font-size: 24rpx;
  color: $text-secondary;
}

.course-price-wrap {
  flex-shrink: 0;
  text-align: right;
}

.course-price {
  font-size: 28rpx;
  font-weight: 700;
  color: $primary;
}

.course-price-unit {
  font-size: 20rpx;
  color: $text-muted;
}

/* Booking Type */
.type-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.type-item {
  border: 3rpx solid $border-color;
  border-radius: 24rpx;
  padding: 24rpx;
  transition: all 0.2s;
}

.type-item.active {
  border-color: $primary;
  background: $primary-soft;
}

.type-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.type-item-name {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.type-radio {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  border: 3rpx solid $border-color;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.type-radio.active {
  border-color: $primary;
}

.type-radio-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: $primary;
}

.type-item-desc {
  font-size: 20rpx;
  color: $text-muted;
  margin-bottom: 12rpx;
}

.type-item-price-row {
  display: flex;
  align-items: baseline;
}

.type-item-price {
  font-size: 28rpx;
  font-weight: 700;
  color: $primary;
}

.type-item-unit {
  font-size: 18rpx;
  color: $text-muted;
  font-weight: 400;
}

/* Lesson Selection */
.lesson-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.lesson-header .section-header {
  margin-bottom: 0;
}

.lesson-count {
  font-size: 24rpx;
  color: $text-muted;
}

.lesson-count-num {
  color: $primary;
  font-weight: 600;
}

.lesson-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx 16rpx;
  border-bottom: 1rpx solid rgba(0, 0, 0, 0.04);
  border-radius: 16rpx;
  transition: all 0.2s;
}

.lesson-item:last-of-type {
  border-bottom: none;
}

.lesson-item.selected {
  background: $primary-light;
}

.lesson-checkbox {
  width: 36rpx;
  height: 36rpx;
  border-radius: 8rpx;
  border: 3rpx solid $border-color;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.lesson-item.selected .lesson-checkbox {
  background: $primary;
  border-color: $primary;
}

.lesson-check-icon {
  font-size: 20rpx;
  color: #fff;
  font-weight: 700;
}

.lesson-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  background: $success-light;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.lesson-play-icon {
  font-size: 20rpx;
  color: $success;
}

.lesson-info {
  flex: 1;
  min-width: 0;
}

.lesson-title {
  font-size: 26rpx;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lesson-meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 6rpx;
}

.lesson-duration {
  font-size: 20rpx;
  color: $text-muted;
}

.lesson-status {
  font-size: 20rpx;
  color: $success;
}

.lesson-price {
  font-size: 26rpx;
  font-weight: 500;
  color: $text-primary;
  flex-shrink: 0;
}

/* Full package promo */
.full-package-bar {
  margin-top: 20rpx;
  background: linear-gradient(to right, rgba(79, 110, 247, 0.05), rgba(108, 92, 231, 0.05));
  border-radius: 20rpx;
  padding: 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.full-package-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.full-package-icon-wrap {
  width: 48rpx;
  height: 48rpx;
  border-radius: 14rpx;
  background: $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.full-package-icon-text {
  font-size: 24rpx;
  font-weight: 700;
  color: #fff;
}

.full-package-text {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.full-package-title {
  font-size: 24rpx;
  font-weight: 600;
  color: $text-primary;
}

.full-package-save {
  font-size: 20rpx;
  color: $text-muted;
}

.full-package-link {
  font-size: 24rpx;
  color: $primary;
  font-weight: 600;
}

/* Lessons expand toggle */
.lessons-expand-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  padding: 20rpx 0 4rpx;
}

.lessons-expand-text {
  font-size: 24rpx;
  color: $primary;
  font-weight: 500;
}

.lessons-expand-arrow {
  font-size: 24rpx;
  color: $primary;
  font-weight: 700;
  transform: rotate(90deg);
}

/* Schedule */
.schedule-fixed-box {
  background: $primary-soft;
  border-radius: 20rpx;
  padding: 24rpx;
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
}

.schedule-icon-wrap {
  width: 72rpx;
  height: 72rpx;
  border-radius: 16rpx;
  background: $primary-light;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.schedule-cal-icon {
  font-size: 32rpx;
}

.schedule-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.schedule-time-text {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.schedule-desc {
  font-size: 22rpx;
  color: $text-muted;
}

.schedule-custom-notice {
  background: $primary-soft;
  border-radius: 20rpx;
  padding: 24rpx;
}

.schedule-custom-text {
  font-size: 24rpx;
  color: $text-secondary;
}

/* Coupon */
.coupon-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 32rpx;
}

.coupon-row-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.coupon-row-right {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.coupon-row-title {
  font-size: 28rpx;
  color: $text-primary;
}

.coupon-row-muted {
  font-size: 24rpx;
  color: $text-muted;
}

.coupon-row-discount {
  font-size: 24rpx;
  font-weight: 600;
  color: #E64A19;
}

.chevron {
  font-size: 38rpx;
  line-height: 1;
  color: $text-muted;
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

/* Payment */
.payment-card {
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

.payment-option:active {
  background: $surface-soft;
}

.payment-option-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
  flex: 1;
}

.payment-option-right {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.payment-copy {
  min-width: 0;
}

.payment-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.payment-name {
  font-size: 28rpx;
  color: $text-primary;
}

.payment-balance {
  font-size: 24rpx;
  color: $text-muted;
}

.balance-warning {
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

.balance-icon {
  background: $primary-light;
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

.wechat-icon {
  background: #E8F5E9;
}

.wechat-mark {
  font-size: 24rpx;
  font-weight: 700;
  color: $success;
}

/* Price Summary */
.price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  margin-bottom: 14rpx;
}

.price-row:last-child {
  margin-bottom: 0;
}

.price-label {
  font-size: 28rpx;
  color: $text-secondary;
}

.price-value {
  font-size: 28rpx;
  color: $text-primary;
}

.price-value.discount {
  color: #E64A19;
}

.price-divider {
  border-top: 2rpx dashed $border-color;
  margin: 16rpx 0;
}

.price-total-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.total-value-wrap {
  display: flex;
  align-items: baseline;
}

.total-row {
  margin-top: 0;
}

.total-label {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.total-value {
  font-size: 44rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: -0.5rpx;
}

.total-symbol {
  font-size: 24rpx;
  font-weight: 600;
  margin-right: 2rpx;
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
  to { transform: rotate(360deg); }
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
  font-size: 24rpx;
  color: $text-muted;
  margin-bottom: 32rpx;
}

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
  font-size: 26rpx;
  color: $text-primary;
  text-align: right;
}

.summary-price {
  font-weight: 600;
  color: $primary;
}

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

/* Coupon Sheet */
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
  margin-bottom: 16rpx;
}

.sheet-coupon-option.active {
  border-color: $primary;
  background: $primary-soft;
}

.sheet-coupon-main {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.coupon-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.sheet-coupon-name {
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

.sheet-coupon-desc {
  font-size: 23rpx;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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

.sheet-coupon-list {
  max-height: 52vh;
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
</style>
