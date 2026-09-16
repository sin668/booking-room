<template>
  <view class="page">
    <!-- 状态栏 + 导航栏（悬浮在 hero 图上） -->
    <view class="nav-overlay" :style="{ height: statusBarHeight + 'px' }" />
    <view class="nav-bar">
      <view class="nav-btn" @tap="goBack">
        <view class="nav-back-arrow" />
      </view>
      <text class="nav-title-text">详情</text>
    </view>

    <scroll-view v-if="loaded" class="content" scroll-y>
      <!-- Hero 图 -->
      <view class="hero">
        <image
          v-if="coverImage"
          class="hero-img"
          :src="coverImage"
          mode="aspectFill"
          @tap="previewImage(coverImage)"
        />
        <view v-else :class="['hero-ph', `ph-${detail.listing_type}`]">
          <view class="icon hero-ph-icon" :class="typeMeta.icon" />
          <text v-if="detail.subject" class="hero-ph-subject">{{ detail.subject }}</text>
        </view>
      </view>

      <!-- 信息卡 -->
      <view class="info-card">
        <view class="info-tags">
          <view :class="['type-badge', `badge-${detail.listing_type}`]">
            <view class="icon type-badge-icon" :class="typeMeta.icon" />
            <text class="type-badge-text">{{ typeMeta.label }}</text>
          </view>
          <view v-for="cb in certBadges" :key="cb.text" class="cert-badge">
            <view class="icon icon-shield-check cert-badge-icon" :class="cb.cls" />
            <text class="cert-badge-text">{{ cb.text }}</text>
          </view>
        </view>

        <text class="info-title">{{ detail.title }}</text>

        <view class="info-price-row">
          <template v-if="detail.price">
            <text class="info-price-symbol">¥</text>
            <text class="info-price">{{ formatPrice(detail.price) }}</text>
            <text v-if="detail.price_unit" class="info-price-unit">{{ detail.price_unit }}</text>
          </template>
          <text v-else class="info-price-neg">价格面议</text>
        </view>

        <view class="info-meta">
          <view v-if="detail.area" class="meta-item">
            <view class="icon icon-location meta-icon" />
            <text class="meta-text">{{ detail.area }}</text>
          </view>
          <view v-if="detail.teaching_mode" class="meta-item">
            <view class="icon icon-user meta-icon" />
            <text class="meta-text">{{ detail.teaching_mode }}</text>
          </view>
          <view class="meta-item">
            <view class="icon icon-eye meta-icon" />
            <text class="meta-text">{{ detail.view_count || 0 }}次浏览</text>
          </view>
        </view>
      </view>

      <!-- 发布者卡片 -->
      <view class="block-card">
        <view class="publisher">
          <image
            v-if="detail.publisher_avatar"
            class="publisher-avatar"
            :src="detail.publisher_avatar"
            mode="aspectFill"
          />
          <view v-else class="publisher-avatar-ph">
            <view class="icon icon-user publisher-avatar-icon" />
          </view>
          <view class="publisher-info">
            <view class="publisher-name-row">
              <text class="publisher-name">{{ detail.publisher_nickname || '匿名用户' }}</text>
              <view v-if="certBadges.length" class="publisher-cert">
                <text class="publisher-cert-text">已认证</text>
              </view>
            </view>
            <text class="publisher-sub">{{ publisherRoleText }}</text>
          </view>
        </view>
      </view>

      <!-- 详细介绍 -->
      <view v-if="detail.description" class="block-card">
        <text class="block-title">详细介绍</text>
        <text class="block-desc">{{ detail.description }}</text>
        <view v-if="detail.subject" class="tag-row">
          <text class="tag">{{ detail.subject }}</text>
          <text v-if="detail.teaching_mode" class="tag">{{ detail.teaching_mode }}</text>
        </view>
      </view>

      <!-- 可授课时间 -->
      <view v-if="detail.available_times && detail.available_times.length" class="block-card">
        <text class="block-title">{{ detail.listing_type === 'demand' ? '期望时间' : '可授课时间' }}</text>
        <view class="time-row">
          <text v-for="t in detail.available_times" :key="t" class="time-chip">{{ t }}</text>
        </view>
      </view>

      <!-- 图片集 -->
      <view v-if="detail.images && detail.images.length > 1" class="block-card">
        <text class="block-title">相关图片</text>
        <view class="gallery">
          <image
            v-for="img in detail.images"
            :key="img"
            class="gallery-img"
            :src="img"
            mode="aspectFill"
            @tap="previewImage(img)"
          />
        </view>
      </view>

      <view class="bottom-space" />
    </scroll-view>

    <!-- 底部操作栏 -->
    <view v-if="loaded" class="action-bar">
      <view class="action-ico" @tap="onConsult">
        <view class="icon icon-eye-off action-ico-icon" />
        <text class="action-ico-text">咨询</text>
      </view>
      <view class="action-primary" @tap="onContact">
        <text class="action-primary-text">立即联系</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getEduListingDetail } from '@/api/eduMarket'
import { formatErrorDetail } from '@/utils/formatters'

const TYPE_META = {
  tutor: { label: '家教', icon: 'icon-graduation-cap', role: '个人家教' },
  training: { label: '培训班', icon: 'icon-chalkboard-user', role: '培训机构/老师' },
  demand: { label: '求教', icon: 'icon-user', role: '求学者' },
}

export default {
  data() {
    return {
      statusBarHeight: 0,
      listingId: null,
      detail: {},
      loaded: false,
    }
  },

  computed: {
    typeMeta() {
      return TYPE_META[this.detail.listing_type] || TYPE_META.demand
    },
    publisherRoleText() {
      return this.typeMeta.role
    },
    coverImage() {
      return this.detail.images && this.detail.images.length ? this.detail.images[0] : ''
    },
    certBadges() {
      const badges = []
      if (this.detail.publisher_education_verified) badges.push({ text: '学历认证', cls: 'cert-edu' })
      if (this.detail.publisher_teacher_verified) badges.push({ text: '教师资格', cls: 'cert-tea' })
      return badges
    },
  },

  onLoad(options) {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
    const query = options || {}
    this.listingId = query.id ? Number(query.id) : null
    if (!this.listingId) {
      uni.showToast({ title: '缺少信息编号', icon: 'none' })
      setTimeout(() => uni.navigateBack(), 800)
      return
    }
    this.loadDetail()
  },

  methods: {
    formatPrice(price) {
      const num = Number(price)
      if (!Number.isFinite(num)) return ''
      return Number.isInteger(num) ? String(num) : num.toFixed(2).replace(/\.?0+$/, '')
    },

    async loadDetail() {
      try {
        this.detail = await getEduListingDetail(this.listingId)
      } catch (error) {
        uni.showToast({ title: formatErrorDetail(error, '加载失败'), icon: 'none' })
      } finally {
        this.loaded = true
      }
    },

    previewImage(current) {
      const urls = this.detail.images || []
      if (!urls.length) return
      uni.previewImage({ current, urls })
    },

    onConsult() {
      uni.showToast({ title: '可在平台内与对方沟通', icon: 'none' })
    },

    onContact() {
      uni.showToast({ title: '平台沟通功能即将上线', icon: 'none' })
    },

    goBack() {
      uni.navigateBack()
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: $bg-color;
}

/* ── 导航 ── */
.nav-overlay {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12rpx);
  flex-shrink: 0;
}

.nav-bar {
  display: flex;
  align-items: center;
  height: 88rpx;
  padding: 0 28rpx;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12rpx);
  position: relative;
  flex-shrink: 0;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06), 0 1rpx 0 rgba(0, 0, 0, 0.04);
}

.nav-btn {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.nav-btn:active {
  background: $primary-soft;
  transform: scale(0.95);
}

.nav-back-arrow {
  width: 20rpx;
  height: 20rpx;
  border-left: 4rpx solid $text-primary;
  border-bottom: 4rpx solid $text-primary;
  transform: rotate(45deg);
}

.nav-title-text {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  font-size: 32rpx;
  font-weight: 700;
  color: $text-primary;
}

.content {
  flex: 1;
  height: 0;
}

/* ── Hero ── */
.hero {
  width: 100%;
  height: 460rpx;
  overflow: hidden;
  background: linear-gradient(135deg, $surface-soft 0%, $bg-color 100%);
  position: relative;
}

.hero-img {
  width: 100%;
  height: 460rpx;
}

.hero-ph {
  width: 100%;
  height: 460rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
}

.ph-tutor {
  background: linear-gradient(135deg, $primary-soft 0%, rgba($primary, 0.2) 100%);
}

.ph-training {
  background: linear-gradient(135deg, $primary-soft 0%, rgba($purple, 0.2) 100%);
}

.ph-demand {
  background: linear-gradient(135deg, $primary-soft 0%, rgba($orange, 0.2) 100%);
}

.hero-ph-icon {
  font-size: 120rpx;
  opacity: 0.55;
  color: $primary;
}

.ph-tutor .hero-ph-icon {
  color: $primary;
}

.ph-training .hero-ph-icon {
  color: $purple;
}

.ph-demand .hero-ph-icon {
  color: $orange;
}

.hero-ph-subject {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-secondary;
  opacity: 0.85;
  letter-spacing: 0.5rpx;
}

/* ── 信息卡 ── */
.info-card {
  position: relative;
  z-index: 10;
  margin-top: -32rpx;
  padding: 36rpx 28rpx 32rpx;
  background: $surface;
  border-radius: 32rpx 32rpx 0 0;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.08);
}

.info-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 14rpx;
}

.type-badge {
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.08);
  background: $primary-light;
}

.badge-tutor {
  background: rgba(79, 110, 247, 0.92);
}

.badge-training {
  background: rgba(108, 92, 231, 0.92);
}

.badge-demand {
  background: rgba(255, 140, 0, 0.92);
}

.type-badge-icon {
  font-size: 20rpx;
  color: $white;
}

.type-badge-text {
  font-size: 21rpx;
  font-weight: 600;
  color: $white;
  letter-spacing: 0.3rpx;
}

.cert-badge {
  display: flex;
  align-items: center;
  gap: 5rpx;
  padding: 6rpx 12rpx;
  background: $primary-soft;
  border-radius: 8rpx;
}

.cert-badge-icon {
  font-size: 20rpx;
}

.cert-edu {
  color: $orange;
}

.cert-tea {
  color: $success;
}

.cert-badge-text {
  font-size: 20rpx;
  color: $text-secondary;
  font-weight: 500;
}

.info-title {
  display: block;
  margin-top: 20rpx;
  font-size: 38rpx;
  font-weight: 700;
  line-height: 1.45;
  color: $text-primary;
  letter-spacing: 0.3rpx;
}

.info-price-row {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
  margin-top: 18rpx;
}

.info-price-symbol {
  font-size: 28rpx;
  font-weight: 700;
  color: $danger;
}

.info-price {
  font-size: 48rpx;
  font-weight: 800;
  color: $danger;
  line-height: 1;
  letter-spacing: -0.5rpx;
}

.info-price-unit {
  font-size: 22rpx;
  color: $text-muted;
  margin-left: 4rpx;
}

.info-price-neg {
  font-size: 36rpx;
  font-weight: 700;
  color: $danger;
}

.info-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 32rpx;
  margin-top: 24rpx;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.meta-icon {
  font-size: 22rpx;
  color: $primary;
}

.meta-text {
  font-size: 22rpx;
  color: $text-secondary;
  font-weight: 500;
}

/* ── 通用块卡片 ── */
.block-card {
  margin: 20rpx 24rpx 0;
  padding: 32rpx;
  background: $surface;
  border-radius: 28rpx;
  box-shadow: $shadow-card;
}

.block-title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: 18rpx;
  letter-spacing: 0.3rpx;
}

.block-desc {
  display: block;
  font-size: 27rpx;
  line-height: 1.8;
  color: $text-secondary;
  letter-spacing: 0.2rpx;
}

/* ── 发布者 ── */
.publisher {
  display: flex;
  align-items: center;
  gap: 22rpx;
}

.publisher-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  border: 3rpx solid $border-soft;
  flex-shrink: 0;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.12);
}

.publisher-avatar-ph {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: $primary-soft;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 3rpx solid $border-soft;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.08);
}

.publisher-avatar-icon {
  font-size: 48rpx;
  color: $text-muted;
}

.publisher-info {
  flex: 1;
  min-width: 0;
}

.publisher-name-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.publisher-name {
  font-size: 28rpx;
  font-weight: 700;
  color: $text-primary;
  letter-spacing: 0.3rpx;
}

.publisher-cert {
  padding: 4rpx 14rpx;
  background: $orange-light;
  border: 2rpx solid rgba($orange, 0.2);
  border-radius: 10rpx;
  box-shadow: 0 2rpx 8rpx rgba($orange, 0.1);
}

.publisher-cert-text {
  font-size: 18rpx;
  color: #92400E;
  font-weight: 600;
}

.publisher-sub {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $text-muted;
  font-weight: 500;
}

/* ── 标签 ── */
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 22rpx;
}

.tag {
  padding: 10rpx 22rpx;
  background: $bg-color;
  border: 2rpx solid $border-soft;
  border-radius: 12rpx;
  font-size: 22rpx;
  color: $text-secondary;
  font-weight: 500;
}

.time-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
}

.time-chip {
  padding: 12rpx 24rpx;
  background: $primary-light;
  border: 2rpx solid rgba($primary, 0.2);
  border-radius: 12rpx;
  font-size: 22rpx;
  color: $primary;
  font-weight: 600;
  box-shadow: 0 2rpx 8rpx rgba($primary, 0.08);
}

/* ── 图片集 ── */
.gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.gallery-img {
  width: 210rpx;
  height: 210rpx;
  border-radius: 18rpx;
  background: $bg-color;
  border: 2rpx solid $border-soft;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}

/* ── 底部操作栏 ── */
.action-bar {
  display: flex;
  align-items: center;
  gap: 28rpx;
  flex-shrink: 0;
  padding: 18rpx 28rpx;
  padding-bottom: calc(18rpx + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(12rpx);
  border-top: 2rpx solid $border-soft;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.08);
}

.action-ico {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  cursor: pointer;
  padding: 8rpx;
  border-radius: 12rpx;
  transition: all 0.2s ease;
}

.action-ico:active {
  background: $primary-soft;
  transform: scale(0.95);
}

.action-ico-icon {
  font-size: 34rpx;
  color: $text-muted;
}

.action-ico-text {
  font-size: 18rpx;
  color: $text-muted;
  font-weight: 500;
}

.action-primary {
  flex: 1;
  height: 92rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $primary;
  border-radius: 999rpx;
  box-shadow: 0 8rpx 24rpx rgba($primary, 0.28), inset 0 2rpx 0 rgba(255, 255, 255, 0.2);
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.action-primary:active {
  transform: scale(0.97);
  box-shadow: 0 4rpx 16rpx rgba($primary, 0.24);
}

.action-primary-text {
  font-size: 30rpx;
  font-weight: 700;
  color: $white;
  letter-spacing: 0.5rpx;
}

.bottom-space {
  height: 40rpx;
}
</style>
