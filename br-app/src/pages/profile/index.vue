<template>
  <view class="page">
    <view v-if="userStore.isLoggedIn" class="profile">
      <view class="profile-header">
        <view class="settings-entry" @tap="navigateTo('/pages/settings/index')">
          <view class="settings-dot" />
          <view class="settings-dot" />
          <view class="settings-dot" />
        </view>
        <view class="avatar">
          <text class="avatar-text">{{ avatarText }}</text>
        </view>
        <view class="user-info">
          <view class="name-row">
            <text class="nickname">{{ userStore.nickname || '学习达人' }}</text>
            <view class="vip-badge">
              <text class="vip-badge-text">VIP会员</text>
            </view>
          </view>
          <text class="phone">已累计学习 {{ studyHoursText }}</text>
        </view>
      </view>

      <view class="stats-card">
        <view class="stat-item" @tap="navigateTo('/pages/wallet/transactions')">
          <text class="stat-value">¥{{ walletBalanceText }}</text>
          <text class="stat-label">钱包余额</text>
        </view>
        <view class="stat-divider" />
        <view class="stat-item" @tap="navigateTo('/pages/coupon/index')">
          <text class="stat-value orange">{{ availableCouponCount }}</text>
          <text class="stat-label">卡券</text>
        </view>
        <view class="stat-divider" />
        <view class="stat-item" @tap="navigateTo('/pages/study-record/index')">
          <text class="stat-value green">{{ studyHoursText }}</text>
          <text class="stat-label">学习时长</text>
        </view>
      </view>

      <view class="menu-list">
        <view class="menu-section-label">
          <text class="menu-section-text">学习服务</text>
        </view>
        <view class="menu-item" @tap="navigateTo('/pages/study-record/index')">
          <view class="menu-icon blue">
            <view class="history-icon" />
          </view>
          <text class="menu-item-text">学习记录</text>
          <text class="menu-item-meta">查看全部</text>
          <view class="icon icon-arrow-right menu-arrow" />
        </view>

        <view class="menu-divider" />
        <view class="menu-section-label">
          <text class="menu-section-text">会员服务</text>
        </view>
        <view class="menu-item" @tap="navigateTo('/pages/qrcode/index')">
          <view class="menu-icon purple">
            <view class="qr-icon" />
          </view>
          <text class="menu-item-text">我的学习码</text>
          <text class="menu-item-meta">到店核销</text>
          <view class="icon icon-arrow-right menu-arrow" />
        </view>
        <view class="menu-item" @tap="navigateTo('/pages/recharge/index')">
          <view class="menu-icon green">
            <view class="wallet-icon" />
          </view>
          <text class="menu-item-text">钱包充值</text>
          <view class="icon icon-arrow-right menu-arrow" />
        </view>
        <view class="menu-item" @tap="navigateTo('/pages/wallet/transactions')">
          <view class="menu-icon blue">
            <view class="bill-icon" />
          </view>
          <text class="menu-item-text">钱包流水</text>
          <text class="menu-item-meta">交易明细</text>
          <view class="icon icon-arrow-right menu-arrow" />
        </view>
        <view class="menu-item" @tap="navigateTo('/pages/coupon/index')">
          <view class="menu-icon orange">
            <view class="ticket-icon" />
          </view>
          <text class="menu-item-text">卡券包</text>
          <text class="menu-item-meta">{{ availableCouponCount }}张可用</text>
          <view class="icon icon-arrow-right menu-arrow" />
        </view>

        <view class="menu-divider" />
        <view class="menu-section-label">
          <text class="menu-section-text">其他</text>
        </view>
        <view class="menu-item" @tap="navigateTo('/pages/settings/index')">
          <view class="menu-icon gray">
            <view class="settings-icon" />
          </view>
          <text class="menu-item-text">设置</text>
          <view class="icon icon-arrow-right menu-arrow" />
        </view>
      </view>

      <view class="member-card">
        <view>
          <text class="member-title">升级超级会员</text>
          <text class="member-desc">享8折优惠 + 专属座位 + 优先预约</text>
        </view>
        <view class="member-action">
          <text class="member-action-text">立即开通</text>
        </view>
      </view>

      <button class="logout-btn" @tap="handleLogout">退出登录</button>
    </view>
    <view v-else class="not-logged-in">
      <text class="title">去K书</text>
      <text class="desc">专注学习，遇见更好的自己</text>
      <button class="login-btn" @tap="goLogin">去登录</button>
    </view>
  </view>
</template>

<script>
import { useUserStore } from '@/store/modules/user'
import { getCoupons } from '@/api/coupons'
import { getMonthlySummary } from '@/api/studyRecords'
import { getBalance } from '@/api/wallet'

export default {
  data() {
    return {
      userStore: useUserStore(),
      walletBalance: 0,
      availableCouponCount: 0,
      totalStudyHours: 0,
      profileRequestId: 0,
    }
  },
  computed: {
    avatarText() {
      return (this.userStore.nickname || this.userStore.phone || 'U').charAt(0).toUpperCase()
    },
    walletBalanceText() {
      return this.formatMoney(this.walletBalance)
    },
    studyHoursText() {
      return `${this.formatHours(this.totalStudyHours)}h`
    },
  },
  onShow() {
    if (this.userStore.isLoggedIn) {
      this.loadProfileStats()
    }
  },
  methods: {
    goLogin() {
      uni.navigateTo({ url: '/pages/login/login' })
    },
    async handleLogout() {
      await this.userStore.logout()
    },
    navigateTo(url) {
      uni.navigateTo({ url })
    },
    async loadProfileStats() {
      const requestId = ++this.profileRequestId
      const month = this.currentMonthString()
      const [balanceResult, couponResult, studyResult] = await Promise.allSettled([
        getBalance(),
        getCoupons('available'),
        getMonthlySummary({ month }),
      ])

      if (requestId !== this.profileRequestId) return

      this.walletBalance = balanceResult.status === 'fulfilled'
        ? (balanceResult.value?.balance || 0)
        : 0

      if (couponResult.status === 'fulfilled') {
        const coupons = Array.isArray(couponResult.value)
          ? couponResult.value
          : (couponResult.value?.items || [])
        this.availableCouponCount = coupons.length
      } else {
        this.availableCouponCount = 0
      }

      this.totalStudyHours = studyResult.status === 'fulfilled'
        ? (studyResult.value?.total_hours || 0)
        : 0
    },
    currentMonthString() {
      const now = new Date()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      return `${now.getFullYear()}-${month}`
    },
    formatMoney(value) {
      const number = Number(value)
      if (!Number.isFinite(number)) return '0.00'
      return number.toFixed(2)
    },
    formatHours(value) {
      const number = Number(value)
      if (!Number.isFinite(number)) return '0'
      return Number.isInteger(number) ? String(number) : number.toFixed(1).replace(/\.0$/, '')
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
}

.profile {
  padding-bottom: 40rpx;
}

.not-logged-in {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  gap: 24rpx;
}

.title {
  font-size: 48rpx;
  font-weight: 700;
  color: $text-primary;
}

.desc {
  font-size: 28rpx;
  color: $text-secondary;
}

.login-btn {
  margin-top: 40rpx;
  width: 400rpx;
  height: 88rpx;
  line-height: 88rpx;
  text-align: center;
  border-radius: 16rpx;
  font-size: 30rpx;
  background: linear-gradient(135deg, $primary, $purple);
  color: #fff;
  box-shadow: 0 8rpx 24rpx rgba(79, 110, 247, 0.25);
  border: none;

  &::after { border: none; }
}

.profile-header {
  position: relative;
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 68rpx 32rpx 76rpx;
  background: linear-gradient(180deg, $primary 0%, $purple 100%);
  overflow: hidden;
}

.profile-header::after {
  content: '';
  position: absolute;
  width: 240rpx;
  height: 240rpx;
  right: -80rpx;
  bottom: -100rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
}

.settings-entry {
  position: absolute;
  top: 28rpx;
  right: 32rpx;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5rpx;
  background: rgba(255, 255, 255, 0.12);
}

.settings-dot {
  width: 6rpx;
  height: 6rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.78);
}

.avatar {
  width: 128rpx;
  height: 128rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.18);
  border: 3rpx solid rgba(255, 255, 255, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.avatar-text {
  font-size: 44rpx;
  font-weight: 700;
  color: $white;
}

.user-info {
  position: relative;
  z-index: 1;
  min-width: 0;
  flex: 1;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.vip-badge {
  border-radius: 999rpx;
  padding: 4rpx 16rpx;
  background: #ffd666;
}

.vip-badge-text {
  font-size: 20rpx;
  font-weight: 600;
  color: #7a4a00;
}

.nickname {
  font-size: 36rpx;
  font-weight: 700;
  color: $white;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.phone {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.72);
  display: block;
  margin-top: 10rpx;
}

.stats-card {
  margin: -34rpx 28rpx 0;
  position: relative;
  z-index: 2;
  background: $white;
  border-radius: 28rpx;
  padding: 28rpx 0;
  box-shadow: 0 8rpx 26rpx rgba(79, 110, 247, 0.11);
  display: flex;
  align-items: center;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.stat-value {
  font-size: 32rpx;
  line-height: 1.1;
  font-weight: 700;
  color: $primary;
}

.stat-value.orange {
  color: #e67900;
}

.stat-value.green {
  color: $success;
}

.stat-label {
  font-size: 22rpx;
  color: $text-muted;
}

.stat-divider {
  width: 1rpx;
  height: 50rpx;
  background: rgba(45, 52, 54, 0.07);
}

.menu-list {
  margin-top: 24rpx;
  margin-left: 28rpx;
  margin-right: 28rpx;
  background: $white;
  border-radius: 28rpx;
  overflow: hidden;
  box-shadow: $shadow-sm;
}

.menu-section-label {
  padding: 22rpx 28rpx 6rpx;
}

.menu-section-text {
  font-size: 22rpx;
  font-weight: 600;
  color: $text-muted;
}

.menu-divider {
  height: 1rpx;
  background: rgba(45, 52, 54, 0.06);
  margin: 12rpx 28rpx;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 24rpx 28rpx;
  gap: 20rpx;
}

.menu-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.menu-icon.blue {
  background: $primary-light;
}

.menu-icon.green {
  background: rgba(7, 193, 96, 0.1);
}

.menu-icon.orange {
  background: rgba(255, 149, 0, 0.12);
}

.menu-icon.purple {
  background: rgba(108, 92, 231, 0.1);
}

.menu-icon.gray {
  background: rgba(99, 110, 114, 0.1);
}

.menu-item-text {
  flex: 1;
  font-size: 28rpx;
  color: $text-primary;
}

.menu-item-meta {
  font-size: 22rpx;
  color: $text-muted;
}

.menu-arrow {
  width: 24rpx;
  height: 24rpx;
  font-size: 24rpx;
  color: $text-muted;
}

.history-icon {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  border: 4rpx solid $primary;
  position: relative;
}

.history-icon::after {
  content: '';
  position: absolute;
  left: 13rpx;
  top: 5rpx;
  width: 4rpx;
  height: 13rpx;
  border-radius: 4rpx;
  background: $primary;
  transform-origin: bottom center;
  transform: rotate(-42deg);
}

.wallet-icon {
  width: 36rpx;
  height: 28rpx;
  border-radius: 7rpx;
  border: 4rpx solid $success;
  position: relative;
}

.wallet-icon::after {
  content: '';
  position: absolute;
  right: -4rpx;
  top: 7rpx;
  width: 14rpx;
  height: 10rpx;
  border-radius: 5rpx;
  background: $success;
}

.bill-icon {
  width: 34rpx;
  height: 40rpx;
  border-radius: 7rpx;
  border: 4rpx solid $primary;
  position: relative;
}

.bill-icon::before,
.bill-icon::after {
  content: '';
  position: absolute;
  left: 7rpx;
  right: 7rpx;
  height: 4rpx;
  border-radius: 4rpx;
  background: $primary;
}

.bill-icon::before {
  top: 10rpx;
}

.bill-icon::after {
  top: 22rpx;
}

.ticket-icon {
  width: 38rpx;
  height: 26rpx;
  border-radius: 8rpx;
  border: 4rpx solid #e67900;
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
  background: $white;
}

.ticket-icon::before {
  left: -8rpx;
}

.ticket-icon::after {
  right: -8rpx;
}

.qr-icon {
  width: 36rpx;
  height: 36rpx;
  border: 4rpx solid $purple;
  border-radius: 7rpx;
  position: relative;
}

.qr-icon::before,
.qr-icon::after {
  content: '';
  position: absolute;
  width: 8rpx;
  height: 8rpx;
  background: $purple;
  border-radius: 2rpx;
}

.qr-icon::before {
  left: 6rpx;
  top: 6rpx;
  box-shadow: 16rpx 0 0 $purple, 0 16rpx 0 $purple;
}

.qr-icon::after {
  right: 6rpx;
  bottom: 6rpx;
}

.settings-icon {
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  border: 5rpx solid $text-muted;
  position: relative;
}

.settings-icon::after {
  content: '';
  position: absolute;
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: $text-muted;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
}

.member-card {
  margin: 24rpx 28rpx 0;
  padding: 28rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #30236b 0%, $purple 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  overflow: hidden;
}

.member-title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: $white;
}

.member-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.68);
}

.member-action {
  height: 56rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: $white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.member-action-text {
  font-size: 22rpx;
  font-weight: 600;
  color: $primary;
}

.logout-btn {
  margin: 36rpx 28rpx 0;
  height: 88rpx;
  line-height: 88rpx;
  text-align: center;
  border-radius: 22rpx;
  font-size: 28rpx;
  background: $white;
  color: $danger;
  border: 1rpx solid rgba(255, 107, 107, 0.18);

  &::after { border: none; }
}
</style>
