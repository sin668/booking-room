<template>
  <view class="placeholder">
    <text class="placeholder-text">预约</text>
    <text class="placeholder-desc">功能开发中...</text>
  </view>
</template>

<script>
export default {}
</script>

<style lang="scss" scoped>
.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
}
.placeholder-text {
  font-size: 36rpx;
  font-weight: 600;
  color: $text-primary;
}
.placeholder-desc {
  margin-top: 16rpx;
  font-size: 28rpx;
  color: $text-muted;
}
</style>
