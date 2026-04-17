<template>
  <view class="container">
    <view v-if="userStore.isLoggedIn" class="logged-in">
      <text class="welcome">欢迎，{{ userStore.nickname || '用户' }}</text>
      <text class="phone">{{ userStore.phone }}</text>
      <button class="btn" @tap="handleLogout">退出登录</button>
    </view>
    <view v-else class="logged-out">
      <text class="title">去K书</text>
      <text class="desc">专注学习，遇见更好的自己</text>
      <button class="btn btn-primary" @tap="goLogin">去登录</button>
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
  methods: {
    goLogin() {
      uni.navigateTo({ url: '/pages/login/login' })
    },
    async handleLogout() {
      await this.userStore.logout()
    },
  },
}
</script>

<style lang="scss" scoped>
.container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  padding: 0 60rpx;
}

.logged-in,
.logged-out {
  display: flex;
  flex-direction: column;
  align-items: center;
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

.welcome {
  font-size: 36rpx;
  font-weight: 600;
  color: $text-primary;
}

.phone {
  font-size: 28rpx;
  color: $text-secondary;
}

.btn {
  margin-top: 40rpx;
  width: 400rpx;
  height: 88rpx;
  line-height: 88rpx;
  text-align: center;
  border-radius: 16rpx;
  font-size: 30rpx;
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, $primary, $purple);
  color: $white;
  box-shadow: 0 8rpx 24rpx rgba(79, 110, 247, 0.25);
}

.btn-primary::after {
  border: none;
}

.btn:not(.btn-primary) {
  background: $white;
  color: $text-secondary;
  border: 2rpx solid $border-color;
}
</style>
