<template>
  <view class="page">
    <scroll-view class="submit-scroll" scroll-y>
      <!-- 已评价：一个订单只能评价一次 -->
      <view v-if="alreadyReviewed" class="state-card">
        <view class="state-icon-wrap">
          <view class="icon icon-check state-icon" />
        </view>
        <text class="state-title">该订单已评价</text>
        <text class="state-desc">一个订单只能发表一次评价</text>
        <view class="state-btn" @tap="goMyReviews">
          <text class="state-btn-text">查看我的评价</text>
        </view>
      </view>

      <template v-else>
        <!-- ==================== 订单信息（第一屏） ==================== -->
        <view class="card order-card fade-in">
          <view class="order-head">
            <view class="order-type" :class="orderTypeClass">
              <view class="icon order-type-icon" :class="orderTypeIcon" />
              <text class="order-type-text">{{ orderTypeLabel }}</text>
            </view>
            <view v-if="statusText" class="order-status" :class="statusClass">
              <text class="order-status-text">{{ statusText }}</text>
            </view>
          </view>

          <text class="order-title">{{ orderTitle }}</text>

          <!-- 订单要点：自习室订单显示座位/时段/门店，课程订单显示老师/课时/上课时间/培训室 -->
          <view class="order-lines">
            <view v-for="line in orderLines" :key="line.text" class="order-line">
              <view class="line-icon-box">
                <view class="icon line-icon" :class="line.icon" />
              </view>
              <text class="line-text">{{ line.text }}</text>
            </view>
          </view>

          <!-- 课程订单：课时清单 -->
          <view v-if="lessonTitleList.length" class="lesson-box">
            <text
              v-for="title in lessonTitleList"
              :key="title"
              class="lesson-chip"
            >{{ title }}</text>
          </view>

          <!-- 课程订单：开课 / 结课日期 -->
          <text v-if="courseDateNote" class="order-note">{{ courseDateNote }}</text>

          <view class="order-divider">
            <view v-for="i in 24" :key="i" class="divider-dash" />
          </view>

          <view class="order-foot">
            <text class="order-no">订单编号 #{{ bookingId }}</text>
            <view class="order-price">
              <text v-if="hasDiscount" class="price-origin">¥{{ originalText }}</text>
              <text class="price-symbol">¥</text>
              <text class="price-value">{{ priceText }}</text>
            </view>
          </view>
          <text v-if="hasDiscount" class="order-discount">已优惠 ¥{{ discountText }}</text>
        </view>

        <!-- ==================== 综合评分 ==================== -->
        <view class="card fade-in delay-1">
          <view class="card-head">
            <view class="head-bar" />
            <text class="head-title">综合评分</text>
            <text class="head-star">*</text>
          </view>

          <view class="rating-body">
            <view class="rating-stars">
              <text
                v-for="slot in starSlots"
                :key="slot.value"
                class="star"
                :class="{ 'star-on': slot.on, 'star-pop': slot.value === popStar }"
                @tap="setRating(slot.value)"
              >{{ slot.char }}</text>
            </view>
            <view class="rating-desc">
              <text class="rating-text" :style="{ color: ratingColor }">{{ ratingText }}</text>
            </view>
            <view class="rating-score">
              <text class="score-num">{{ scoreText }}</text>
              <text class="score-unit">分</text>
            </view>
          </view>
        </view>

        <!-- ==================== 评价标签 ==================== -->
        <view class="card fade-in delay-2">
          <view class="card-head">
            <view class="head-bar" />
            <text class="head-title">选个标签</text>
            <text class="head-extra">已选 {{ tags.length }}/{{ maxTags }}</text>
          </view>
          <view class="tag-row">
            <text
              v-for="tag in tagPool"
              :key="tag"
              class="tag"
              :class="tagClass(tag)"
              @tap="toggleTag(tag)"
            >{{ tag }}</text>
          </view>
        </view>

        <!-- ==================== 评价内容 + 快捷填入 ==================== -->
        <view class="card fade-in delay-2">
          <view class="card-head">
            <view class="head-bar" />
            <text class="head-title">写下你的评价</text>
            <text class="counter" :class="{ 'counter-ok': contentEnough }">
              {{ content.length }}/500
            </text>
          </view>

          <textarea
            v-model="content"
            class="content-input"
            :class="{ 'content-input-focus': contentFocused }"
            maxlength="500"
            placeholder="聊聊课程节奏、老师讲解、资料质量、上课环境…真实的评价能帮助更多同学"
            placeholder-class="content-placeholder"
            @focus="contentFocused = true"
            @blur="contentFocused = false"
          />

          <!-- 快捷填入：一键补充常用好评句式 -->
          <view class="quick-row">
            <view class="quick-label">
              <view class="icon icon-star quick-icon" />
              <text class="quick-label-text">快捷填入</text>
            </view>
            <scroll-view class="quick-scroll" scroll-x :show-scrollbar="false">
              <view class="quick-list">
                <text
                  v-for="phrase in quickPhrases"
                  :key="phrase.label"
                  class="quick-chip"
                  :class="{ 'quick-chip-used': isPhraseUsed(phrase) }"
                  @tap="fillPhrase(phrase)"
                >{{ phrase.label }}</text>
              </view>
            </scroll-view>
          </view>
        </view>

        <!-- ==================== 图片上传 ==================== -->
        <view class="card fade-in delay-3">
          <view class="card-head">
            <view class="head-bar" />
            <text class="head-title">添加图片</text>
            <text class="head-extra">最多 9 张，可不传</text>
          </view>
          <view class="image-row">
            <view v-for="(img, index) in images" :key="img" class="image-item">
              <image class="image-thumb" :src="img" mode="aspectFill" @tap="previewImage(img)" />
              <view class="image-remove" @tap.stop="removeImage(index)">
                <text class="image-remove-text">×</text>
              </view>
            </view>
            <view v-if="uploading" class="image-item image-add image-add-busy">
              <text class="image-add-text">上传中</text>
            </view>
            <view v-else-if="canAddImage" class="image-add" @tap="chooseImages">
              <view class="image-add-icon-box">
                <text class="image-add-icon">＋</text>
              </view>
              <text class="image-add-text">{{ images.length }}/9</text>
            </view>
          </view>
        </view>

        <!-- ==================== 匿名与审核提示 ==================== -->
        <view class="card plain-card fade-in delay-3">
          <view class="switch-row">
            <view class="switch-icon-box">
              <view class="icon icon-eye-off switch-icon" />
            </view>
            <view class="switch-text">
              <text class="switch-title">匿名评价</text>
              <text class="switch-desc">开启后其他同学看不到你的昵称与头像</text>
            </view>
            <switch
              class="switch-ctl"
              :checked="isAnonymous"
              color="#4F6EF7"
              @change="onAnonymousChange"
            />
          </view>

          <view class="notice">
            <view class="icon icon-shield notice-icon" />
            <text class="notice-text">评价将经过审核后展示，请勿包含广告、联系方式或不实内容</text>
          </view>
        </view>

        <view class="scroll-bottom-space" />
      </template>
    </scroll-view>

    <!-- ==================== 底部提交栏 ==================== -->
    <view v-if="!alreadyReviewed" class="submit-bar">
      <view class="submit-hint">
        <text class="hint-label">评价要求</text>
        <text class="hint-value" :class="{ 'hint-ok': canSubmit }">{{ submitHint }}</text>
      </view>
      <view class="submit-btn" :class="{ 'submit-btn-off': !canSubmit }" @tap="onSubmit">
        <text class="submit-btn-text">{{ submitText }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getBooking } from '@/api/bookings'
import { getReviewList, createReview } from '@/api/review'
import { uploadImage } from '@/api/upload'
import {
  buildStarChars,
  formatBookingStatus,
  formatCourseEndDate,
  formatCourseSchedule,
  formatCourseStartDate,
  formatErrorDetail,
  formatHourCount,
  formatMoney,
  formatSeatZone,
  formatShortTime,
} from '@/utils/formatters'

const MAX_IMAGES = 9
const MAX_TAGS = 5
// 与后端 min_length=1 保持一致：10 字仅作为前端鼓励阈值，不阻断提交
const CONTENT_SUGGEST_LENGTH = 10
const RATING_META = [
  { text: '很失望', color: '#E4574C' },
  { text: '不太满意', color: '#F39C12' },
  { text: '一般般', color: '#F39C12' },
  { text: '比较满意', color: '#FFB400' },
  { text: '超出预期', color: '#FFB400' },
]
const RATING_IDLE = { text: '点击星星打分', color: '#B2BEC3' }
const TAGS_POS = ['讲解清晰', '重点突出', '答疑及时', '资料齐全', '节奏适中', '互动性强', '案例生动', '环境安静', '座位舒适', '性价比高', '收获很大', '会再报名']
const TAGS_NEG = ['进度太快', '内容偏浅', '答疑不及时', '资料缺失', '设备问题', '隔音较差', '座位拥挤', '性价比一般', '与描述不符']
// 快捷填入：与原型 review-submit.html 的三条常用句式一致
const QUICK_PHRASES = [
  { label: '讲解清晰', text: '老师讲解清晰，重点突出，课后答疑也很及时，收获很大！' },
  { label: '资料齐全', text: '配套资料很全，真题解析详细，跟着节奏复习效率提升明显。' },
  { label: '环境不错', text: '培训室安静舒适，座位宽敞，学习氛围很好，会再来。' },
]

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
      quickPhrases: QUICK_PHRASES,
      maxTags: MAX_TAGS,
      loading: true,
      alreadyReviewed: false,
      rating: 5,
      popStar: 0,
      tags: [],
      content: '',
      contentFocused: false,
      images: [],
      uploading: false,
      isAnonymous: false,
      submitting: false,
    }
  },

  computed: {
    isCourse() {
      return this.booking.booking_type === 'course'
    },
    orderTypeLabel() {
      return this.isCourse ? '课程预约' : '自习室预约'
    },
    orderTypeClass() {
      return this.isCourse ? 'order-type-course' : 'order-type-seat'
    },
    orderTypeIcon() {
      return this.isCourse ? 'icon-book' : 'icon-location'
    },
    orderTitle() {
      if (this.isCourse) return this.booking.course_name || '课程预约'
      return this.booking.room?.name || '自习室预约'
    },
    statusText() {
      return this.booking.status ? formatBookingStatus(this.booking.status) : ''
    },
    // 状态徽标配色随订单状态区分，避免已取消/待开始也走成功色
    statusClass() {
      const status = this.booking.status
      if (status === 'cancelled') return 'order-status-off'
      if (status === 'pending_start' || status === 'pending_confirm') return 'order-status-wait'
      return 'order-status-on'
    },
    seatText() {
      const seat = this.booking.seat
      if (!seat) return ''
      const zone = formatSeatZone(seat.zone)
      return zone ? `${seat.seat_number}号座位 · ${zone}` : `${seat.seat_number}号座位`
    },
    timeRangeText() {
      const booking = this.booking
      if (!booking.date) return ''
      const dateText = String(booking.date).slice(0, 10)
      const start = formatShortTime(booking.start_time)
      const end = formatShortTime(booking.end_time)
      return start && end ? `${dateText} ${start}-${end}` : dateText
    },
    seatTimeText() {
      if (!this.timeRangeText) return ''
      const hours = formatHourCount(this.booking.start_time, this.booking.end_time)
      // formatHourCount 在时间缺失时返回 "0"，需按数值判断再拼接时长
      return Number(hours) > 0 ? `${this.timeRangeText} · ${hours}小时` : this.timeRangeText
    },
    teacherText() {
      return this.booking.teacher_name ? `${this.booking.teacher_name} 老师` : ''
    },
    lessonTitleList() {
      return this.booking.lesson_titles || []
    },
    lessonText() {
      const count = this.lessonTitleList.length
      return count ? `共 ${count} 课时` : ''
    },
    scheduleText() {
      return formatCourseSchedule(this.booking.schedule) || this.timeRangeText
    },
    courseDateNote() {
      if (!this.isCourse) return ''
      return [
        formatCourseStartDate(this.booking.start_date),
        formatCourseEndDate(this.booking.end_date),
      ]
        .filter(Boolean)
        .join(' · ')
    },
    // 订单要点：在 JS 侧组装好，模板只做遍历，避免出现 `<` `>` 字符（BUG-20）
    orderLines() {
      const room = this.booking.room
      if (this.isCourse) {
        return [
          { icon: 'icon-user', text: this.teacherText },
          { icon: 'icon-location', text: room?.name || '' },
        ].filter((line) => line.text)
      }
      return [
        { icon: 'icon-ticket', text: this.seatText },
        { icon: 'icon-clock', text: this.seatTimeText },
        { icon: 'icon-location', text: room?.address || room?.name || '' },
      ].filter((line) => line.text)
    },
    priceText() {
      return formatMoney(this.booking.total_price)
    },
    originalText() {
      return formatMoney(this.booking.original_price)
    },
    discountText() {
      return formatMoney(this.booking.discount_amount)
    },
    hasDiscount() {
      return Number(this.booking.discount_amount || 0) > 0
    },
    // BUG-20 防线：模板里不出现 `<` `>` 字符，比较结果都在 computed 里算好
    // value 供 @tap 回传所点星数，char 取自公用星级渲染，on 供上色
    starSlots() {
      return buildStarChars(this.rating).map((char, index) => ({
        value: index + 1,
        char,
        on: char === '★',
      }))
    },
    ratingMeta() {
      return this.rating ? RATING_META[this.rating - 1] : RATING_IDLE
    },
    ratingText() {
      return this.ratingMeta.text
    },
    ratingColor() {
      return this.ratingMeta.color
    },
    scoreText() {
      return Number(this.rating || 0).toFixed(1)
    },
    tagPool() {
      // 未打分时默认展示好评标签，仅 1-3 星切到差评标签
      return this.rating && this.rating <= 3 ? TAGS_NEG : TAGS_POS
    },
    tagNegative() {
      return this.tagPool === TAGS_NEG
    },
    contentEnough() {
      return this.content.trim().length >= CONTENT_SUGGEST_LENGTH
    },
    canAddImage() {
      return this.images.length < MAX_IMAGES
    },
    canSubmit() {
      return this.rating !== 0 && this.content.trim().length !== 0 && !this.submitting
    },
    submitText() {
      return this.submitting ? '提交中…' : '提交评价'
    },
    submitHint() {
      if (this.submitting) return '正在提交，请稍候'
      if (!this.rating) return '请先为本次体验打分'
      const length = this.content.trim().length
      if (length === 0) return '写下真实感受再提交'
      if (length < CONTENT_SUGGEST_LENGTH) return `再写 ${CONTENT_SUGGEST_LENGTH - length} 字更有帮助`
      return '审核通过后展示在课程与老师页'
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
      this.popStar = value
      setTimeout(() => {
        this.popStar = 0
      }, 340)
      if (this.rating === value) return
      // 标签池随星级切换；直接比对切换前后的池，避免与 tagPool 的判定条件各写一套而漂移
      const previousPool = this.tagPool
      this.rating = value
      if (this.tagPool !== previousPool) this.tags = []
    },

    tagClass(tag) {
      if (this.tags.indexOf(tag) === -1) return ''
      return this.tagNegative ? 'tag-on-neg' : 'tag-on'
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

    isPhraseUsed(phrase) {
      return this.content.indexOf(phrase.text) !== -1
    },

    // 快捷填入：已包含该句则不重复插入，否则以空格续写并截断到 500 字
    fillPhrase(phrase) {
      if (this.isPhraseUsed(phrase)) {
        uni.showToast({ title: '这句话已经填入过了', icon: 'none' })
        return
      }
      const base = this.content.replace(/\s+$/, '')
      const merged = base ? `${base} ${phrase.text}` : phrase.text
      if (merged.length > 500) {
        uni.showToast({ title: '评价内容已达 500 字上限', icon: 'none' })
        this.content = merged.slice(0, 500)
        return
      }
      this.content = merged
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
  background: linear-gradient(180deg, $bg-warm 0%, $bg-color 260rpx);
}

.submit-scroll {
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

/* === 卡片与标题 === */
.card {
  margin: 20rpx 24rpx 0;
  padding: 28rpx;
  background: $surface;
  border-radius: $radius-xl;
  box-shadow: $shadow-card;
}

.plain-card {
  padding: 0;
  overflow: hidden;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.head-bar {
  width: 6rpx;
  height: 26rpx;
  background: $gradient-primary;
  border-radius: 999rpx;
}

.head-title {
  font-size: 28rpx;
  font-weight: bold;
  color: $text-primary;
}

.head-star {
  font-size: 22rpx;
  color: $danger;
}

.head-extra {
  margin-left: auto;
  font-size: 20rpx;
  color: $text-muted;
}

/* === 订单信息 === */
.order-card {
  margin-top: 24rpx;
  padding: 28rpx 28rpx 24rpx;
}

.order-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.order-type {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding: 6rpx 16rpx 6rpx 12rpx;
  border-radius: 999rpx;
}

.order-type-seat {
  background: $primary-soft;
}

.order-type-course {
  background: rgba(108, 92, 231, 0.1);
}

.order-type-icon {
  font-size: 20rpx;
}

.order-type-seat .order-type-icon {
  color: $primary;
}

.order-type-course .order-type-icon {
  color: $purple;
}

.order-type-text {
  font-size: 20rpx;
  font-weight: 500;
}

.order-type-seat .order-type-text {
  color: $primary;
}

.order-type-course .order-type-text {
  color: $purple;
}

.order-status {
  padding: 6rpx 16rpx;
  border-radius: 999rpx;
}

.order-status-on {
  background: $success-light;
}

.order-status-on .order-status-text {
  color: $success;
}

.order-status-wait {
  background: $orange-light;
}

.order-status-wait .order-status-text {
  color: $orange;
}

.order-status-off {
  background: $bg-color;
}

.order-status-off .order-status-text {
  color: $text-muted;
}

.order-status-text {
  font-size: 20rpx;
}

.order-title {
  display: block;
  margin-top: 18rpx;
  font-size: 32rpx;
  font-weight: bold;
  line-height: 1.4;
  color: $text-primary;
}

.order-lines {
  margin-top: 18rpx;
}

.order-line {
  display: flex;
  align-items: center;
  gap: 14rpx;

  & + & {
    margin-top: 14rpx;
  }
}

.line-icon-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36rpx;
  height: 36rpx;
  background: $primary-soft;
  border-radius: 10rpx;
  flex-shrink: 0;
}

.line-icon {
  font-size: 20rpx;
  color: $primary;
}

.line-text {
  flex: 1;
  min-width: 0;
  font-size: 24rpx;
  color: $text-secondary;
}

.lesson-box {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 18rpx;
  padding: 18rpx;
  background: $surface-soft;
  border-radius: $radius-md;
}

.lesson-chip {
  padding: 6rpx 16rpx;
  background: $surface;
  border: 2rpx solid $border-soft;
  border-radius: 999rpx;
  font-size: 20rpx;
  color: $text-secondary;
}

.order-note {
  display: block;
  margin-top: 16rpx;
  font-size: 20rpx;
  color: $text-muted;
}

.order-divider {
  display: flex;
  justify-content: space-between;
  margin-top: 24rpx;
}

.divider-dash {
  width: 10rpx;
  height: 2rpx;
  background: $border-color;
  border-radius: 2rpx;
}

.order-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20rpx;
}

.order-no {
  font-size: 20rpx;
  color: $text-muted;
}

.order-price {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.price-origin {
  font-size: 20rpx;
  color: $text-muted;
  text-decoration: line-through;
}

.price-symbol {
  font-size: 22rpx;
  font-weight: 500;
  color: $primary;
}

.price-value {
  font-size: 34rpx;
  font-weight: bold;
  color: $primary;
}

.order-discount {
  display: block;
  margin-top: 10rpx;
  font-size: 20rpx;
  color: $orange;
  text-align: right;
}

/* === 综合评分 === */
.rating-body {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 24rpx;
}

.rating-stars {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.star {
  font-size: 56rpx;
  line-height: 1;
  color: #e1e5ef;
  transition: color 0.2s $ease-out;
}

.star-on {
  color: #ffb400;
}

@keyframes starPop {
  0% {
    transform: scale(1);
  }
  45% {
    transform: scale(1.3);
  }
  100% {
    transform: scale(1);
  }
}

.star-pop {
  animation: starPop 0.32s $ease-out;
}

.rating-desc {
  flex: 1;
  min-width: 0;
}

.rating-text {
  display: block;
  font-size: 26rpx;
  font-weight: bold;
}

.rating-score {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
  flex-shrink: 0;
}

.score-num {
  font-size: 48rpx;
  font-weight: bold;
  line-height: 1;
  color: $text-primary;
}

.score-unit {
  font-size: 20rpx;
  color: $text-muted;
}

/* === 标签 === */
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 24rpx;
}

.tag {
  padding: 12rpx 24rpx;
  background: $bg-color;
  border: 2rpx solid transparent;
  border-radius: 999rpx;
  font-size: 22rpx;
  color: $text-secondary;
  transition: all 0.18s $ease-out;
}

.tag-on {
  background: $primary-light;
  border-color: rgba(79, 110, 247, 0.35);
  color: $primary;
  font-weight: 500;
}

.tag-on-neg {
  background: $danger-light;
  border-color: rgba(255, 107, 107, 0.3);
  color: $danger;
  font-weight: 500;
}

/* === 评价内容 === */
.counter {
  margin-left: auto;
  font-size: 20rpx;
  color: $text-muted;
}

.counter-ok {
  color: $success;
}

.content-input {
  width: 100%;
  height: 220rpx;
  margin-top: 20rpx;
  padding: 22rpx;
  box-sizing: border-box;
  background: #f8f9fc;
  border: 2rpx solid transparent;
  border-radius: $radius-md;
  font-size: 26rpx;
  line-height: 1.7;
  color: $text-primary;
  transition: border-color 0.2s $ease-out, background 0.2s $ease-out;
}

.content-input-focus {
  background: $surface;
  border-color: rgba(79, 110, 247, 0.4);
}

.content-placeholder {
  color: $text-muted;
}

/* === 快捷填入 === */
.quick-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 20rpx;
}

.quick-label {
  display: flex;
  align-items: center;
  gap: 6rpx;
  flex-shrink: 0;
}

.quick-icon {
  font-size: 20rpx;
  color: $orange;
}

.quick-label-text {
  font-size: 20rpx;
  color: $text-muted;
}

.quick-scroll {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
}

.quick-list {
  display: inline-flex;
  align-items: center;
  gap: 12rpx;
}

.quick-chip {
  padding: 10rpx 22rpx;
  background: $primary-soft;
  border: 2rpx solid rgba(79, 110, 247, 0.16);
  border-radius: 999rpx;
  font-size: 22rpx;
  color: $primary;
  white-space: nowrap;
  transition: all 0.18s $ease-out;
}

.quick-chip-used {
  background: $success-light;
  border-color: rgba(7, 193, 96, 0.24);
  color: $success;
}

/* === 图片 === */
.image-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 24rpx;
}

.image-item {
  position: relative;
  width: 168rpx;
  height: 168rpx;
}

.image-thumb {
  width: 168rpx;
  height: 168rpx;
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
  gap: 10rpx;
  width: 168rpx;
  height: 168rpx;
  box-sizing: border-box;
  background: $surface-soft;
  border: 2rpx dashed rgba(79, 110, 247, 0.28);
  border-radius: $radius-md;
  transition: background 0.18s $ease-out;
}

.image-add-busy {
  border-style: solid;
  border-color: $border-color;
}

.image-add-icon-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52rpx;
  height: 52rpx;
  background: $primary-soft;
  border-radius: 50%;
}

.image-add-icon {
  font-size: 32rpx;
  line-height: 1;
  color: $primary;
}

.image-add-text {
  font-size: 20rpx;
  color: $text-muted;
}

/* === 匿名与提示 === */
.switch-row {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 28rpx;
}

.switch-icon-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  background: $primary-soft;
  border-radius: $radius-md;
  flex-shrink: 0;
}

.switch-icon {
  font-size: 26rpx;
  color: $primary;
}

.switch-text {
  flex: 1;
  min-width: 0;
}

.switch-title {
  display: block;
  font-size: 26rpx;
  font-weight: 500;
  color: $text-primary;
}

.switch-desc {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: $text-muted;
}

.switch-ctl {
  transform: scale(0.82);
  flex-shrink: 0;
}

.notice {
  display: flex;
  align-items: flex-start;
  gap: 10rpx;
  padding: 20rpx 28rpx;
  background: $surface-soft;
  border-top: 2rpx solid rgba(0, 0, 0, 0.03);
}

.notice-icon {
  margin-top: 4rpx;
  font-size: 20rpx;
  color: $primary;
  flex-shrink: 0;
}

.notice-text {
  flex: 1;
  font-size: 20rpx;
  line-height: 1.6;
  color: $text-muted;
}

/* === 已评价状态 === */
.state-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 120rpx 24rpx 0;
  padding: 64rpx 40rpx;
  background: $surface;
  border-radius: $radius-xl;
  box-shadow: $shadow-card;
}

.state-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 108rpx;
  height: 108rpx;
  background: $success-light;
  border-radius: 50%;
}

.state-icon {
  font-size: 52rpx;
  color: $success;
}

.state-title {
  margin-top: 28rpx;
  font-size: 32rpx;
  font-weight: bold;
  color: $text-primary;
}

.state-desc {
  margin-top: 12rpx;
  font-size: 22rpx;
  color: $text-muted;
}

.state-btn {
  margin-top: 36rpx;
  padding: 18rpx 52rpx;
  background: $gradient-primary;
  border-radius: 999rpx;
  box-shadow: $shadow-md;
}

.state-btn-text {
  font-size: 26rpx;
  font-weight: 500;
  color: $white;
}

/* === 底部提交栏 === */
.submit-bar {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex-shrink: 0;
  padding: 18rpx 24rpx;
  padding-bottom: calc(18rpx + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.96);
  border-top: 2rpx solid rgba(0, 0, 0, 0.03);
  box-shadow: $shadow-bottom;
}

.submit-hint {
  flex-shrink: 0;
  max-width: 240rpx;
}

.hint-label {
  display: block;
  font-size: 18rpx;
  color: $text-muted;
}

.hint-value {
  display: block;
  margin-top: 4rpx;
  font-size: 22rpx;
  font-weight: 500;
  color: $orange;
}

.hint-ok {
  color: $success;
}

.submit-btn {
  flex: 1;
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $gradient-primary;
  border-radius: 999rpx;
  box-shadow: $shadow-float;
  transition: opacity 0.2s $ease-out, box-shadow 0.2s $ease-out;
}

.submit-btn-off {
  background: #c7d0f5;
  box-shadow: none;
}

.submit-btn-text {
  font-size: 30rpx;
  font-weight: bold;
  color: $white;
}

.scroll-bottom-space {
  height: 40rpx;
}
</style>
