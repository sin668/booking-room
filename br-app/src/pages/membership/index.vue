<template>
  <view class="page">
    <view class="hero">
      <text class="eyebrow">SUPER VIP</text>
      <text class="title">超级会员</text>
      <text class="subtitle">专注学习时，每一次预约都更划算。</text>
    </view>

    <view class="benefit-list">
      <view v-for="item in benefits" :key="item.title" class="benefit-item">
        <view class="benefit-icon">
          <text class="benefit-icon-text">{{ item.icon }}</text>
        </view>
        <view class="benefit-main">
          <text class="benefit-title">{{ item.title }}</text>
          <text class="benefit-desc">{{ item.desc }}</text>
        </view>
      </view>
    </view>

    <view class="bottom-bar">
      <button class="open-btn" :disabled="userStore.isVip" @tap="handleOpenVip">
        {{ userStore.isVip ? '已是超级会员' : '立即开通 - 充值100元起' }}
      </button>
    </view>
  </view>
</template>

<script>
import { useUserStore } from '@/store/modules/user'

export default {
  data() {
    return {
      userStore: useUserStore(),
      benefits: [
        { icon: '8', title: '8折优惠', desc: 'VIP 专属折扣券自动发放至卡券包' },
        { icon: '座', title: '专属座位', desc: '支持 VIP 专享座位和卡券权益' },
        { icon: '先', title: '优先预约', desc: '重要时段预约体验更稳定' },
      ],
    }
  },

  onShow() {
    if (this.userStore.isLoggedIn) {
      this.userStore.fetchUserInfo().catch(() => {})
    }
  },

  methods: {
    handleOpenVip() {
      if (this.userStore.isVip) return
      if (!this.userStore.isLoggedIn) {
        uni.navigateTo({ url: '/pages/login/login' })
        return
      }
      uni.navigateTo({ url: '/pages/recharge/index?amount=100&source=vip' })
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  padding: 32rpx 32rpx 180rpx;
  background: $bg-color;
  box-sizing: border-box;
}

.hero {
  min-height: 360rpx;
  padding: 48rpx 40rpx;
  border-radius: 32rpx;
  background: linear-gradient(135deg, #232946 0%, #4f6ef7 56%, #00b894 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-shadow: 0 18rpx 44rpx rgba(35, 41, 70, 0.22);
}

.eyebrow {
  font-size: 22rpx;
  line-height: 30rpx;
  color: rgba(255, 255, 255, 0.72);
  font-weight: 700;
}

.title {
  margin-top: 20rpx;
  font-size: 56rpx;
  line-height: 72rpx;
  color: $white;
  font-weight: 800;
}

.subtitle {
  margin-top: 16rpx;
  font-size: 26rpx;
  line-height: 38rpx;
  color: rgba(255, 255, 255, 0.76);
}

.benefit-list {
  margin-top: 32rpx;
  border-radius: 28rpx;
  background: $white;
  overflow: hidden;
  box-shadow: $shadow-sm;
}

.benefit-item {
  min-height: 132rpx;
  padding: 26rpx 28rpx;
  display: flex;
  align-items: center;
  gap: 24rpx;
  border-top: 1rpx solid rgba(45, 52, 54, 0.06);
}

.benefit-item:first-child {
  border-top: none;
}

.benefit-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 22rpx;
  background: rgba(79, 110, 247, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.benefit-icon-text {
  font-size: 28rpx;
  line-height: 1;
  font-weight: 800;
  color: $primary;
}

.benefit-main {
  flex: 1;
  min-width: 0;
}

.benefit-title {
  display: block;
  font-size: 30rpx;
  line-height: 40rpx;
  font-weight: 700;
  color: $text-primary;
}

.benefit-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 34rpx;
  color: $text-secondary;
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 24rpx 32rpx calc(24rpx + env(safe-area-inset-bottom));
  background: rgba(245, 246, 250, 0.96);
}

.open-btn {
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 24rpx;
  background: $primary;
  color: $white;
  font-size: 28rpx;
  font-weight: 700;
  border: none;
}

.open-btn::after {
  border: none;
}

.open-btn[disabled] {
  background: $text-muted;
  color: $white;
}
</style>
