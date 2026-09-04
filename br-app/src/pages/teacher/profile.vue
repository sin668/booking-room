<template>
  <view class="page">
    <!-- 顶部导航 -->
    <view class="nav-overlay">
      <view :style="{ height: statusBarHeight + 'px' }" />
      <view class="nav-bar">
        <view class="nav-btn" @tap="onBack">
          <view class="nav-chevron" />
        </view>
        <view class="nav-placeholder" />
        <view class="nav-btn" @tap="onToggleFav">
          <text :class="['nav-heart', { active: isFav }]">♥</text>
        </view>
      </view>
    </view>

    <scroll-view class="content" scroll-y>
      <!-- Hero 区 -->
      <view class="hero">
        <image
          v-if="teacher.avatar"
          class="hero-image"
          :src="teacher.avatar"
          mode="aspectFill"
        />
        <view class="hero-gradient" />
        <view class="hero-info">
          <view class="hero-bottom">
            <view class="hero-avatar-wrap">
              <image
                v-if="teacher.avatar"
                class="hero-avatar"
                :src="teacher.avatar"
                mode="aspectFill"
              />
              <view v-else class="hero-avatar-ph">
                <text class="hero-avatar-text">{{ avatarText }}</text>
              </view>
              <view class="hero-avatar-badge">
                <text class="hero-badge-icon">✓</text>
              </view>
            </view>
            <view class="hero-text">
              <view class="hero-name-row">
                <text class="hero-name">{{ teacher.name || '教师' }}</text>
                <view class="hero-tag">
                  <text class="hero-tag-text">认证讲师</text>
                </view>
              </view>
              <text class="hero-sub">{{ heroSub }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 统计行 -->
      <view class="stats-card animate-in delay-1">
        <view class="stats-grid">
          <view class="stats-item">
            <text class="stats-value stats-primary">{{ teacher.student_count || 0 }}</text>
            <text class="stats-label">学员数量</text>
          </view>
          <view class="stats-item stats-border">
            <text class="stats-value stats-orange">{{ courses.length }}</text>
            <text class="stats-label">授课课程</text>
          </view>
          <view class="stats-item stats-border">
            <text class="stats-value stats-green">{{ ratingText }}</text>
            <text class="stats-label">综合评分</text>
          </view>
        </view>
      </view>

      <!-- 个人简介 -->
      <view v-if="teacher.bio" class="section animate-in delay-2">
        <view class="section-header">
          <view class="section-bar" />
          <text class="section-title">个人简介</text>
        </view>
        <text class="bio-text">{{ teacher.bio }}</text>
      </view>

      <!-- 资质认证（读接口数据，空则隐藏） -->
      <view v-if="qualifications.length" class="section animate-in delay-2">
        <view class="section-header">
          <view class="section-bar" />
          <text class="section-title">资质认证</text>
        </view>
        <view class="qual-list">
          <template v-for="(q, idx) in qualifications" :key="idx">
            <view v-if="idx > 0" class="qual-divider" />
            <view class="qual-item">
              <view :class="['qual-icon-wrap', `qual-bg-${q.color}`]">
                <text :class="['qual-icon', `qual-icon-${q.color}`]">{{ q.icon }}</text>
              </view>
              <view class="qual-body">
                <text class="qual-name">{{ q.name }}</text>
                <text v-if="q.sub" class="qual-sub">{{ q.sub }}</text>
              </view>
              <text class="qual-check">✓</text>
            </view>
          </template>
        </view>
      </view>

      <!-- 教学特色（读接口数据，空则隐藏） -->
      <view v-if="teachingTags.length" class="section animate-in delay-3">
        <view class="section-header">
          <view class="section-bar" />
          <text class="section-title">教学特色</text>
        </view>
        <view class="tag-list">
          <view v-for="(t, idx) in teachingTags" :key="idx" :class="['tag-pill', `tag-bg-${t.color}`]">
            <text :class="['tag-text', `tag-text-${t.color}`]">{{ t.label }}</text>
          </view>
        </view>
      </view>

      <!-- 主讲课程列表 -->
      <view class="courses-section animate-in delay-3">
        <view class="courses-header">
          <text class="courses-title">主讲课程</text>
          <text class="courses-count">共{{ courses.length }}门</text>
        </view>
        <view v-if="courses.length === 0" class="empty-state">
          <text class="empty-text">暂无课程</text>
        </view>
        <view v-else class="course-list">
          <view v-for="course in courses" :key="course.id" class="course-card" @tap="onCourseDetail(course)">
            <image class="course-cover" :src="course.cover_image || ''" mode="aspectFill" />
            <view class="course-body">
              <view class="course-top">
                <text class="course-name">{{ course.name }}</text>
              </view>
              <text class="course-lesson-info">共{{ course.lesson_count || 0 }}课时 · 含资料</text>
              <view class="course-rating-row">
                <view class="rating-stars">
                  <text class="star-icon">★</text>
                  <text class="rating-value">{{ course.rating }}</text>
                </view>
                <text class="rating-count">{{ course.enrollment_count }}人</text>
              </view>
              <view class="course-bottom">
                <view class="course-price-wrap">
                  <text class="course-price">¥{{ course.price }}</text>
                  <text class="price-unit">/课时</text>
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 学员评价（静态占位数据） -->
      <view class="section animate-in delay-4">
        <view class="section-header">
          <view class="section-bar" />
          <text class="section-title">学员评价</text>
          <text class="section-sub">{{ reviews.length }}条</text>
        </view>
        <view v-for="(review, idx) in reviews" :key="idx" class="review-item">
          <view v-if="idx > 0" class="review-divider" />
          <view class="review-header">
            <image class="review-avatar" :src="review.avatar" mode="aspectFill" />
            <view class="review-meta">
              <text class="review-name">{{ review.name }}</text>
              <view class="review-stars">
                <text v-for="s in 5" :key="s" class="review-star">★</text>
              </view>
            </view>
            <text class="review-time">{{ review.time }}</text>
          </view>
          <text class="review-content">{{ review.content }}</text>
        </view>
        <view class="review-more-btn">
          <text class="review-more-text">查看全部评价</text>
        </view>
      </view>

      <!-- 底部占位 -->
      <view style="height: 180rpx;" />
    </scroll-view>

    <!-- 底部操作栏 -->
    <view class="bottom-bar">
      <view class="chat-btn">
        <text class="chat-icon">✎</text>
      </view>
      <view class="action-btn" @tap="onBackToCourses">
        <text class="action-btn-text">返回课程</text>
      </view>
    </view>
  </view>
</template>

<script>
import { onLoad } from '@dcloudio/uni-app'
import { getTeacherDetail } from '@/api/teacher'
import { followTeacher, unfollowTeacher, isTeacherFollowed } from '@/services/followedTeachers'

export default {
  data() {
    return {
      statusBarHeight: 0,
      teacherId: null,
      teacher: {},
      courses: [],
      isFav: false,
      loading: true,
      reviews: [
        {
          avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=60&h=60&fit=crop&crop=face',
          name: '学习达人',
          content: '老师讲课非常有感染力，把枯燥的理论知识讲得生动有趣。答题方法真的很实用，强烈推荐！',
          time: '3天前',
        },
        {
          avatar: 'https://images.unsplash.com/photo-1599566159882-aa1b6c5f0c3a?w=60&h=60&fit=crop&crop=face',
          name: '考研上岸君',
          content: '跟着老师学了一个月，成绩提升明显！押题命中率真的很高，强烈推荐！',
          time: '1周前',
        },
        {
          avatar: 'https://images.unsplash.com/photo-1607746755531-e42f2c35a319?w=60&h=60&fit=crop&crop=face',
          name: '勤奋小张',
          content: '老师耐心负责，每次课后都会答疑，知识点梳理得很清晰，配套资料也很全面。',
          time: '2周前',
        },
      ],
      qualifications: [],
      teachingTags: [],
    }
  },

  computed: {
    avatarText() {
      const name = this.teacher.name || ''
      return name.charAt(0) || '师'
    },
    ratingText() {
      const r = this.teacher.rating
      if (r === undefined || r === null) return '0.0'
      return Number(r).toFixed(1)
    },
    heroSub() {
      const t = this.teacher
      const parts = []
      if (t.specialty) parts.push(t.specialty)
      if (t.teaching_years) parts.push(`${t.teaching_years}年教龄`)
      if (t.education) parts.push(t.education)
      return parts.length ? parts.join(' · ') : t.title || '讲师'
    },
  },

  onLoad(options) {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0

    if (options.teacher_id) {
      this.teacherId = Number(options.teacher_id)
      this.isFav = isTeacherFollowed(this.teacherId)
      this.loadData()
    }
  },

  methods: {
    async loadData() {
      this.loading = true
      try {
        const data = await getTeacherDetail(this.teacherId)
        this.teacher = data || {}
        this.courses = data.courses || []
        this.qualifications = this.buildQualifications(data.qualifications)
        this.teachingTags = this.buildTeachingTags(data.teaching_tags)
        this.isFav = isTeacherFollowed(this.teacherId)
      } catch {
        uni.showToast({ title: '加载失败', icon: 'none' })
      } finally {
        this.loading = false
      }
    },

    // 资质认证：接口返回 [{name, sub}]，循环分配图标与配色保持原型风格
    buildQualifications(list) {
      const icons = ['◆', '★', '✦']
      const colors = ['primary', 'orange', 'green']
      return (list || [])
        .filter((q) => q && q.name)
        .map((q, idx) => ({
          name: q.name,
          sub: q.sub || '',
          icon: icons[idx % icons.length],
          color: colors[idx % colors.length],
        }))
    },

    // 教学特色：接口返回标签字符串数组，循环分配配色
    buildTeachingTags(list) {
      const colors = ['primary', 'orange', 'green', 'purple', 'red']
      return (list || [])
        .filter((t) => t)
        .map((label, idx) => ({
          label,
          color: colors[idx % colors.length],
        }))
    },

    onBack() {
      uni.navigateBack()
    },

    async onToggleFav() {
      if (!this.teacherId) return

      if (this.isFav) {
        try {
          await unfollowTeacher(this.teacherId)
          this.isFav = false
          uni.showToast({ title: '已取消关注', icon: 'none' })
        } catch {
          uni.showToast({ title: '取消关注失败，请重试', icon: 'none' })
        }
      } else {
        try {
          await followTeacher({
            id: this.teacher.id || this.teacherId,
            name: this.teacher.name,
            avatar: this.teacher.avatar,
            title: this.teacher.title,
          })
          this.isFav = true
          uni.showToast({ title: '已关注教师', icon: 'none' })
        } catch {
          uni.showToast({ title: '关注失败，请重试', icon: 'none' })
        }
      }
    },

    onBackToCourses() {
      uni.switchTab({ url: '/pages/training/index' })
    },

    onCourseDetail(course) {
      if (!course || !course.id) return
      uni.navigateTo({
        url: `/pages/training/course-detail?course_id=${course.id}`,
      })
    },
  },
}
</script>

<style lang="scss">
/* ── Page scaffold ── */
.page {
  min-height: 100vh;
  background: $bg-color;
}

/* === 导航栏 === */
.nav-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 200;
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  padding: 0 16rpx;
}

.nav-btn {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10rpx);
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-chevron {
  width: 16rpx;
  height: 16rpx;
  border-left: 4rpx solid $white;
  border-bottom: 4rpx solid $white;
  transform: rotate(45deg);
  margin-left: 6rpx;
}

.nav-placeholder {
  flex: 1;
}

.nav-heart {
  font-size: 40rpx;
  color: $white;
  -webkit-text-stroke: 2rpx rgba(255, 255, 255, 0.5);
}

.nav-heart.active {
  color: $danger;
  -webkit-text-stroke-color: $danger;
}

/* === Hero 区 === */
.hero {
  position: relative;
  height: 480rpx;
  background: $gradient-primary;
}

.hero-image {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}

.hero-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.2) 0%, transparent 40%, rgba(245, 246, 250, 1) 100%);
}

.hero-info {
  position: absolute;
  /* 上移整个头像/认证讲师/头衔称号区块，避免被下方 stats-card（margin-top:-56rpx，z-index:10）
     遮挡住底部的头衔称号（hero-sub）。56rpx 与卡片上拉量对齐，内容底边恰好越过卡片顶边。 */
  bottom: 40rpx;
  left: 0;
  right: 0;
  padding: 28rpx;
}

.hero-bottom {
  display: flex;
  align-items: flex-end;
  gap: 20rpx;
}

.hero-avatar-wrap {
  position: relative;
  flex-shrink: 0;
}

.hero-avatar {
  width: 140rpx;
  height: 140rpx;
  border-radius: 50%;
  border: 6rpx solid $white;
  box-shadow: $shadow-card;
}

.hero-avatar-ph {
  width: 140rpx;
  height: 140rpx;
  border-radius: 50%;
  border: 6rpx solid $white;
  background: $primary;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-avatar-text {
  font-size: 48rpx;
  color: $white;
  font-weight: bold;
}

.hero-avatar-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: $success;
  border: 4rpx solid $white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-badge-icon {
  font-size: 18rpx;
  color: $white;
  font-weight: bold;
}

.hero-text {
  flex: 1;
  padding-bottom: 8rpx;
}

.hero-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.hero-name {
  font-size: 36rpx;
  font-weight: bold;
  color: $white;
}

.hero-tag {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(6rpx);
  padding: 4rpx 16rpx;
  border-radius: 999rpx;
}

.hero-tag-text {
  font-size: 22rpx;
  color: $white;
}

.hero-sub {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 6rpx;
}

/* === 统计行 === */
.stats-card {
  margin: -56rpx 28rpx 0;
  position: relative;
  z-index: 10;
  background: $surface;
  border-radius: 28rpx;
  padding: 28rpx;
  box-shadow: $shadow-card;
}

.stats-grid {
  display: flex;
}

.stats-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stats-border {
  border-left: 2rpx solid rgba(0, 0, 0, 0.05);
}

.stats-value {
  font-size: 36rpx;
  font-weight: bold;
  color: $text-primary;
}

.stats-primary {
  color: $primary;
}

.stats-orange {
  color: $orange;
}

.stats-green {
  color: $success;
}

.stats-label {
  font-size: 22rpx;
  color: $text-muted;
  margin-top: 6rpx;
}

/* === 通用 section === */
.section {
  margin: 28rpx 28rpx 0;
  background: $surface;
  border-radius: 28rpx;
  padding: 28rpx;
  box-shadow: $shadow-sm;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 20rpx;
}

.section-bar {
  width: 8rpx;
  height: 28rpx;
  background: $primary;
  border-radius: 4rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: bold;
  color: $text-primary;
}

.section-sub {
  font-size: 22rpx;
  color: $text-muted;
  margin-left: auto;
}

/* === 个人简介 === */
.bio-text {
  font-size: 26rpx;
  color: $text-secondary;
  line-height: 1.7;
}

/* === 资质认证 === */
.qual-list {
  display: flex;
  flex-direction: column;
}

.qual-item {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 8rpx 0;
}

.qual-divider {
  height: 2rpx;
  background: rgba(0, 0, 0, 0.03);
}

.qual-icon-wrap {
  width: 60rpx;
  height: 60rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.qual-bg-primary { background: $primary-soft; }
.qual-bg-orange { background: $orange-light; }
.qual-bg-green { background: $success-light; }

.qual-icon {
  font-size: 28rpx;
}

.qual-icon-primary { color: $primary; }
.qual-icon-orange { color: $orange; }
.qual-icon-green { color: $success; }

.qual-body {
  flex: 1;
}

.qual-name {
  font-size: 26rpx;
  color: $text-primary;
}

.qual-sub {
  font-size: 20rpx;
  color: $text-muted;
  margin-top: 2rpx;
}

.qual-check {
  font-size: 24rpx;
  color: $success;
}

/* === 教学特色 === */
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
}

.tag-pill {
  padding: 10rpx 22rpx;
  border-radius: 999rpx;
}

.tag-bg-primary { background: $primary-soft; }
.tag-bg-orange { background: $orange-light; }
.tag-bg-green { background: $success-light; }
.tag-bg-purple { background: rgba(108, 92, 231, 0.1); }
.tag-bg-red { background: $danger-light; }

.tag-text {
  font-size: 24rpx;
}

.tag-text-primary { color: $primary; }
.tag-text-orange { color: $orange; }
.tag-text-green { color: $success; }
.tag-text-purple { color: $purple; }
.tag-text-red { color: $danger; }

/* === 主讲课程 === */
.courses-section {
  margin-top: 28rpx;
}

.courses-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28rpx;
  margin-bottom: 14rpx;
}

.courses-title {
  font-size: 30rpx;
  font-weight: bold;
  color: $text-primary;
}

.courses-count {
  font-size: 22rpx;
  color: $text-muted;
}

.empty-state {
  padding: 40rpx 0;
  text-align: center;
}

.empty-text {
  font-size: 26rpx;
  color: $text-muted;
}

.course-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  padding: 0 28rpx;
}

.course-card {
  display: flex;
  background: $surface;
  border-radius: 28rpx;
  overflow: hidden;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.course-cover {
  width: 180rpx;
  height: 180rpx;
  flex-shrink: 0;
}

.course-body {
  flex: 1;
  padding: 18rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.course-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8rpx;
}

.course-name {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
  line-height: 1.3;
  flex: 1;
}

.course-lesson-info {
  font-size: 20rpx;
  color: $text-muted;
  margin-top: 6rpx;
}

.course-rating-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 8rpx;
}

.rating-stars {
  display: flex;
  align-items: center;
  gap: 4rpx;
}

.star-icon {
  font-size: 18rpx;
  color: #FFD700;
}

.rating-value {
  font-size: 24rpx;
  font-weight: 500;
  color: $text-primary;
}

.rating-count {
  font-size: 20rpx;
  color: $text-muted;
}

.course-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4rpx;
}

.course-price-wrap {
  display: flex;
  align-items: baseline;
}

.course-price {
  font-size: 28rpx;
  font-weight: bold;
  color: $primary;
}

.price-unit {
  font-size: 20rpx;
  font-weight: normal;
  color: $text-muted;
}

/* === 学员评价 === */
.review-item {
  padding-bottom: 20rpx;
}

.review-item + .review-item {
  margin-top: 0;
}

.review-divider {
  height: 2rpx;
  background: rgba(0, 0, 0, 0.03);
  margin-bottom: 20rpx;
}

.review-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 10rpx;
}

.review-avatar {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.review-meta {
  flex: 1;
}

.review-name {
  font-size: 26rpx;
  font-weight: 500;
  color: $text-primary;
}

.review-stars {
  display: flex;
  gap: 2rpx;
}

.review-star {
  font-size: 18rpx;
  color: #FFD700;
}

.review-time {
  font-size: 20rpx;
  color: $text-muted;
}

.review-content {
  font-size: 24rpx;
  color: $text-secondary;
  line-height: 1.6;
}

.review-more-btn {
  margin-top: 20rpx;
  padding: 16rpx 0;
  border: 2rpx solid $border-color;
  border-radius: 20rpx;
  text-align: center;
}

.review-more-text {
  font-size: 26rpx;
  color: $text-secondary;
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

.chat-btn {
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

.chat-icon {
  font-size: 36rpx;
  color: $text-secondary;
}

.action-btn {
  flex: 1;
  height: 92rpx;
  background: $gradient-primary;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow-float;
}

.action-btn:active {
  opacity: 0.9;
  transform: translateY(1rpx);
}

.action-btn-text {
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

.delay-1 { animation-delay: 0.08s; }
.delay-2 { animation-delay: 0.16s; }
.delay-3 { animation-delay: 0.24s; }
.delay-4 { animation-delay: 0.32s; }

.content {
  height: 100vh;
}
</style>
