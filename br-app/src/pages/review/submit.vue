<template>
  <view class="page">
    <scroll-view class="submit-scroll" scroll-y>
      <!-- 已评价：一个订单只能评价一次 -->
      <view v-if="alreadyReviewed" class="state-card">
        <text class="state-icon">✓</text>
        <text class="state-title">该订单已评价</text>
        <text class="state-desc">一个订单只能发表一次评价</text>
        <view class="state-btn" @tap="goMyReviews">
          <text class="state-btn-text">查看我的评价</text>
        </view>
      </view>

      <template v-else>
        <!-- 订单信息 -->
        <view class="card order-card">
          <text class="order-name">{{ orderName }}</text>
          <view v-if="booking.teacher_name" class="order-row">
            <text class="order-label">老师</text>
            <text class="order-value">{{ booking.teacher_name }}</text>
          </view>
          <view v-if="orderTimeText" class="order-row">
            <text class="order-label">上课时间</text>
            <text class="order-value">{{ orderTimeText }}</text>
          </view>
        </view>

        <!-- 星级评分 -->
        <view class="card">
          <text class="card-title">总体评分</text>
          <view class="rating-row">
            <text
              v-for="slot in starSlots"
              :key="slot.value"
              class="rating-star"
              @tap="setRating(slot.value)"
            >{{ slot.char }}</text>
          </view>
          <view v-if="ratingMeta" class="rating-meta">
            <text class="rating-text" :style="{ color: ratingMeta.color }">{{ ratingMeta.text }}</text>
            <text class="rating-hint">{{ ratingMeta.hint }}</text>
          </view>
          <text v-else class="rating-hint">点击星星打分</text>
        </view>

        <!-- 标签 -->
        <view class="card">
          <text class="card-title">
            选择标签
            <text class="card-title-sub">（最多 5 个，可不选）</text>
          </text>
          <view class="tag-row">
            <text
              v-for="tag in tagPool"
              :key="tag"
              class="tag"
              :class="{ 'tag-on': tags.indexOf(tag) !== -1 }"
              @tap="toggleTag(tag)"
            >{{ tag }}</text>
          </view>
        </view>

        <!-- 评价内容 -->
        <view class="card">
          <view class="card-title-row">
            <text class="card-title">评价内容</text>
            <text class="counter">{{ content.length }}/500</text>
          </view>
          <textarea
            v-model="content"
            class="content-input"
            maxlength="500"
            placeholder="说说这门课、这位老师给你的真实感受，帮助更多同学做决定"
            placeholder-class="content-placeholder"
          />
        </view>

        <!-- 图片 -->
        <view class="card">
          <text class="card-title">
            上传图片
            <text class="card-title-sub">（最多 9 张，可不传）</text>
          </text>
          <view class="image-row">
            <view v-for="(img, index) in images" :key="img" class="image-item">
              <image class="image-thumb" :src="img" mode="aspectFill" @tap="previewImage(img)" />
              <view class="image-remove" @tap.stop="removeImage(index)">
                <text class="image-remove-text">×</text>
              </view>
            </view>
            <view v-if="uploading" class="image-item image-add">
              <text class="image-add-text">上传中</text>
            </view>
            <view
              v-else-if="canAddImage"
              class="image-item image-add"
              @tap="chooseImages"
            >
              <text class="image-add-icon">＋</text>
              <text class="image-add-text">{{ images.length }}/9</text>
            </view>
          </view>
        </view>

        <!-- 匿名 -->
        <view class="card anonymous-card">
          <view class="anonymous-text">
            <text class="card-title">匿名评价</text>
            <text class="anonymous-desc">开启后其他同学看不到你的昵称与头像</text>
          </view>
          <switch :checked="isAnonymous" color="#4F6EF7" @change="onAnonymousChange" />
        </view>

        <view class="scroll-bottom-space" />
      </template>
    </scroll-view>

    <!-- 底部提交栏 -->
    <view v-if="!alreadyReviewed" class="submit-bar">
      <view class="submit-btn" :class="{ 'submit-btn-disabled': submitting }" @tap="onSubmit">
        <text class="submit-btn-text">{{ submitting ? '提交中...' : '提交评价' }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getBooking } from '@/api/bookings'
import { getReviewList, createReview } from '@/api/review'
import { uploadImage } from '@/api/upload'
import { buildStarChars, formatErrorDetail } from '@/utils/formatters'

const MAX_IMAGES = 9
const MAX_TAGS = 5
const RATING_META = [
  { text: '很失望', hint: '课程与预期差距较大', color: '#E4574C' },
  { text: '不太满意', hint: '还有较多可以改进的地方', color: '#F39C12' },
  { text: '一般般', hint: '基本符合预期，中规中矩', color: '#F39C12' },
  { text: '比较满意', hint: '整体不错，值得推荐', color: '#FFB400' },
  { text: '超出预期', hint: '老师讲解、课程安排都很棒', color: '#FFB400' },
]
const TAGS_POS = ['讲解清晰', '重点突出', '答疑及时', '资料齐全', '节奏适中', '互动性强', '案例生动', '环境安静', '座位舒适', '性价比高', '收获很大', '会再报名']
const TAGS_NEG = ['进度太快', '内容偏浅', '答疑不及时', '资料缺失', '设备问题', '隔音较差', '座位拥挤', '性价比一般', '与描述不符']

function chooseImagePaths(count) {
  return new Promise((resolve, reject) => {
    uni.chooseImage({
      count,
      sizeType: ['compressed'],
      success: (res) => resolve(res.tempFilePaths || []),
      fail: reject,
    })
  })
}

export default {
  data() {
    return {
      bookingId: null,
      booking: {},
      loading: true,
      alreadyReviewed: false,
      rating: 0,
      tags: [],
      content: '',
      images: [],
      uploading: false,
      isAnonymous: false,
      submitting: false,
    }
  },

  computed: {
    orderName() {
      return this.booking.course_name || this.booking.room?.name || '订单'
    },
    orderTimeText() {
      const booking = this.booking
      if (booking.date) {
        const time = String(booking.start_time || '').slice(0, 5)
        return `${String(booking.date).slice(0, 10)}${time ? ' ' + time : ''}`
      }
      return booking.start_date ? String(booking.start_date).slice(0, 10) : ''
    },
    // BUG-20 防线：模板里不出现 `<` `>` 字符，比较结果都在 computed 里算好
    // value 供 @tap 回传所点星数，char 取自公用星级渲染
    starSlots() {
      return buildStarChars(this.rating).map((char, index) => ({ value: index + 1, char }))
    },
    ratingMeta() {
      return this.rating ? RATING_META[this.rating - 1] : null
    },
    tagPool() {
      // 未打分时默认展示好评标签，仅 1-3 星切到差评标签
      return this.rating && this.rating <= 3 ? TAGS_NEG : TAGS_POS
    },
    canAddImage() {
      return this.images.length < MAX_IMAGES
    },
  },

  onLoad(options) {
    const query = options || {}
    this.bookingId = query.booking_id ? Number(query.booking_id) : null
    if (!this.bookingId) {
      uni.showToast({ title: '缺少订单信息', icon: 'none' })
      this.loading = false
      return
    }
    this.loadBooking()
    this.checkAlreadyReviewed()
  },

  methods: {
    async loadBooking() {
      try {
        this.booking = await getBooking(this.bookingId)
      } catch (error) {
        uni.showToast({ title: formatErrorDetail(error, '订单信息加载失败'), icon: 'none' })
      } finally {
        this.loading = false
      }
    },

    // 进入时预判：复用列表接口按订单查本人评价，后端 400 仍是最终兜底
    async checkAlreadyReviewed() {
      try {
        const data = await getReviewList({ booking_id: this.bookingId, mine: true, page: 1, page_size: 1 })
        this.alreadyReviewed = (data.total || 0) !== 0
      } catch {
        this.alreadyReviewed = false
      }
    },

    setRating(value) {
      if (this.rating === value) return
      // 标签池随星级切换；直接比对切换前后的池，避免与 tagPool 的判定条件各写一套而漂移
      const previousPool = this.tagPool
      this.rating = value
      if (this.tagPool !== previousPool) this.tags = []
    },

    toggleTag(tag) {
      const index = this.tags.indexOf(tag)
      if (index !== -1) {
        this.tags.splice(index, 1)
        return
      }
      if (this.tags.length >= MAX_TAGS) {
        uni.showToast({ title: `最多选择 ${MAX_TAGS} 个标签`, icon: 'none' })
        return
      }
      this.tags.push(tag)
    },

    async chooseImages() {
      const remain = MAX_IMAGES - this.images.length
      if (remain <= 0) return
      let paths = []
      try {
        paths = await chooseImagePaths(remain)
      } catch {
        return // 用户取消选择
      }
      if (!paths.length) return

      this.uploading = true
      for (const path of paths) {
        try {
          const result = await uploadImage(path, 'review')
          this.images.push(result.url)
        } catch (error) {
          // 单张失败不入列，其余继续
          uni.showToast({ title: formatErrorDetail(error, '图片上传失败'), icon: 'none' })
        }
      }
      this.uploading = false
    },

    removeImage(index) {
      this.images.splice(index, 1)
    },

    previewImage(current) {
      uni.previewImage({ current, urls: this.images })
    },

    onAnonymousChange(event) {
      this.isAnonymous = event.detail.value
    },

    goMyReviews() {
      uni.navigateTo({ url: '/pages/review/list?mine=1' })
    },

    async onSubmit() {
      if (this.submitting) return
      if (!this.rating) {
        uni.showToast({ title: '请先打分', icon: 'none' })
        return
      }
      const content = this.content.trim()
      if (!content) {
        uni.showToast({ title: '请填写评价内容', icon: 'none' })
        return
      }

      this.submitting = true
      try {
        await createReview({
          booking_id: this.bookingId,
          rating: this.rating,
          content,
          images: this.images,
          tags: this.tags,
          is_anonymous: this.isAnonymous,
        })
        uni.showToast({ title: '提交成功，审核通过后展示', icon: 'none' })
        setTimeout(() => uni.navigateBack(), 1200)
      } catch (error) {
        uni.showToast({ title: formatErrorDetail(error, '提交失败'), icon: 'none' })
      } finally {
        this.submitting = false
      }
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

.submit-scroll {
  flex: 1;
  height: 0;
}

.card {
  margin: 20rpx 24rpx 0;
  padding: 28rpx;
  background: $surface;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
}

.card-title {
  font-size: 28rpx;
  font-weight: 500;
  color: $text-primary;
}

.card-title-sub {
  font-size: 20rpx;
  font-weight: normal;
  color: $text-muted;
}

.card-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* === 订单信息 === */
.order-card {
  margin-top: 24rpx;
}

.order-name {
  display: block;
  font-size: 30rpx;
  font-weight: bold;
  color: $text-primary;
}

.order-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 12rpx;
}

.order-label {
  font-size: 22rpx;
  color: $text-muted;
}

.order-value {
  font-size: 22rpx;
  color: $text-secondary;
}

/* === 星级评分 === */
.rating-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 20rpx;
}

.rating-star {
  font-size: 60rpx;
  line-height: 1;
  color: #ffb400;
}

.rating-meta {
  display: flex;
  align-items: baseline;
  gap: 12rpx;
  margin-top: 16rpx;
}

.rating-text {
  font-size: 26rpx;
  font-weight: 500;
}

.rating-hint {
  margin-top: 16rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.rating-meta .rating-hint {
  margin-top: 0;
}

/* === 标签 === */
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 20rpx;
}

.tag {
  padding: 10rpx 22rpx;
  background: $bg-color;
  border-radius: 999rpx;
  font-size: 22rpx;
  color: $text-secondary;
}

.tag-on {
  background: $primary-soft;
  color: $primary;
  font-weight: 500;
}

/* === 评价内容 === */
.counter {
  font-size: 20rpx;
  color: $text-muted;
}

.content-input {
  width: 100%;
  height: 200rpx;
  margin-top: 16rpx;
  padding: 20rpx;
  box-sizing: border-box;
  background: $bg-color;
  border-radius: $radius-md;
  font-size: 26rpx;
  line-height: 1.6;
  color: $text-primary;
}

.content-placeholder {
  color: $text-muted;
}

/* === 图片 === */
.image-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 20rpx;
}

.image-item {
  position: relative;
  width: 200rpx;
  height: 200rpx;
}

.image-thumb {
  width: 200rpx;
  height: 200rpx;
  border-radius: $radius-md;
  background: $bg-color;
}

.image-remove {
  position: absolute;
  top: -10rpx;
  right: -10rpx;
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.55);
  border-radius: 50%;
}

.image-remove-text {
  font-size: 26rpx;
  line-height: 1;
  color: $white;
}

.image-add {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  background: $bg-color;
  border: 2rpx dashed $border-color;
  border-radius: $radius-md;
  box-sizing: border-box;
}

.image-add-icon {
  font-size: 44rpx;
  line-height: 1;
  color: $text-muted;
}

.image-add-text {
  font-size: 20rpx;
  color: $text-muted;
}

/* === 匿名 === */
.anonymous-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.anonymous-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  color: $text-muted;
}

/* === 已评价状态 === */
.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 120rpx 24rpx 0;
  padding: 60rpx 40rpx;
  background: $surface;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
}

.state-icon {
  width: 96rpx;
  height: 96rpx;
  line-height: 96rpx;
  text-align: center;
  background: $success-light;
  border-radius: 50%;
  font-size: 48rpx;
  color: $success;
}

.state-title {
  margin-top: 24rpx;
  font-size: 30rpx;
  font-weight: 500;
  color: $text-primary;
}

.state-desc {
  margin-top: 12rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.state-btn {
  margin-top: 32rpx;
  padding: 16rpx 48rpx;
  background: $primary-soft;
  border-radius: 999rpx;
}

.state-btn-text {
  font-size: 26rpx;
  color: $primary;
}

/* === 底部提交栏 === */
.submit-bar {
  flex-shrink: 0;
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: $surface;
  box-shadow: $shadow-bottom;
}

.submit-btn {
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $gradient-primary;
  border-radius: 999rpx;
}

.submit-btn-disabled {
  opacity: 0.6;
}

.submit-btn-text {
  font-size: 30rpx;
  font-weight: 500;
  color: $white;
}

.scroll-bottom-space {
  height: 40rpx;
}
</style>
