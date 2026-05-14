<template>
  <view class="page">
    <scroll-view class="content-scroll" scroll-y>
      <view class="balance-card">
        <text class="balance-label">账户余额</text>
        <view v-if="loading" class="balance-skeleton main" />
        <text v-else class="balance-value">¥{{ formatMoney(balance) }}</text>
        <view v-if="loading" class="balance-skeleton sub" />
        <text v-else class="balance-total">累计充值 ¥{{ formatMoney(totalRecharged) }}</text>
      </view>

      <view class="section">
        <text class="section-title">选择充值金额</text>
        <view class="amount-grid">
          <view
            v-for="amount in amounts"
            :key="amount"
            :class="['amount-btn', { selected: selectedAmount === amount }]"
            @tap="selectAmount(amount)"
          >
            <text class="amount-text">¥{{ amount }}</text>
          </view>
          <view
            :class="['amount-btn', 'custom', { selected: isCustomAmount }]"
            @tap="showCustomAmountInput"
          >
            <text class="amount-text">{{ isCustomAmount ? `¥${selectedAmount}` : '自定义' }}</text>
          </view>
        </view>
      </view>

      <view class="payment-card">
        <text class="section-title">支付方式</text>
        <view class="payment-item" @tap="togglePayment('wechat')">
          <view class="payment-main">
            <view class="payment-icon wechat">
              <text class="payment-icon-text">微</text>
            </view>
            <text class="payment-name">微信支付</text>
          </view>
          <view :class="['radio', { active: paymentMethod === 'wechat' }]">
            <view v-if="paymentMethod === 'wechat'" class="radio-dot" />
          </view>
        </view>
        <view class="payment-divider" />
        <view class="payment-item" @tap="togglePayment('alipay')">
          <view class="payment-main">
            <view class="payment-icon alipay">
              <text class="payment-icon-text">支</text>
            </view>
            <text class="payment-name">支付宝</text>
          </view>
          <view :class="['radio', { active: paymentMethod === 'alipay' }]">
            <view v-if="paymentMethod === 'alipay'" class="radio-dot" />
          </view>
        </view>
      </view>

      <view class="promo-card">
        <view class="promo-row">
          <view class="promo-icon">
            <text class="promo-icon-text">券</text>
          </view>
          <input
            v-model.trim="promoCode"
            class="promo-input"
            placeholder="输入优惠码"
            placeholder-class="promo-placeholder"
            confirm-type="done"
            :disabled="submitting"
          />
          <button class="promo-btn" :disabled="submitting" @tap="redeemPromoCode">
            兑换
          </button>
        </view>
        <text v-if="promoInfo" class="promo-info">{{ promoText }}</text>
      </view>

      <view class="bottom-safe" />
    </scroll-view>

    <view class="bottom-bar">
      <button class="recharge-btn" :disabled="submitting" @tap="handleRecharge">
        {{ submitting ? '充值中...' : rechargeButtonText }}
      </button>
    </view>
  </view>
</template>

<script>
import {
  getBalance,
  createRechargeOrder,
  confirmPayment,
  redeemPromoCode as redeemPromoCodeApi,
} from '@/api/wallet'

const DEFAULT_AMOUNT = 50
const MIN_AMOUNT = 1
const MAX_AMOUNT = 9999

export default {
  data() {
    return {
      balance: 0,
      totalRecharged: 0,
      selectedAmount: DEFAULT_AMOUNT,
      paymentMethod: 'wechat',
      promoCode: '',
      promoInfo: null,
      loading: false,
      submitting: false,
      amounts: [30, 50, 100, 200, 500],
    }
  },

  computed: {
    isCustomAmount() {
      return !this.amounts.includes(Number(this.selectedAmount))
    },

    rechargeButtonText() {
      return `立即充值 ¥${this.formatAmount(this.selectedAmount)}`
    },

    promoText() {
      if (!this.promoInfo) return ''
      if (this.promoInfo.description) return this.promoInfo.description
      const bonus = this.promoInfo.bonus_amount || this.promoInfo.bonusAmount || 0
      return `充${this.formatAmount(this.selectedAmount)}送${this.formatAmount(bonus)}`
    },
  },

  onLoad() {
    this.loadBalance()
  },

  methods: {
    async loadBalance() {
      this.loading = true
      try {
        const data = await getBalance()
        this.balance = data.balance || 0
        this.totalRecharged = data.total_recharged || data.totalRecharged || 0
      } catch {
        uni.showToast({ title: '余额加载失败', icon: 'none' })
      } finally {
        this.loading = false
      }
    },

    selectAmount(amount) {
      this.selectedAmount = amount
    },

    showCustomAmountInput() {
      uni.showModal({
        title: '自定义金额',
        editable: true,
        placeholderText: '请输入1-9999元',
        success: (res) => {
          if (!res.confirm) return
          const inputValue = String(res.content || '').trim()
          const amount = Number(inputValue)
          if (!this.isValidAmount(amount, inputValue)) {
            uni.showToast({ title: '请输入1-9999的整数金额', icon: 'none' })
            return
          }
          this.selectedAmount = amount
        },
      })
    },

    isValidAmount(amount, rawValue) {
      return /^\d+$/.test(rawValue) && amount >= MIN_AMOUNT && amount <= MAX_AMOUNT
    },

    togglePayment(method) {
      this.paymentMethod = method
    },

    async redeemPromoCode() {
      if (!this.promoCode) {
        uni.showToast({ title: '请输入优惠码', icon: 'none' })
        return
      }
      try {
        const data = await redeemPromoCodeApi(this.promoCode)
        this.promoInfo = data
        uni.showToast({ title: '兑换成功' })
      } catch {
        this.promoInfo = null
        uni.showToast({ title: '优惠码无效或已使用', icon: 'none' })
      }
    },

    async handleRecharge() {
      if (this.submitting) return
      const amount = Number(this.selectedAmount)
      if (!this.isValidAmount(amount, String(this.selectedAmount))) {
        uni.showToast({ title: '请选择有效充值金额', icon: 'none' })
        return
      }

      this.submitting = true
      try {
        const payload = {
          amount,
          payment_method: this.paymentMethod,
        }
        if (this.promoCode) {
          payload.promo_code = this.promoCode
        }
        const order = await createRechargeOrder(payload)
        const orderId = order.order_id || order.orderId
        await confirmPayment(orderId)
        uni.showToast({ title: '充值成功' })
        this.promoInfo = null
        await this.loadBalance()
      } catch {
        uni.showToast({ title: '充值失败，请重试', icon: 'none' })
      } finally {
        this.submitting = false
      }
    },

    formatMoney(value) {
      const amount = Number(value)
      if (!Number.isFinite(amount)) return '0.00'
      return amount.toFixed(2)
    },

    formatAmount(value) {
      const amount = Number(value)
      if (!Number.isFinite(amount)) return '0'
      return Number.isInteger(amount) ? String(amount) : amount.toFixed(2).replace(/\.?0+$/, '')
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
}

.content-scroll {
  height: 100vh;
}

.balance-card {
  margin: 32rpx 32rpx 0;
  padding: 40rpx;
  border-radius: 32rpx;
  background: linear-gradient(135deg, $primary 0%, #6c5ce7 100%);
  color: $white;
  box-shadow: 0 18rpx 42rpx rgba(79, 110, 247, 0.22);
  display: flex;
  flex-direction: column;
}

.balance-label,
.balance-total {
  font-size: 24rpx;
  line-height: 34rpx;
  color: rgba(255, 255, 255, 0.68);
}

.balance-value {
  margin-top: 8rpx;
  font-size: 60rpx;
  line-height: 76rpx;
  font-weight: 700;
  color: $white;
}

.balance-total {
  margin-top: 12rpx;
}

.balance-skeleton {
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.22);
}

.balance-skeleton.main {
  width: 260rpx;
  height: 64rpx;
  margin-top: 16rpx;
}

.balance-skeleton.sub {
  width: 220rpx;
  height: 28rpx;
  margin-top: 22rpx;
}

.section {
  margin: 32rpx 32rpx 0;
}

.section-title {
  display: block;
  margin-bottom: 24rpx;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 600;
  color: $text-primary;
}

.amount-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24rpx;
}

.amount-btn {
  height: 96rpx;
  border-radius: 24rpx;
  background: $white;
  border: 2rpx solid transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 18rpx rgba(45, 52, 54, 0.04);
}

.amount-btn.selected {
  background: $primary-light;
  border-color: $primary;
  box-shadow: 0 8rpx 22rpx rgba(79, 110, 247, 0.14);
}

.amount-text {
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
  color: $text-primary;
}

.amount-btn.selected .amount-text {
  color: $primary;
  font-weight: 700;
}

.amount-btn.custom .amount-text {
  color: $text-secondary;
}

.amount-btn.custom.selected .amount-text {
  color: $primary;
}

.payment-card,
.promo-card {
  margin: 32rpx 32rpx 0;
  padding: 32rpx;
  border-radius: 32rpx;
  background: $white;
  box-shadow: 0 6rpx 20rpx rgba(45, 52, 54, 0.04);
}

.payment-item {
  min-height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.payment-main {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.payment-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.payment-icon.wechat {
  background: $success;
}

.payment-icon.alipay {
  background: $primary;
}

.payment-icon-text {
  font-size: 28rpx;
  line-height: 1;
  font-weight: 700;
  color: $white;
}

.payment-name {
  font-size: 28rpx;
  line-height: 40rpx;
  color: $text-primary;
}

.payment-divider {
  height: 1rpx;
  margin-left: 88rpx;
  background: rgba(45, 52, 54, 0.06);
}

.radio {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  border: 4rpx solid $text-muted;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.radio.active {
  border-color: $primary;
}

.radio-dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  background: $primary;
}

.promo-card {
  padding: 28rpx 32rpx;
}

.promo-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.promo-icon {
  width: 36rpx;
  height: 36rpx;
  border-radius: 10rpx;
  background: $primary-light;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.promo-icon-text {
  font-size: 20rpx;
  line-height: 1;
  color: $primary;
  font-weight: 700;
}

.promo-input {
  flex: 1;
  min-width: 0;
  height: 56rpx;
  font-size: 28rpx;
  color: $text-primary;
}

.promo-placeholder {
  color: $text-muted;
}

.promo-btn {
  flex-shrink: 0;
  height: 56rpx;
  line-height: 56rpx;
  padding: 0 28rpx;
  border-radius: 999rpx;
  background: $primary-light;
  color: $primary;
  font-size: 24rpx;
  font-weight: 600;
  border: none;
}

.promo-btn::after,
.recharge-btn::after {
  border: none;
}

.promo-btn[disabled],
.recharge-btn[disabled] {
  opacity: 0.62;
}

.promo-info {
  display: block;
  margin-top: 20rpx;
  padding: 16rpx 20rpx;
  border-radius: 16rpx;
  background: rgba(79, 110, 247, 0.08);
  color: $primary;
  font-size: 24rpx;
  line-height: 34rpx;
}

.bottom-safe {
  height: 184rpx;
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 24rpx 32rpx calc(24rpx + env(safe-area-inset-bottom));
  background: $white;
  box-shadow: 0 -4rpx 20rpx rgba(45, 52, 54, 0.06);
}

.recharge-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 999rpx;
  background: $primary;
  color: $white;
  font-size: 28rpx;
  font-weight: 700;
  box-shadow: 0 12rpx 26rpx rgba(79, 110, 247, 0.24);
  border: none;
}

.recharge-btn:active {
  background: $primary-dark;
}
</style>
