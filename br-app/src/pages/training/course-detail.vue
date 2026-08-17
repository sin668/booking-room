<template>
  <view class="page">
    <!-- 自定义导航栏 -->
    <view class="nav-overlay">
      <view :style="{ height: statusBarHeight + 'px' }" />
      <view class="nav-bar">
        <view class="nav-btn" @tap="onBack">
          <view class="nav-chevron" />
        </view>
        <view class="nav-placeholder" />
        <view class="nav-btn" @tap="onShare">
          <view class="nav-share">
            <view class="nav-share-dot top" />
            <view class="nav-share-dot left" />
            <view class="nav-share-dot right" />
            <view class="nav-share-line one" />
            <view class="nav-share-line two" />
          </view>
        </view>
      </view>
    </view>

    <!-- 内容区 -->
    <scroll-view class="content" scroll-y>
      <!-- Hero 区域 -->
      <view class="hero">
        <image
          v-if="heroImage"
          class="hero-image"
          :src="heroImage"
          mode="aspectFill"
        />
        <view class="hero-gradient" />
      </view>

      <!-- 课程信息卡 -->
      <view class="info-card animate-in">
        <!-- 标签行 -->
        <view class="tags-row">
          <view
            v-for="(tag, idx) in tagsList"
            :key="idx"
            :class="['tag', idx === 0 && course.is_hot ? 'tag-hot' : 'tag-blue']"
          >
            <text class="tag-text">{{ tag }}</text>
          </view>
        </view>

        <!-- 课程名称 -->
        <text class="course-name">{{ course.name || '课程详情' }}</text>

        <!-- 评分 + 已学人数 + 课时数 -->
        <view class="stats-row">
          <view class="stats-item">
            <text class="star-icon">★</text>
            <text class="stats-value">{{ course.rating || '0' }}</text>
            <text class="stats-sub">({{ course.review_count || 0 }})</text>
          </view>
          <view class="stats-item">
            <text class="stats-text">{{ course.enrollment_count || 0 }}人已学</text>
          </view>
          <view class="stats-item">
            <text class="stats-text">{{ course.lesson_count || lessons.length }}课时</text>
          </view>
        </view>

        <!-- 价格区域 -->
        <view class="price-area">
          <view class="price-main">
            <text class="price-symbol">¥</text>
            <text class="price-value">{{ course.price || 0 }}</text>
            <text class="price-unit">/课时</text>
          </view>
          <view v-if="course.is_hot" class="hot-badge">
            <text class="hot-text">本周热销Top3</text>
          </view>
        </view>
      </view>

      <!-- 教师信息卡 -->
      <view v-if="teacher" class="teacher-card animate-in" style="animation-delay: 0.08s;" @tap="onTeacherTap">
        <view class="teacher-left">
          <view class="teacher-avatar-wrap">
            <image
              v-if="teacher.avatar"
              class="teacher-avatar"
              :src="teacher.avatar"
              mode="aspectFill"
            />
            <view v-else class="teacher-avatar-ph" />
            <view class="teacher-verify">
              <text class="teacher-verify-icon">✓</text>
            </view>
          </view>
        </view>
        <view class="teacher-body">
          <view class="teacher-name-row">
            <text class="teacher-name">{{ teacher.name }}</text>
            <view class="teacher-badge">
              <text class="teacher-badge-text">认证讲师</text>
            </view>
          </view>
          <text v-if="teacher.bio" class="teacher-bio">{{ teacher.bio }}</text>
          <view class="teacher-stats">
            <text class="star-icon sm">★</text>
            <text class="teacher-rating-val">{{ teacher.rating || '0' }}</text>
            <text class="teacher-students">· {{ teacher.student_count || 0 }}位学员</text>
          </view>
        </view>
        <view class="teacher-arrow">
          <view class="arrow-icon" />
        </view>
      </view>

      <!-- 课程介绍区域 -->
      <view class="section intro-section animate-in" style="animation-delay: 0.16s;">
        <view class="section-header">
          <view class="section-title-group">
            <view class="section-bar" />
            <text class="section-title">课程介绍</text>
          </view>
        </view>
        <text class="intro-text">{{ course.description || '暂无课程介绍' }}</text>
        <view class="feature-grid">
          <view class="feature-item">
            <text class="feature-icon">◎</text>
            <text class="feature-text">高频考点精准梳理</text>
          </view>
          <view class="feature-item">
            <text class="feature-icon">◎</text>
            <text class="feature-text">三步答题法</text>
          </view>
          <view class="feature-item">
            <text class="feature-icon">◎</text>
            <text class="feature-text">配套资料免费送</text>
          </view>
          <view class="feature-item">
            <text class="feature-icon">◎</text>
            <text class="feature-text">课后答疑</text>
          </view>
        </view>
      </view>

      <!-- 课程目录区域 -->
      <view class="section lessons-section animate-in" style="animation-delay: 0.24s;">
        <view class="section-header">
          <view class="section-title-group">
            <view class="section-bar" />
            <text class="section-title">课程目录</text>
          </view>
          <text class="section-sub">共{{ lessons.length }}课时</text>
        </view>
        <view v-if="lessons.length === 0" class="empty-state">
          <text class="empty-text">暂无课程目录</text>
        </view>
        <view v-else class="lessons-list">
          <view
            v-for="(lesson, idx) in displayLessons"
            :key="lesson.id || idx"
            class="lesson-item"
          >
            <view :class="['lesson-icon-wrap', lesson.is_free_preview ? 'active' : 'locked']">
              <text :class="['lesson-icon', lesson.is_free_preview ? 'play' : 'lock']">
                {{ lesson.is_free_preview ? '▶' : '◼' }}
              </text>
            </view>
            <view class="lesson-body">
              <text class="lesson-title">{{ lesson.title }}</text>
              <text class="lesson-meta">
                {{ lesson.duration_minutes ? lesson.duration_minutes + '分钟' : '45分钟' }}{{ lesson.is_free_preview ? ' · 免费试听' : '' }}
              </text>
            </view>
            <text :class="['lesson-status', lesson.is_free_preview ? 'available' : '']">
              {{ lesson.is_free_preview ? '可试听' : '付费' }}
            </text>
          </view>
          <view v-if="lessons.length > 4" class="expand-btn" @tap="toggleLessons">
            <text class="expand-text">
              {{ lessonsExpanded ? '收起' : '查看全部' + lessons.length + '课时' }}
              <text class="expand-arrow">{{ lessonsExpanded ? '▲' : '▼' }}</text>
            </text>
          </view>
        </view>
      </view>

      <!-- 学员评价区域 -->
      <view class="section reviews-section animate-in" style="animation-delay: 0.32s;">
        <view class="section-header">
          <view class="section-title-group">
            <view class="section-bar" />
            <text class="section-title">学员评价</text>
          </view>
          <view class="review-summary">
            <text class="star-icon sm">★</text>
            <text class="review-avg">{{ course.rating || '0' }}</text>
            <text class="review-count">({{ course.review_count || 0 }}条)</text>
          </view>
        </view>
        <view
          v-for="(review, idx) in reviews"
          :key="idx"
          :class="['review-item', idx < reviews.length - 1 ? 'bordered' : '']"
        >
          <view class="review-top">
            <view class="review-avatar-ph" />
            <view class="review-info">
              <text class="review-name">{{ review.name }}</text>
              <view class="review-stars">
                <text
                  v-for="s in review.rating"
                  :key="s"
                  class="star-icon xs"
                >★</text>
              </view>
            </view>
            <text class="review-date">{{ review.date }}</text>
          </view>
          <text class="review-content">{{ review.content }}</text>
        </view>
      </view>

      <!-- 相关课程 -->
      <view v-if="relatedCourses.length > 0" class="section related-section animate-in" style="animation-delay: 0.40s;">
        <view class="section-header">
          <view class="section-title-group">
            <view class="section-bar" />
            <text class="section-title">相关课程</text>
          </view>
        </view>
        <scroll-view class="related-scroll" scroll-x :show-scrollbar="false">
          <view class="related-list">
            <view
              v-for="rc in relatedCourses"
              :key="rc.id"
              class="related-card"
              @tap="onRelatedCourse(rc)"
            >
              <image
                v-if="rc.cover_image"
                class="related-cover"
                :src="rc.cover_image"
                mode="aspectFill"
              />
              <view v-else class="related-cover-ph" />
              <view class="related-body">
                <text class="related-name">{{ rc.name }}</text>
                <view class="related-price">
                  <text class="related-price-val">¥{{ rc.price }}</text>
                  <text class="related-price-unit">/课时</text>
                </view>
              </view>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 底部留白 -->
      <view style="height: 140rpx;" />
    </scroll-view>

    <!-- 底部操作栏 -->
    <view class="bottom-bar">
      <view class="fav-btn" @tap="onToggleFav">
        <text :class="['heart-icon', { active: isFav }]">♥</text>
      </view>
      <view class="bottom-price">
        <text class="bottom-price-label">单课时</text>
        <view class="bottom-price-row">
          <text class="bottom-price-val">¥{{ course.price || 0 }}</text>
          <text class="bottom-price-suffix">起</text>
        </view>
      </view>
      <view class="book-btn" @tap="onBook">
        <text class="book-btn-text">立即预约</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getCourseDetail } from '@/api/training'
import { followCourse, isCourseFollowed, unfollowCourse } from '@/services/followedCourses'

export default {
  data() {
    return {
      statusBarHeight: 0,
      courseId: null,
      course: {},
      teacher: null,
      room: null,
      lessons: [],
      relatedCourses: [],
      loading: true,
      isFav: false,
      lessonsExpanded: false,
      reviews: [
        { name: '张同学', rating: 5, content: '课程内容很充实，老师讲解很到位。', date: '2025-12-01' },
        { name: '李同学', rating: 4, content: '整体不错，希望能增加更多实操环节。', date: '2025-11-20' },
      ],
    }
  },

  computed: {
    displayLessons() {
      if (this.lessonsExpanded || this.lessons.length <= 4) return this.lessons
      return this.lessons.slice(0, 4)
    },

    heroImage() {
      return this.course.cover_image || ''
    },

    tagsList() {
      const tags = this.course.tags || []
      if (this.course.is_hot) {
        return ['热销', ...tags]
      }
      return tags
    },
  },

  onLoad(options) {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
    if (options.course_id) {
      this.courseId = Number(options.course_id)
      this.isFav = isCourseFollowed(this.courseId)
      this.loadCourseDetail()
    }
  },

  methods: {
    async loadCourseDetail() {
      this.loading = true
      try {
        const data = await getCourseDetail(this.courseId)
        if (data) {
          this.course = data.course || data
          this.teacher = data.teacher || this.course.teacher || null
          this.lessons = data.lessons || this.course.lessons || []
          this.relatedCourses = data.related_courses || []
          this.isFav = isCourseFollowed(this.courseId)
        }
      } catch {
        // keep defaults
      } finally {
        this.loading = false
      }
    },

    onBack() {
      uni.navigateBack()
    },

    onShare() {
      // placeholder
    },

    async onToggleFav() {
      if (!this.courseId) return

      if (this.isFav) {
        try {
          await unfollowCourse(this.courseId)
          this.isFav = false
          uni.showToast({ title: '已取消关注', icon: 'none' })
        } catch {
          uni.showToast({ title: '取消关注失败，请重试', icon: 'none' })
        }
        return
      }

      try {
        await followCourse({
          ...this.course,
          id: this.course.id || this.courseId,
          name: this.course.name || '未命名课程',
        })
        this.isFav = true
        uni.showToast({ title: '已加入关注课程', icon: 'none' })
      } catch {
        uni.showToast({ title: '关注失败，请重试', icon: 'none' })
      }
    },

    onBook() {
      if (!this.courseId) return
      uni.navigateTo({
        url: `/pages/training/course-booking?course_id=${this.courseId}`,
      })
    },

    toggleLessons() {
      this.lessonsExpanded = !this.lessonsExpanded
    },

    onTeacherTap() {
      if (!this.teacher || !this.teacher.id) return
      uni.navigateTo({
        url: `/pages/teacher/profile?teacher_id=${this.teacher.id}`,
      })
    },

    onRelatedCourse(course) {
      if (!course || !course.id) return
      uni.redirectTo({ url: '/pages/training/course-detail?course_id=' + course.id })
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  background: linear-gradient(180deg, #eef1fb 0, $bg-color 520rpx);
  min-height: 100vh;
}

/* === 导航栏 === */
.nav-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 28rpx;
}

.nav-btn {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.28);
  border: 1rpx solid rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(35, 41, 68, 0.16);
}

.nav-btn:active {
  transform: scale(0.96);
}

.nav-chevron {
  width: 20rpx;
  height: 20rpx;
  border-left: 4rpx solid $white;
  border-bottom: 4rpx solid $white;
  transform: rotate(45deg);
  margin-left: 8rpx;
}

.nav-share {
  position: relative;
  width: 34rpx;
  height: 34rpx;
}

.nav-share-dot {
  position: absolute;
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: $white;
}

.nav-share-dot.top { top: 0; right: 2rpx; }
.nav-share-dot.left { left: 2rpx; bottom: 4rpx; }
.nav-share-dot.right { right: 0; bottom: 2rpx; }

.nav-share-line {
  position: absolute;
  height: 3rpx;
  width: 22rpx;
  border-radius: 3rpx;
  background: $white;
  transform-origin: left center;
}

.nav-share-line.one { left: 9rpx; top: 12rpx; transform: rotate(152deg); }
.nav-share-line.two { left: 11rpx; top: 24rpx; transform: rotate(12deg); }

.nav-placeholder {
  flex: 1;
}

.content {
  height: 100vh;
}

/* === Hero === */
.hero {
  position: relative;
  height: 420rpx;
  overflow: hidden;
  background: #eef1fb;
}

.hero-image {
  width: 100%;
  height: 100%;
}

.hero-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(24, 31, 54, 0.18) 0%, rgba(24, 31, 54, 0.02) 40%, rgba(24, 31, 54, 0.42) 100%);
}

/* === 课程信息卡 === */
.info-card {
  margin: -42rpx 28rpx 0;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 32rpx;
  padding: 30rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  position: relative;
  z-index: 10;
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: 14rpx;
}

.tag {
  padding: 7rpx 18rpx;
  border-radius: 999rpx;
}

.tag-hot {
  background: rgba(255, 71, 87, 0.1);
}

.tag-hot .tag-text {
  color: #FF4757;
  font-size: 22rpx;
  font-weight: 500;
}

.tag-blue {
  background: $primary-soft;
  border: 1rpx solid rgba(79, 110, 247, 0.08);
}

.tag-blue .tag-text {
  color: $primary;
  font-size: 22rpx;
  font-weight: 500;
}

.course-name {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-primary;
  line-height: 1.3;
  display: block;
}

.stats-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 16rpx;
}

.stats-item {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.star-icon {
  color: #ffc107;
  font-size: 28rpx;
}

.star-icon.sm {
  font-size: 22rpx;
}

.star-icon.xs {
  font-size: 18rpx;
}

.stats-value {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.stats-sub {
  font-size: 22rpx;
  color: $text-muted;
}

.stats-text {
  font-size: 24rpx;
  color: $text-secondary;
}

.price-area {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid rgba(99, 110, 114, 0.08);
}

.price-main {
  display: flex;
  align-items: baseline;
}

.price-symbol {
  font-size: 28rpx;
  font-weight: 700;
  color: $primary;
}

.price-value {
  font-size: 44rpx;
  font-weight: 700;
  color: $primary;
  line-height: 1;
}

.price-unit {
  font-size: 22rpx;
  color: $text-muted;
  margin-left: 4rpx;
}

.hot-badge {
  display: flex;
  align-items: center;
  gap: 4rpx;
}

.hot-text {
  font-size: 22rpx;
  color: #e67900;
  font-weight: 500;
}

/* === 教师信息卡 === */
.teacher-card {
  margin: 24rpx 28rpx 0;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 32rpx;
  padding: 28rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.teacher-card:active {
  background: $surface-soft;
}

.teacher-avatar-wrap {
  position: relative;
  flex-shrink: 0;
}

.teacher-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
}

.teacher-avatar-ph {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: $surface-soft;
}

.teacher-verify {
  position: absolute;
  right: -4rpx;
  bottom: -4rpx;
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  background: $success;
  border: 4rpx solid $white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.teacher-verify-icon {
  font-size: 18rpx;
  color: $white;
  font-weight: 700;
}

.teacher-body {
  flex: 1;
  min-width: 0;
}

.teacher-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.teacher-name {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.teacher-badge {
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  background: $primary-soft;
}

.teacher-badge-text {
  font-size: 20rpx;
  color: $primary;
  font-weight: 500;
}

.teacher-bio {
  font-size: 22rpx;
  color: $text-muted;
  margin-top: 6rpx;
  display: block;
}

.teacher-stats {
  display: flex;
  align-items: center;
  gap: 6rpx;
  margin-top: 8rpx;
}

.teacher-rating-val {
  font-size: 24rpx;
  font-weight: 500;
  color: $text-primary;
}

.teacher-students {
  font-size: 22rpx;
  color: $text-muted;
}

.teacher-arrow {
  flex-shrink: 0;
}

.arrow-icon {
  width: 16rpx;
  height: 16rpx;
  border-right: 4rpx solid $text-muted;
  border-bottom: 4rpx solid $text-muted;
  transform: rotate(-45deg);
}

/* === 通用 section === */
.section {
  margin: 28rpx 28rpx 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.section-title-group {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.section-bar {
  width: 6rpx;
  height: 28rpx;
  border-radius: 6rpx;
  background: $primary;
}

.section-title {
  font-size: 31rpx;
  font-weight: 700;
  color: $text-primary;
}

.section-sub {
  font-size: 24rpx;
  color: $text-muted;
}

/* === 课程介绍 === */
.intro-section {
  background: $surface;
  border-radius: 32rpx;
  padding: 28rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.intro-text {
  font-size: 26rpx;
  line-height: 1.7;
  color: $text-secondary;
  display: block;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14rpx;
  margin-top: 20rpx;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10rpx;
  background: $primary-soft;
  border-radius: 16rpx;
  padding: 16rpx 20rpx;
}

.feature-icon {
  font-size: 22rpx;
  color: $primary;
}

.feature-text {
  font-size: 24rpx;
  color: $text-secondary;
}

/* === 课程目录 === */
.lessons-section {
  background: $surface;
  border-radius: 32rpx;
  padding: 28rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.lessons-list {
  display: flex;
  flex-direction: column;
}

.lesson-item {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 22rpx 0;
  border-bottom: 1rpx solid rgba(99, 110, 114, 0.06);
}

.lesson-item:last-child {
  border-bottom: none;
}

.lesson-icon-wrap {
  width: 60rpx;
  height: 60rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.lesson-icon-wrap.active {
  background: rgba(7, 193, 96, 0.1);
}

.lesson-icon-wrap.locked {
  background: $surface-soft;
}

.lesson-icon {
  font-size: 22rpx;
}

.lesson-icon.play {
  color: $success;
}

.lesson-icon.lock {
  color: $text-muted;
}

.lesson-body {
  flex: 1;
  min-width: 0;
}

.lesson-title {
  font-size: 26rpx;
  color: $text-primary;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lesson-meta {
  font-size: 22rpx;
  color: $text-muted;
  margin-top: 4rpx;
  display: block;
}

.lesson-status {
  font-size: 24rpx;
  color: $text-muted;
  flex-shrink: 0;
}

.lesson-status.available {
  color: $success;
  font-weight: 500;
}

.expand-btn {
  padding: 20rpx 0 4rpx;
  text-align: center;
}

.expand-text {
  font-size: 26rpx;
  color: $primary;
  font-weight: 500;
}

.expand-arrow {
  font-size: 20rpx;
  color: $primary;
  margin-left: 6rpx;
}

/* === 学员评价 === */
.reviews-section {
  background: $surface;
  border-radius: 32rpx;
  padding: 28rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.review-summary {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.review-avg {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-primary;
}

.review-count {
  font-size: 22rpx;
  color: $text-muted;
}

.review-item {
  padding: 20rpx 0;
}

.review-item.bordered {
  border-bottom: 1rpx solid rgba(99, 110, 114, 0.06);
  margin-bottom: 4rpx;
}

.review-top {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-bottom: 12rpx;
}

.review-avatar-ph {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background: $surface-soft;
  flex-shrink: 0;
}

.review-info {
  flex: 1;
  min-width: 0;
}

.review-name {
  font-size: 26rpx;
  font-weight: 500;
  color: $text-primary;
  display: block;
}

.review-stars {
  display: flex;
  gap: 2rpx;
  margin-top: 4rpx;
}

.review-date {
  font-size: 22rpx;
  color: $text-muted;
  flex-shrink: 0;
}

.review-content {
  font-size: 26rpx;
  line-height: 1.6;
  color: $text-secondary;
  display: block;
}

/* === 相关课程 === */
.related-section {
  margin-top: 32rpx;
}

.related-scroll {
  white-space: nowrap;
}

.related-list {
  display: inline-flex;
  gap: 18rpx;
  padding-bottom: 4rpx;
}

.related-card {
  width: 280rpx;
  background: $surface;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  flex-shrink: 0;
}

.related-card:active {
  opacity: 0.85;
}

.related-cover {
  width: 100%;
  height: 168rpx;
}

.related-cover-ph {
  width: 100%;
  height: 168rpx;
  background: $surface-soft;
}

.related-body {
  padding: 16rpx 18rpx;
}

.related-name {
  font-size: 26rpx;
  font-weight: 500;
  color: $text-primary;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.related-price {
  display: flex;
  align-items: baseline;
  margin-top: 8rpx;
}

.related-price-val {
  font-size: 28rpx;
  font-weight: 700;
  color: $primary;
}

.related-price-unit {
  font-size: 20rpx;
  color: $text-muted;
  margin-left: 4rpx;
}

/* === 底部操作栏 === */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 18rpx 28rpx;
  padding-bottom: calc(18rpx + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.98);
  border-top: 1rpx solid rgba(45, 52, 54, 0.06);
  box-shadow: $shadow-bottom;
  backdrop-filter: blur(18rpx);
  z-index: 100;
}

.fav-btn {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  border: 2rpx solid $border-color;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: $white;
}

.heart-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  font-size: 50rpx;
  line-height: 56rpx;
  color: $white;
  -webkit-text-stroke: 3rpx $text-muted;
  font-family: Arial, Helvetica, sans-serif;
  transform: translateY(1rpx);
}

.heart-icon.active {
  color: $danger;
  -webkit-text-stroke-color: $danger;
}

.bottom-price {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.bottom-price-label {
  font-size: 20rpx;
  color: $text-muted;
  line-height: 1.1;
}

.bottom-price-row {
  display: flex;
  align-items: baseline;
}

.bottom-price-val {
  font-size: 36rpx;
  font-weight: 700;
  color: $primary;
  line-height: 1.1;
}

.bottom-price-suffix {
  font-size: 22rpx;
  color: $text-muted;
  margin-left: 2rpx;
}

.book-btn {
  flex: 1;
  height: 92rpx;
  background: $gradient-primary;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow-float;
}

.book-btn:active {
  background: $primary-dark;
  transform: translateY(1rpx);
}

.book-btn-text {
  font-size: 30rpx;
  font-weight: 600;
  color: $white;
}

/* === 动画 === */
.animate-in {
  animation: fadeInUp 0.4s ease both;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* === 空状态 === */
.empty-state {
  padding: 40rpx 0;
  text-align: center;
}

.empty-text {
  font-size: 26rpx;
  color: $text-muted;
}
</style>
