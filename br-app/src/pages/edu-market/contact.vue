<template>
  <!-- #ifdef H5 -->
  <view class="page">
    <view class="phone-section">
      <text class="phone-title">联系发布者</text>
      <text v-if="phone" class="phone-number">{{ phone }}</text>
      <view v-if="phone" class="phone-btn" @tap="callPhone">
        <text class="phone-btn-text">拨打电话</text>
      </view>
      <text v-else class="phone-empty">发布者暂未设置联系电话</text>
    </view>
    <view id="knocket-container" class="knocket-area" />
  </view>
  <!-- #endif -->
  <!-- #ifndef H5 -->
  <web-view :src="knocketUrl" @message="onWebViewMessage" />
  <!-- #endif -->
</template>

<script>
const KNOCKET_SDK_URL =
  'https://trtc.io/knocket-sdk/sdk.js?identifier=0ee9b993c7ff89bb61&v=1791511906929'

const KNOCKET_PAGE_URL = 'https://f4e.yichengpai.cn/knocket.html'

export default {
  data() {
    return {
      phone: '',
      knocketUrl: KNOCKET_PAGE_URL,
    }
  },

  onLoad(options) {
    this.phone = options.phone || ''
    // #ifdef H5
    this.$nextTick(() => this.loadKnocketSdk())
    // #endif
  },

  // #ifndef H5
  onShareAppMessage() {
    return { title: '联系发布者', path: '/pages/edu-market/index' }
  },
  // #endif

  methods: {
    callPhone() {
      if (this.phone) uni.makePhoneCall({ phoneNumber: this.phone })
    },

    // #ifdef H5
    loadKnocketSdk() {
      const script = document.createElement('script')
      script.src = KNOCKET_SDK_URL
      script.async = true
      document.head.appendChild(script)
    },
    // #endif

    // #ifndef H5
    onWebViewMessage() {},
    // #endif
  },
}
</script>

<!-- #ifdef H5 -->
<style lang="scss" scoped>
.page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: $bg-color;
}

.phone-section {
  padding: 48rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
  background: $surface;
  border-bottom: 2rpx solid $border-soft;
}

.phone-title {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
}

.phone-number {
  font-size: 40rpx;
  font-weight: 700;
  color: $primary;
  letter-spacing: 2rpx;
}

.phone-btn {
  margin-top: 8rpx;
  padding: 20rpx 80rpx;
  background: $primary;
  border-radius: 999rpx;
}

.phone-btn-text {
  font-size: 30rpx;
  font-weight: 700;
  color: $white;
}

.phone-empty {
  font-size: 28rpx;
  color: $text-muted;
}

.knocket-area {
  flex: 1;
}
</style>
<!-- #endif -->
