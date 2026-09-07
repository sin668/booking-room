<template>
  <view class="page">
    <scroll-view
      class="review-scroll"
      scroll-y
      refresher-enabled
      :refresher-triggered="refreshing"
      @refresherrefresh="onPullRefresh"
      @scrolltolower="onLoadMore"
    >
      <!-- 评分概览：仅在按课程或老师维度浏览时展示 -->
      <view v-if="summary" class="summary-card">
        <view class="summary-top">
          <view class="summary-score">
            <text class="summary-average">{{ averageText }}</text>
            <text class="summary-stars">{{ starText(summary.average) }}</text>
            <text class="summary-count">{{ summary.count }} 条评价</text>
          </view>
          <view class="summary-bars">
            <view v-for="row in distributionRows" :key="row.star" class="bar-row">
              <text class="bar-label">{{ row.star }}星</text>
              <view class="bar-track">
                <view
                  class="bar-fill"
                  :class="{ 'bar-fill-low': row.low }"
                  :style="{ width: row.percent + '%' }"
                />
              </view>
              <text class="bar-percent">{{ row.percent }}%</text>
            </view>
          </view>
        </view>
        <view v-if="hasSummaryData" class="summary-footer">
          <text class="summary-badge">好评率 {{ summary.positive_rate }}%</text>
        </view>
      </view>

      <!-- 筛选 + 排序 -->
      <view class="filter-bar">
        <view class="chip-row">
          <text
            v-for="band in BANDS"
            :key="band.key"
            class="chip"
            :class="{ 'chip-on': ratingBand === band.key }"
            @tap="onSwitchBand(band.key)"
          >{{ band.label }}</text>
          <text
            class="chip"
            :class="{ 'chip-on': hasImages }"
            @tap="onToggleImages"
          >仅看有图</text>
        </view>
        <view class="filter-row">
          <view class="seg">
            <text
              v-for="item in SORTS"
              :key="item.key"
              class="seg-item"
              :class="{ 'seg-item-on': sort === item.key }"
              @tap="onSwitchSort(item.key)"
            >{{ item.label }}</text>
          </view>
          <text class="result-count">共 {{ total }} 条</text>
        </view>
      </view>

      <!-- 骨架屏 -->
      <view v-if="loading && !reviews.length" class="loading-state">
        <view v-for="i in 3" :key="i" class="skeleton-card">
          <view class="skeleton-row skeleton-row-header" />
          <view class="skeleton-row" />
          <view class="skeleton-row skeleton-row-short" />
        </view>
      </view>

      <!-- 空状态 -->
      <view v-else-if="!loading && !reviews.length" class="empty-state">
        <text class="empty-icon">☆</text>
        <text class="empty-text">{{ emptyText }}</text>
      </view>

      <!-- 评价列表 -->
      <view v-else class="review-list">
        <view v-for="item in reviews" :key="item.id" class="review-card">
          <view class="review-header">
            <image
              v-if="item.user_avatar"
              class="review-avatar"
              :src="item.user_avatar"
              mode="aspectFill"
            />
            <view v-else class="review-avatar review-avatar-empty">
              <text class="review-avatar-char">{{ avatarChar(item.user_nickname) }}</text>
            </view>
            <view class="review-meta">
              <view class="review-title-row">
                <text class="review-name">{{ item.user_nickname || '匿名用户' }}</text>
                <text v-if="mine" class="review-status" :class="statusClass(item.status)">
                  {{ statusLabel(item.status) }}
                </text>
              </view>
              <view class="review-sub-row">
                <text class="review-stars">{{ starText(item.rating) }}</text>
                <text class="review-time">{{ formatDateTime(item.created_at) }}</text>
              </view>
            </view>
          </view>

          <text class="review-content">{{ item.content }}</text>

          <view v-if="item.images.length" class="review-images">
            <image
              v-for="(img, imgIndex) in item.images"
              :key="imgIndex"
              class="review-image"
              :src="img"
              mode="aspectFill"
              @tap="previewImage(item.images, img)"
            />
          </view>

          <view v-if="item.tags.length" class="review-tags">
            <text v-for="(tag, tagIndex) in item.tags" :key="tagIndex" class="review-tag">
              {{ tag }}
            </text>
          </view>

          <view v-if="mine && targetText(item)" class="review-target">
            <text class="review-target-text">{{ targetText(item) }}</text>
          </view>

          <view v-if="mine && item.reject_reason" class="review-reject">
            <text class="review-reject-text">驳回理由：{{ item.reject_reason }}</text>
          </view>

          <view v-if="item.reply_content" class="review-reply">
            <text class="review-reply-label">机构回复</text>
            <text class="review-reply-text">{{ item.reply_content }}</text>
          </view>
        </view>

        <view class="load-more">
          <text v-if="loading" class="load-more-text">加载中...</text>
          <text v-else-if="!hasMore" class="load-more-text">没有更多了</text>
        </view>
      </view>

      <view class="bottom-space" />
    </scroll-view>
  </view>
</template>

<script>
import { getReviewList, getReviewSummary } from '@/api/review'
import { buildStarChars, formatDateTime, formatErrorDetail } from '@/utils/formatters'

const PAGE_SIZE = 20
const BANDS = [
  { key: 'all', label: '全部' },
  { key: 'good', label: '好评' },
  { key: 'mid', label: '中评' },
  { key: 'bad', label: '差评' },
]
const SORTS = [
  { key: 'new', label: '最新发布' },
  { key: 'score', label: '评分最高' },
]
const STATUS_LABELS = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已驳回',
}

export default {
  data() {
    return {
      BANDS,
      SORTS,
      courseId: null,
      teacherId: null,
      mine: false,
      reviews: [],
      total: 0,
      page: 1,
      hasMore: true,
      loading: false,
      refreshing: false,
      summary: null,
      ratingBand: 'all',
      hasImages: false,
      sort: 'new',
    }
  },

  computed: {
    averageText() {
      return Number(this.summary?.average || 0).toFixed(1)
    },
    hasSummaryData() {
      return Number(this.summary?.count || 0) !== 0
    },
    distributionRows() {
      const total = Number(this.summary?.count || 0)
      const distribution = this.summary?.distribution || {}
      return [5, 4, 3, 2, 1].map((star) => {
        const count = Number(distribution[String(star)] || 0)
        const percent = total ? Math.round((count / total) * 100) : 0
        return { star, count, percent, low: star === 1 || star === 2 }
      })
    },
    emptyText() {
      if (this.mine) return '你还没有发表过评价'
      if (this.ratingBand !== 'all' || this.hasImages) return '没有符合条件的评价'
      return '暂无评价，快来抢沙发'
    },
  },

  onLoad(options) {
    const query = options || {}
    this.courseId = query.course_id ? Number(query.course_id) : null
    this.teacherId = query.teacher_id ? Number(query.teacher_id) : null
    this.mine = query.mine === '1' || query.mine === 'true'

    const title = query.title
      ? decodeURIComponent(query.title)
      : this.mine
        ? '我的评价'
        : '学员评价'
    uni.setNavigationBarTitle({ title })

    this.loadSummary()
    this.resetAndLoad()
  },

  methods: {
    formatDateTime,

    // BUG-20 防线：模板里不出现 `<` `>` 字符，星级与比较结果都在方法内算好
    starText(rating) {
      return buildStarChars(rating).join('')
    },

    avatarChar(nickname) {
      return String(nickname || '匿').slice(0, 1)
    },

    statusLabel(status) {
      return STATUS_LABELS[status] || status
    },

    statusClass(status) {
      return `review-status-${status}`
    },

    targetText(item) {
      return [item.course_name, item.teacher_name].filter(Boolean).join(' · ')
    },

    buildParams() {
      const params = {
        page: this.page,
        page_size: PAGE_SIZE,
        rating_band: this.ratingBand,
        has_images: this.hasImages,
        sort: this.sort,
      }
      if (this.mine) params.mine = true
      if (this.courseId) params.course_id = this.courseId
      if (this.teacherId) params.teacher_id = this.teacherId
      return params
    },

    async loadSummary() {
      // 概览接口只支持课程/老师维度，「我的评价」不展示概览
      if (!this.courseId && !this.teacherId) return
      const params = {}
      if (this.courseId) params.course_id = this.courseId
      if (this.teacherId) params.teacher_id = this.teacherId
      try {
        this.summary = await getReviewSummary(params)
      } catch (error) {
        this.summary = null
        uni.showToast({ title: formatErrorDetail(error, '评价概览加载失败'), icon: 'none' })
      }
    },

    async resetAndLoad() {
      this.page = 1
      this.reviews = []
      this.hasMore = true
      await this.loadReviews()
    },

    async loadReviews() {
      if (this.loading) return
      this.loading = true
      try {
        const data = await getReviewList(this.buildParams())
        const items = data.items || []
        this.reviews = this.page === 1 ? items : this.reviews.concat(items)
        this.total = data.total || 0
        this.hasMore = this.reviews.length < this.total
      } catch (error) {
        if (this.page === 1) this.reviews = []
        uni.showToast({ title: formatErrorDetail(error, '评价加载失败'), icon: 'none' })
      } finally {
        this.loading = false
        this.refreshing = false
      }
    },

    onSwitchBand(key) {
      if (this.ratingBand === key) return
      this.ratingBand = key
      this.resetAndLoad()
    },

    onToggleImages() {
      this.hasImages = !this.hasImages
      this.resetAndLoad()
    },

    onSwitchSort(key) {
      if (this.sort === key) return
      this.sort = key
      this.resetAndLoad()
    },

    onPullRefresh() {
      this.refreshing = true
      this.loadSummary()
      this.resetAndLoad()
    },

    onLoadMore() {
      if (!this.hasMore || this.loading) return
      this.page += 1
      this.loadReviews()
    },

    previewImage(urls, current) {
      uni.previewImage({ current, urls })
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

.review-scroll {
  flex: 1;
  height: 0;
}

/* === 评分概览 === */
.summary-card {
  margin: 20rpx 24rpx 0;
  padding: 28rpx;
  background: $surface;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
}

.summary-top {
  display: flex;
  align-items: center;
  gap: 28rpx;
}

.summary-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 160rpx;
}

.summary-average {
  font-size: 72rpx;
  font-weight: bold;
  line-height: 1;
  color: $text-primary;
}

.summary-stars {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #ffb400;
}

.summary-count {
  margin-top: 8rpx;
  font-size: 20rpx;
  color: $text-muted;
}

.summary-bars {
  flex: 1;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 12rpx;

  & + & {
    margin-top: 10rpx;
  }
}

.bar-label {
  width: 48rpx;
  font-size: 20rpx;
  color: $text-secondary;
  text-align: right;
}

.bar-track {
  flex: 1;
  height: 10rpx;
  background: $bg-color;
  border-radius: 6rpx;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: #ffb400;
  border-radius: 6rpx;
}

.bar-fill-low {
  background: #f39c12;
}

.bar-percent {
  width: 56rpx;
  font-size: 20rpx;
  color: $text-muted;
}

.summary-footer {
  margin-top: 24rpx;
  padding-top: 20rpx;
  border-top: 2rpx solid rgba(0, 0, 0, 0.04);
}

.summary-badge {
  display: inline-block;
  padding: 8rpx 20rpx;
  background: $success-light;
  border-radius: 999rpx;
  font-size: 20rpx;
  color: $success;
}

/* === 筛选 + 排序 === */
.filter-bar {
  margin: 20rpx 24rpx 0;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.chip {
  padding: 10rpx 24rpx;
  background: $surface;
  border-radius: 999rpx;
  font-size: 22rpx;
  color: $text-secondary;
}

.chip-on {
  background: $primary;
  color: $white;
}

.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
}

.seg {
  display: flex;
  padding: 4rpx;
  background: $surface;
  border-radius: 999rpx;
}

.seg-item {
  padding: 8rpx 22rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  color: $text-secondary;
}

.seg-item-on {
  background: $primary-soft;
  color: $primary;
  font-weight: 500;
}

.result-count {
  font-size: 20rpx;
  color: $text-muted;
}

/* === 骨架屏 === */
.loading-state {
  padding: 20rpx 24rpx;
}

.skeleton-card {
  padding: 28rpx;
  background: $surface;
  border-radius: $radius-lg;

  & + & {
    margin-top: 20rpx;
  }
}

.skeleton-row {
  height: 24rpx;
  background: $bg-color;
  border-radius: $radius-sm;

  & + & {
    margin-top: 16rpx;
  }
}

.skeleton-row-header {
  width: 40%;
  height: 32rpx;
}

.skeleton-row-short {
  width: 60%;
}

/* === 空状态 === */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 140rpx 40rpx;
}

.empty-icon {
  font-size: 88rpx;
  color: $border-color;
}

.empty-text {
  margin-top: 20rpx;
  font-size: 24rpx;
  color: $text-muted;
}

/* === 评价卡片 === */
.review-list {
  padding: 20rpx 24rpx 0;
}

.review-card {
  padding: 28rpx;
  background: $surface;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;

  & + & {
    margin-top: 20rpx;
  }
}

.review-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.review-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.review-avatar-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: $primary-soft;
}

.review-avatar-char {
  font-size: 26rpx;
  color: $primary;
}

.review-meta {
  flex: 1;
  min-width: 0;
}

.review-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.review-name {
  font-size: 26rpx;
  font-weight: 500;
  color: $text-primary;
}

.review-status {
  padding: 2rpx 12rpx;
  border-radius: 999rpx;
  font-size: 18rpx;
}

.review-status-pending {
  background: $orange-light;
  color: $orange;
}

.review-status-approved {
  background: $success-light;
  color: $success;
}

.review-status-rejected {
  background: $danger-light;
  color: $danger;
}

.review-sub-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 6rpx;
}

.review-stars {
  font-size: 20rpx;
  color: #ffb400;
}

.review-time {
  font-size: 20rpx;
  color: $text-muted;
}

.review-content {
  display: block;
  margin-top: 16rpx;
  font-size: 26rpx;
  line-height: 1.6;
  color: $text-primary;
}

.review-images {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 16rpx;
}

.review-image {
  width: 200rpx;
  height: 200rpx;
  border-radius: $radius-md;
  background: $bg-color;
}

.review-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 16rpx;
}

.review-tag {
  padding: 6rpx 16rpx;
  background: $bg-color;
  border-radius: 999rpx;
  font-size: 20rpx;
  color: $text-secondary;
}

.review-target {
  margin-top: 16rpx;
}

.review-target-text {
  font-size: 20rpx;
  color: $text-muted;
}

.review-reject {
  margin-top: 16rpx;
  padding: 16rpx 20rpx;
  background: $danger-light;
  border-radius: $radius-md;
}

.review-reject-text {
  font-size: 22rpx;
  line-height: 1.5;
  color: $danger;
}

.review-reply {
  position: relative;
  margin-top: 24rpx;
  padding: 24rpx 20rpx 16rpx;
  background: $surface-soft;
  border-radius: $radius-md;
}

.review-reply-label {
  position: absolute;
  top: -12rpx;
  left: 24rpx;
  padding: 4rpx 14rpx;
  background: $primary;
  border-radius: 999rpx;
  font-size: 18rpx;
  color: $white;
}

.review-reply-text {
  display: block;
  font-size: 22rpx;
  line-height: 1.6;
  color: $text-secondary;
}

/* === 加载更多 === */
.load-more {
  padding: 28rpx 0;
  text-align: center;
}

.load-more-text {
  font-size: 22rpx;
  color: $text-muted;
}

.bottom-space {
  height: 40rpx;
}
</style>
