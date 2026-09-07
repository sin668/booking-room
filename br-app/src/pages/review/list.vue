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
      <!-- ==================== 评分概览：仅在按课程或老师维度浏览时展示 ==================== -->
      <view v-if="summary" class="summary-card fade-in">
        <view class="summary-top">
          <view class="summary-score">
            <text class="summary-average">{{ averageText }}</text>
            <text class="summary-stars">{{ starText(summary.average) }}</text>
            <text class="summary-count">{{ summary.count }} 条评价</text>
          </view>
          <view class="summary-divider" />
          <view class="summary-bars">
            <view v-for="row in distributionRows" :key="row.star" class="bar-row">
              <text class="bar-label">{{ row.star }}星</text>
              <view class="bar-track">
                <view
                  class="bar-fill"
                  :class="row.fillClass"
                  :style="{ width: row.percent + '%' }"
                />
              </view>
              <text class="bar-percent">{{ row.percent }}%</text>
            </view>
          </view>
        </view>
        <view v-if="hasSummaryData" class="summary-footer">
          <view class="summary-badge">
            <view class="icon icon-check summary-badge-icon" />
            <text class="summary-badge-text">好评率 {{ summary.positive_rate }}%</text>
          </view>
          <text class="summary-average-label">综合评分 {{ averageText }} 分</text>
        </view>
      </view>

      <!-- ==================== 评分档位 TAB：等宽铺满整行 ==================== -->
      <view class="band-wrap fade-in delay-1">
        <view class="band-tabs">
          <view
            v-for="band in bandTabs"
            :key="band.key"
            class="band-tab"
            :class="{ 'band-tab-on': ratingBand === band.key }"
            @tap="onSwitchBand(band.key)"
          >
            <text class="band-label">{{ band.label }}</text>
            <text class="band-sub">{{ band.sub }}</text>
          </view>
        </view>
      </view>

      <!-- ==================== 排序 + 有图筛选 ==================== -->
      <view class="filter-row fade-in delay-1">
        <view class="seg">
          <text
            v-for="item in SORTS"
            :key="item.key"
            class="seg-item"
            :class="{ 'seg-item-on': sort === item.key }"
            @tap="onSwitchSort(item.key)"
          >{{ item.label }}</text>
        </view>
        <view class="filter-right">
          <view class="photo-chip" :class="{ 'photo-chip-on': hasImages }" @tap="onToggleImages">
            <text class="photo-chip-text">仅看有图</text>
          </view>
          <text class="result-count">共 {{ total }} 条</text>
        </view>
      </view>

      <!-- ==================== 骨架屏 ==================== -->
      <view v-if="loading && !reviews.length" class="loading-state">
        <view v-for="i in 3" :key="i" class="skeleton-card">
          <view class="skeleton-head">
            <view class="skeleton-avatar" />
            <view class="skeleton-head-text">
              <view class="skeleton-row skeleton-row-name" />
              <view class="skeleton-row skeleton-row-time" />
            </view>
          </view>
          <view class="skeleton-row" />
          <view class="skeleton-row skeleton-row-short" />
        </view>
      </view>

      <!-- ==================== 空状态 ==================== -->
      <view v-else-if="!loading && !reviews.length" class="empty-state">
        <view class="empty-icon-wrap">
          <text class="empty-icon">☆</text>
        </view>
        <text class="empty-text">{{ emptyText }}</text>
        <text class="empty-desc">{{ emptyDesc }}</text>
      </view>

      <!-- ==================== 评价列表 ==================== -->
      <view v-else class="review-list">
        <view
          v-for="(item, index) in reviews"
          :key="item.id"
          class="review-card fade-in"
          :class="enterClass(index)"
        >
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
                <text class="review-dot">·</text>
                <text class="review-time">{{ timeText(item.created_at) }}</text>
              </view>
            </view>
            <view class="review-score">
              <text class="review-score-num">{{ ratingText(item.rating) }}</text>
              <text class="review-score-unit">分</text>
            </view>
          </view>

          <text class="review-content">{{ item.content }}</text>

          <view v-if="item.images.length" class="review-images">
            <image
              v-for="(img, imgIndex) in item.images"
              :key="imgIndex"
              class="review-image"
              :class="imageClass(item.images.length)"
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
            <view class="icon icon-book review-target-icon" />
            <text class="review-target-text">{{ targetText(item) }}</text>
          </view>

          <view v-if="mine && item.reject_reason" class="review-reject">
            <text class="review-reject-label">驳回理由</text>
            <text class="review-reject-text">{{ item.reject_reason }}</text>
          </view>

          <view v-if="item.reply_content" class="review-reply">
            <text class="review-reply-label">机构回复</text>
            <text class="review-reply-text">{{ item.reply_content }}</text>
          </view>
        </view>

        <view class="load-more">
          <text v-if="loading" class="load-more-text">加载中…</text>
          <text v-else-if="!hasMore" class="load-more-text">已经到底啦 · 共 {{ total }} 条评价</text>
        </view>
      </view>

      <view class="bottom-space" />
    </scroll-view>
  </view>
</template>

<script>
import { getReviewList, getReviewSummary } from '@/api/review'
import { buildStarChars, formatErrorDetail, formatRelativeDay } from '@/utils/formatters'

const PAGE_SIZE = 20
const SORTS = [
  { key: 'new', label: '最新发布' },
  { key: 'score', label: '评分最高' },
]
const STATUS_LABELS = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已驳回',
}
// 档位副标题：与后端 RATING_BANDS 的星级集合口径一致
const BAND_SUBS = {
  good: '4-5星',
  mid: '3星',
  bad: '1-2星',
}
const BAND_KEYS = ['all', 'good', 'mid', 'bad']
const BAND_LABELS = {
  all: '全部',
  good: '好评',
  mid: '中评',
  bad: '差评',
}

export default {
  data() {
    return {
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
    // 「全部」TAB 副标题展示好评率；概览接口不支持「我的评价」维度时回落到总条数
    allBandSub() {
      if (!this.hasSummaryData) return '全部评价'
      return `${this.summary.positive_rate}%好评`
    },
    bandTabs() {
      return BAND_KEYS.map((key) => ({
        key,
        label: BAND_LABELS[key],
        sub: key === 'all' ? this.allBandSub : BAND_SUBS[key],
      }))
    },
    distributionRows() {
      const total = Number(this.summary?.count || 0)
      const distribution = this.summary?.distribution || {}
      return [5, 4, 3, 2, 1].map((star) => {
        const count = Number(distribution[String(star)] || 0)
        const percent = total ? Math.round((count / total) * 100) : 0
        // 1-2 星走暖色，与好评/差评的语义色区分；比较结果在 JS 侧算好（BUG-20）
        return { star, count, percent, fillClass: star <= 2 ? 'bar-fill-low' : 'bar-fill-high' }
      })
    },
    emptyText() {
      if (this.mine) return '你还没有发表过评价'
      if (this.ratingBand !== 'all' || this.hasImages) return '没有符合条件的评价'
      return '暂无评价，快来抢沙发'
    },
    emptyDesc() {
      if (this.mine) return '完成课程或自习室预约后即可发表评价'
      if (this.ratingBand !== 'all' || this.hasImages) return '换个筛选条件看看'
      return '成为第一个评价的人'
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
    // BUG-20 防线：模板里不出现 `<` `>` 字符，星级与比较结果都在方法内算好
    starText(rating) {
      return buildStarChars(rating).join('')
    },

    ratingText(rating) {
      return Number(rating || 0).toFixed(1)
    },

    timeText(value) {
      return formatRelativeDay(value)
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

    // 入场动画分批延迟，超过 4 张后不再叠加，避免长列表越滚越慢
    enterClass(index) {
      return `delay-${index % 4}`
    },

    // 单图放大、双图并排、三图及以上走三列网格
    imageClass(count) {
      if (count === 1) return 'review-image-single'
      if (count === 2) return 'review-image-double'
      return ''
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
  background: linear-gradient(180deg, $bg-warm 0%, $bg-color 260rpx);
}

.review-scroll {
  flex: 1;
  height: 0;
}

/* === 入场动画 === */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* backwards 而非 forwards：动画结束后回到自然状态（opacity 1），
   避免小程序下动画未触发时元素永久停在 opacity 0 而不可见 */
.fade-in {
  animation: fadeInUp 0.36s $ease-out backwards;
}

.delay-1 {
  animation-delay: 0.06s;
}

.delay-2 {
  animation-delay: 0.12s;
}

.delay-3 {
  animation-delay: 0.18s;
}

.delay-0 {
  animation-delay: 0s;
}

/* === 评分概览 === */
.summary-card {
  margin: 24rpx 24rpx 0;
  padding: 30rpx 28rpx 24rpx;
  background: $surface;
  border-radius: $radius-xl;
  box-shadow: $shadow-card;
}

.summary-top {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.summary-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 168rpx;
}

.summary-average {
  font-size: 76rpx;
  font-weight: bold;
  line-height: 1;
  color: $text-primary;
}

.summary-stars {
  margin-top: 12rpx;
  font-size: 22rpx;
  letter-spacing: 2rpx;
  color: #ffb400;
}

.summary-count {
  margin-top: 10rpx;
  font-size: 20rpx;
  color: $text-muted;
}

.summary-divider {
  width: 2rpx;
  height: 108rpx;
  background: rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
}

.summary-bars {
  flex: 1;
  min-width: 0;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 12rpx;

  & + & {
    margin-top: 12rpx;
  }
}

.bar-label {
  width: 48rpx;
  font-size: 20rpx;
  color: $text-secondary;
  text-align: right;
  flex-shrink: 0;
}

.bar-track {
  flex: 1;
  height: 10rpx;
  background: $bg-color;
  border-radius: 999rpx;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999rpx;
  transition: width 0.4s $ease-out;
}

.bar-fill-high {
  background: linear-gradient(90deg, #ffc93c 0%, #ffb400 100%);
}

.bar-fill-low {
  background: linear-gradient(90deg, #ffb37b 0%, #f39c12 100%);
}

.bar-percent {
  width: 60rpx;
  font-size: 20rpx;
  color: $text-muted;
  flex-shrink: 0;
}

.summary-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 26rpx;
  padding-top: 22rpx;
  border-top: 2rpx solid rgba(0, 0, 0, 0.04);
}

.summary-badge {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 8rpx 20rpx;
  background: $success-light;
  border-radius: 999rpx;
}

.summary-badge-icon {
  font-size: 18rpx;
  color: $success;
}

.summary-badge-text {
  font-size: 20rpx;
  font-weight: 500;
  color: $success;
}

.summary-average-label {
  font-size: 20rpx;
  color: $text-muted;
}

/* === 评分档位 TAB：四等分铺满整行 === */
.band-wrap {
  margin: 20rpx 24rpx 0;
  padding: 6rpx;
  background: $surface;
  border-radius: 999rpx;
  box-shadow: $shadow-sm;
}

.band-tabs {
  display: flex;
  align-items: stretch;
  gap: 6rpx;
}

.band-tab {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
  padding: 14rpx 4rpx;
  border-radius: 999rpx;
  transition: background 0.22s $ease-out, box-shadow 0.22s $ease-out;
}

.band-tab-on {
  background: $gradient-primary;
  box-shadow: $shadow-md;
}

.band-label {
  font-size: 24rpx;
  font-weight: 500;
  color: $text-secondary;
  white-space: nowrap;
}

.band-tab-on .band-label {
  color: $white;
  font-weight: bold;
}

.band-sub {
  font-size: 18rpx;
  color: $text-muted;
  white-space: nowrap;
}

.band-tab-on .band-sub {
  color: rgba(255, 255, 255, 0.82);
}

/* === 排序 + 有图筛选 === */
.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin: 20rpx 24rpx 0;
}

.seg {
  display: flex;
  padding: 4rpx;
  background: $surface;
  border-radius: 999rpx;
  box-shadow: $shadow-sm;
}

.seg-item {
  padding: 10rpx 24rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  color: $text-secondary;
  transition: all 0.2s $ease-out;
}

.seg-item-on {
  background: $primary-soft;
  color: $primary;
  font-weight: 500;
}

.filter-right {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.photo-chip {
  display: flex;
  align-items: center;
  padding: 10rpx 22rpx;
  background: $surface;
  border: 2rpx solid transparent;
  border-radius: 999rpx;
  box-shadow: $shadow-sm;
  transition: all 0.2s $ease-out;
}

.photo-chip-on {
  background: $primary-light;
  border-color: rgba(79, 110, 247, 0.35);
}

.photo-chip-text {
  font-size: 22rpx;
  color: $text-secondary;
}

.photo-chip-on .photo-chip-text {
  color: $primary;
  font-weight: 500;
}

.result-count {
  font-size: 20rpx;
  color: $text-muted;
}

/* === 骨架屏 === */
.loading-state {
  padding: 20rpx 24rpx 0;
}

.skeleton-card {
  padding: 28rpx;
  background: $surface;
  border-radius: $radius-xl;

  & + & {
    margin-top: 20rpx;
  }
}

.skeleton-head {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 22rpx;
}

.skeleton-avatar {
  width: 68rpx;
  height: 68rpx;
  background: $bg-color;
  border-radius: 50%;
  flex-shrink: 0;
}

.skeleton-head-text {
  flex: 1;
}

.skeleton-row {
  height: 24rpx;
  background: $bg-color;
  border-radius: $radius-sm;

  & + & {
    margin-top: 16rpx;
  }
}

.skeleton-row-name {
  width: 36%;
  height: 28rpx;
}

.skeleton-row-time {
  width: 24%;
  height: 20rpx;
  margin-top: 12rpx;
}

.skeleton-row-short {
  width: 60%;
}

/* === 空状态 === */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 40rpx;
}

.empty-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 140rpx;
  height: 140rpx;
  background: $surface;
  border-radius: 50%;
  box-shadow: $shadow-sm;
}

.empty-icon {
  font-size: 68rpx;
  line-height: 1;
  color: $border-color;
}

.empty-text {
  margin-top: 28rpx;
  font-size: 26rpx;
  font-weight: 500;
  color: $text-secondary;
}

.empty-desc {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: $text-muted;
}

/* === 评价卡片 === */
.review-list {
  padding: 20rpx 24rpx 0;
}

.review-card {
  padding: 28rpx;
  background: $surface;
  border-radius: $radius-xl;
  box-shadow: $shadow-card;

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
  width: 68rpx;
  height: 68rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.review-avatar-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: $gradient-primary;
}

.review-avatar-char {
  font-size: 28rpx;
  font-weight: 500;
  color: $white;
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
  padding: 4rpx 14rpx;
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
  gap: 8rpx;
  margin-top: 8rpx;
}

.review-stars {
  font-size: 20rpx;
  letter-spacing: 2rpx;
  color: #ffb400;
}

.review-dot {
  font-size: 20rpx;
  color: $border-color;
}

.review-time {
  font-size: 20rpx;
  color: $text-muted;
}

.review-score {
  display: flex;
  align-items: baseline;
  gap: 2rpx;
  flex-shrink: 0;
}

.review-score-num {
  font-size: 32rpx;
  font-weight: bold;
  color: #ffb400;
}

.review-score-unit {
  font-size: 18rpx;
  color: $text-muted;
}

.review-content {
  display: block;
  margin-top: 20rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: $text-primary;
}

.review-images {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 20rpx;
}

.review-image {
  width: 186rpx;
  height: 186rpx;
  border-radius: $radius-md;
  background: $bg-color;
}

.review-image-single {
  width: 320rpx;
  height: 320rpx;
  border-radius: $radius-lg;
}

.review-image-double {
  width: 282rpx;
  height: 282rpx;
}

.review-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 20rpx;
}

.review-tag {
  padding: 8rpx 18rpx;
  background: $primary-soft;
  border-radius: 999rpx;
  font-size: 20rpx;
  color: $primary;
}

.review-target {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 20rpx;
  padding-top: 18rpx;
  border-top: 2rpx solid rgba(0, 0, 0, 0.04);
}

.review-target-icon {
  font-size: 20rpx;
  color: $text-muted;
}

.review-target-text {
  font-size: 20rpx;
  color: $text-muted;
}

.review-reject {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  margin-top: 18rpx;
  padding: 18rpx 20rpx;
  background: $danger-light;
  border-left: 6rpx solid $danger;
  border-radius: $radius-md;
}

.review-reject-label {
  font-size: 20rpx;
  font-weight: 500;
  color: $danger;
  flex-shrink: 0;
}

.review-reject-text {
  flex: 1;
  font-size: 22rpx;
  line-height: 1.6;
  color: $danger;
}

.review-reply {
  position: relative;
  margin-top: 26rpx;
  padding: 26rpx 20rpx 18rpx;
  background: $surface-soft;
  border-radius: $radius-md;
}

.review-reply-label {
  position: absolute;
  top: -14rpx;
  left: 24rpx;
  padding: 5rpx 16rpx;
  background: $gradient-primary;
  border-radius: 999rpx;
  font-size: 18rpx;
  color: $white;
  box-shadow: $shadow-sm;
}

.review-reply-text {
  display: block;
  font-size: 22rpx;
  line-height: 1.7;
  color: $text-secondary;
}

/* === 加载更多 === */
.load-more {
  padding: 32rpx 0;
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
