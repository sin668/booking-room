<template>
  <view class="page">
    <scroll-view class="content" scroll-y>
      <view v-if="loading" class="state-wrap">
        <text class="state-text">活动加载中...</text>
      </view>

      <view v-else-if="loadError" class="state-wrap">
        <text class="state-text">活动加载失败，请重试</text>
        <view class="retry-btn" @tap="loadActivityDetail">
          <text class="retry-btn-text">重新加载</text>
        </view>
      </view>

      <template v-else>
        <image
          v-if="activity.cover_image"
          class="hero-cover"
          :src="activity.cover_image"
          mode="aspectFill"
        />

        <view class="header-section">
          <text class="activity-title">{{ activity.title || '活动详情' }}</text>
          <text v-if="activity.description" class="activity-desc">{{ activity.description }}</text>
          <view class="participant-row">
            <text class="participant-text">已有{{ participantCount }}人参与</text>
          </view>
        </view>

        <view v-if="hasContent" class="content-section">
          <text class="section-title">活动介绍</text>
          <rich-text class="rich-content" :nodes="activity.content_html" />
        </view>

        <view v-if="activityCoupons.length > 0" class="coupon-section">
          <text class="section-title">活动卡券</text>

          <view v-if="activityCoupons.length === 0" class="empty-coupons">
            <text class="empty-text">暂无可领取卡券</text>
          </view>

          <view
            v-for="item in activityCoupons"
            :key="item.id"
            class="coupon-card"
          >
            <view class="coupon-main">
              <view class="coupon-info">
                <text class="coupon-title">{{ couponDisplayTitle(item) }}</text>
                <text v-if="couponDisplayDescription(item)" class="coupon-desc">
                  {{ couponDisplayDescription(item) }}
                </text>
                <view class="coupon-meta">
                  <text class="coupon-tag">{{ typeText(item.coupon?.type) }}</text>
                  <text class="coupon-rule">{{ couponRuleText(item.coupon) }}</text>
                </view>
              </view>
              <view
                :class="['claim-btn', { disabled: !canClaim(item) || claimingId === item.id }]"
                @tap="onClaimCoupon(item)"
              >
                <text class="claim-btn-text">
                  {{ claimingId === item.id ? '领取中' : claimButtonText(item) }}
                </text>
              </view>
            </view>

            <view class="coupon-extra">
              <text class="coupon-extra-text">{{ validityText(item.coupon) }}</text>
              <text class="coupon-extra-text">{{ stockText(item) }}</text>
              <text class="coupon-extra-text">每人限领{{ item.per_user_limit || 1 }}张</text>
            </view>
          </view>
        </view>

        <view class="bottom-safe" />
      </template>
    </scroll-view>
  </view>
</template>

<script>
import { claimActivityCoupon, getActivityDetail } from '@/api/activities'
import { getToken } from '@/utils/request'

const TYPE_TEXT = {
  amount_off: '立减券',
  threshold_amount_off: '满减券',
  percentage_off: '折扣券',
}

const STATUS_TEXT = {
  available: '立即领取',
  claimed: '已领取',
  limit_reached: '已领取',
  sold_out: '已抢光',
  not_started: '未开始',
  ended: '已结束',
  disabled: '已结束',
}

export default {
  data() {
    return {
      activityId: '',
      activity: {},
      loading: true,
      loadError: false,
      claimingId: null,
      requestId: 0,
    }
  },

  computed: {
    activityCoupons() {
      return Array.isArray(this.activity.activity_coupons) ? this.activity.activity_coupons : []
    },

    hasContent() {
      return !!String(this.activity.content_html || '').trim()
    },

    participantCount() {
      const count = Number(this.activity.participant_count || 0)
      return Number.isFinite(count) ? count : 0
    },
  },

  onLoad(options) {
    this.activityId = options.id || options.activity_id || ''
    this.loadActivityDetail()
  },

  methods: {
    async loadActivityDetail() {
      if (!this.activityId) {
        this.loading = false
        this.loadError = true
        uni.showToast({ title: '活动不存在', icon: 'none' })
        return
      }

      const requestId = ++this.requestId
      this.loading = true
      this.loadError = false
      try {
        const data = await getActivityDetail(this.activityId)
        if (requestId !== this.requestId) return
        this.activity = data || {}
      } catch {
        if (requestId !== this.requestId) return
        this.activity = {}
        this.loadError = true
      } finally {
        if (requestId === this.requestId) {
          this.loading = false
        }
      }
    },

    async refreshDetailSilently() {
      try {
        const data = await getActivityDetail(this.activityId)
        this.activity = data || {}
      } catch {
        // 刷新失败时保留当前页面数据，避免把用户刚看到的错误状态清空。
      }
    },

    async onClaimCoupon(item) {
      if (!item?.id || this.claimingId) return

      if (!getToken()) {
        uni.showToast({ title: '请先登录后领取', icon: 'none' })
        uni.navigateTo({ url: '/pages/login/login' })
        return
      }

      if (!this.canClaim(item)) return

      this.claimingId = item.id
      try {
        await claimActivityCoupon(this.activityId, item.id)
        uni.showToast({ title: '领取成功', icon: 'success' })
        await this.refreshDetailSilently()
      } catch (err) {
        uni.showToast({ title: this.errorText(err), icon: 'none' })
        await this.refreshDetailSilently()
      } finally {
        this.claimingId = null
      }
    },

    canClaim(item) {
      return item?.is_claimable === true || item?.claim_status === 'available'
    },

    claimButtonText(item) {
      return STATUS_TEXT[item?.claim_status] || (item?.is_claimable ? '立即领取' : '已结束')
    },

    couponDisplayTitle(item) {
      return item.display_title || item.coupon?.name || this.typeText(item.coupon?.type)
    },

    couponDisplayDescription(item) {
      return item.display_description || item.coupon?.description || ''
    },

    typeText(type) {
      return TYPE_TEXT[type] || '优惠券'
    },

    couponRuleText(coupon) {
      if (!coupon) return '优惠规则以卡券为准'
      if (coupon.type === 'percentage_off' && coupon.discount_percent) {
        return `${this.trimNumber(coupon.discount_percent / 10)}折优惠`
      }
      if (coupon.type === 'threshold_amount_off') {
        return `满${this.money(coupon.min_order_amount)}减${this.money(coupon.discount_amount)}`
      }
      if (coupon.discount_amount) {
        return `立减${this.money(coupon.discount_amount)}`
      }
      return '优惠规则以卡券为准'
    },

    validityText(coupon) {
      if (!coupon?.expires_at) return '有效期以门店规则为准'
      return `有效期至 ${this.formatDate(coupon.expires_at)}`
    },

    stockText(item) {
      const remaining = Number(item.remaining_quantity)
      if (!Number.isFinite(remaining)) return '库存以活动规则为准'
      return remaining > 0 ? `剩余${remaining}张` : '已抢光'
    },

    formatDate(value) {
      return String(value || '').slice(0, 10)
    },

    money(value) {
      if (value === null || value === undefined || value === '') return '0'
      return this.trimNumber(Number(value))
    },

    trimNumber(value) {
      if (!Number.isFinite(value)) return '0'
      return Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/\.?0+$/, '')
    },

    errorText(err) {
      if (!err) return '领取失败，请稍后重试'
      if (typeof err === 'string') return err
      return err.detail || err.message || err.errMsg || err.error || '领取失败，请稍后重试'
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(180deg, #fff 0, $bg-warm 220rpx, $bg-color 520rpx);
}

.content {
  height: 100vh;
}

.hero-cover {
  width: 100%;
  height: 420rpx;
  background: #eef1fb;
}

.header-section,
.content-section,
.coupon-section {
  margin: 24rpx 28rpx 0;
  padding: 30rpx;
  border-radius: 28rpx;
  background: $surface;
  border: 1rpx solid $border-soft;
  box-shadow: $shadow-card;
}

.activity-title {
  font-size: 38rpx;
  line-height: 52rpx;
  font-weight: 700;
  color: $text-primary;
}

.activity-desc {
  display: block;
  margin-top: 14rpx;
  font-size: 26rpx;
  line-height: 38rpx;
  color: $text-secondary;
}

.participant-row {
  margin-top: 22rpx;
  display: flex;
  align-items: center;
}

.participant-text {
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(79, 110, 247, 0.1);
  font-size: 22rpx;
  color: $primary;
}

.section-title {
  display: block;
  margin-bottom: 22rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
}

.rich-content {
  font-size: 28rpx;
  line-height: 44rpx;
  color: $text-secondary;
}

.empty-coupons {
  min-height: 160rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 22rpx;
  background: $surface-soft;
}

.empty-text,
.state-text {
  font-size: 28rpx;
  color: $text-muted;
}

.coupon-card {
  padding: 26rpx;
  margin-bottom: 22rpx;
  border-radius: 24rpx;
  background: $surface-soft;
  border: 1rpx solid $border-soft;
}

.coupon-card:last-child {
  margin-bottom: 0;
}

.coupon-main {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24rpx;
}

.coupon-info {
  flex: 1;
  min-width: 0;
}

.coupon-title {
  display: block;
  font-size: 32rpx;
  line-height: 42rpx;
  font-weight: 700;
  color: #e64a19;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.coupon-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  line-height: 34rpx;
  color: $text-secondary;
}

.coupon-meta {
  margin-top: 16rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
}

.coupon-tag {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 159, 67, 0.14);
  color: #f08a24;
  font-size: 22rpx;
}

.coupon-rule {
  font-size: 24rpx;
  color: $text-primary;
}

.claim-btn {
  flex-shrink: 0;
  min-width: 142rpx;
  height: 64rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: $gradient-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow-float;
}

.claim-btn.disabled {
  background: rgba(178, 190, 195, 0.22);
  box-shadow: none;
}

.claim-btn-text {
  font-size: 24rpx;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
}

.claim-btn.disabled .claim-btn-text {
  color: $text-muted;
}

.coupon-extra {
  margin-top: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.coupon-extra-text {
  font-size: 22rpx;
  line-height: 30rpx;
  color: $text-muted;
}

.state-wrap {
  min-height: 620rpx;
  padding: 120rpx 48rpx 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.retry-btn {
  margin-top: 36rpx;
  height: 72rpx;
  padding: 0 44rpx;
  border-radius: 999rpx;
  border: 2rpx solid $primary;
  background: $surface;
  display: flex;
  align-items: center;
  justify-content: center;
}

.retry-btn-text {
  color: $primary;
  font-size: 26rpx;
  font-weight: 600;
}

.bottom-safe {
  height: 48rpx;
}
</style>
