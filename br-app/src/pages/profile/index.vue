<template>
  <view class="page">
    <view v-if="userStore.isLoggedIn" class="profile">
      <view class="profile-header">
        <view class="avatar">
          <text class="avatar-text">{{ avatarText }}</text>
        </view>
        <view class="user-info">
          <text class="nickname">{{ userStore.nickname || '用户' }}</text>
          <text class="phone">{{ userStore.phone }}</text>
        </view>
      </view>
      <view class="menu-list">
        <view class="menu-item" @tap="navigateTo('/pages/coupon/index')">
          <text class="menu-item-text">卡券包</text>
          <text class="menu-item-arrow">></text>
        </view>
        <view class="menu-item" @tap="navigateTo('/pages/recharge/index')">
          <text class="menu-item-text">钱包充值</text>
          <text class="menu-item-arrow">></text>
        </view>
        <view class="menu-item" @tap="navigateTo('/pages/study-record/index')">
          <text class="menu-item-text">学习记录</text>
          <text class="menu-item-arrow">></text>
        </view>
        <view class="menu-item" @tap="navigateTo('/pages/settings/index')">
          <text class="menu-item-text">设置</text>
          <text class="menu-item-arrow">></text>
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

export default {
  data() {
    return {
      userStore: useUserStore(),
    }
  },
  computed: {
    avatarText() {
      return (this.userStore.nickname || this.userStore.phone || 'U').charAt(0).toUpperCase()
    },
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
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
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
  display: flex;
  align-items: center;
  padding: 60rpx 40rpx;
  background: #fff;
}

.avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, $primary, $purple);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-text {
  font-size: 44rpx;
  font-weight: 700;
  color: #fff;
}

.user-info {
  margin-left: 28rpx;
}

.nickname {
  font-size: 34rpx;
  font-weight: 600;
  color: $text-primary;
  display: block;
}

.phone {
  font-size: 26rpx;
  color: $text-secondary;
  display: block;
  margin-top: 6rpx;
}

.menu-list {
  margin-top: 24rpx;
  background: #fff;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx 40rpx;
  border-bottom: 1rpx solid $border-color;

  &:last-child { border-bottom: none; }
}

.menu-item-text {
  font-size: 30rpx;
  color: $text-primary;
}

.menu-item-arrow {
  font-size: 28rpx;
  color: $text-muted;
}

.logout-btn {
  margin: 60rpx 40rpx 0;
  height: 88rpx;
  line-height: 88rpx;
  text-align: center;
  border-radius: 16rpx;
  font-size: 30rpx;
  background: #fff;
  color: $danger;
  border: 2rpx solid $border-color;

  &::after { border: none; }
}
</style>
