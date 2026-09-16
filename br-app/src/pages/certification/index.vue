<template>
  <view class="page">
    <!-- Status bar spacer -->
    <view :style="{ height: statusBarHeight + 'px', background: '#fff' }" />

    <!-- Nav bar -->
    <view class="nav-bar">
      <view class="nav-back" @tap="goBack">
        <view class="nav-back-arrow" />
      </view>
      <text class="nav-title">认证管理</text>
    </view>

    <scroll-view class="content" scroll-y>
      <!-- Certification status header -->
      <view class="status-header">
        <view class="status-icon">
          <view class="icon icon-shield-check status-icon-inner" />
        </view>
        <view class="status-info">
          <text class="status-title">已认证 {{ verifiedCount }} 项</text>
          <text class="status-desc">完成更多认证，解锁更多发布权限</text>
        </view>
      </view>

      <!-- Real name certification -->
      <view class="cert-card" @tap="onTapRealName">
        <view class="cert-header">
          <view class="cert-title-row">
            <view class="cert-icon real-name-icon">
              <view class="icon icon-id-card cert-icon-inner" />
            </view>
            <view class="cert-info">
              <text class="cert-name">实名认证</text>
              <text class="cert-requirement">所有用户必须完成</text>
            </view>
          </view>
          <view :class="['cert-badge', `badge-${certStatus(realNameCert)}`]">
            <text class="cert-badge-text">{{ getCertStatusText(realNameCert) }}</text>
          </view>
        </view>
        <view v-if="isApproved(realNameCert)" class="cert-detail">
          <view class="detail-row">
            <text class="detail-label">姓名</text>
            <text class="detail-value">{{ realNameCert.real_name }}</text>
          </view>
        </view>
        <view v-if="realNameCert?.status === 'rejected'" class="cert-rejection">
          <text class="rejection-text">拒绝原因：{{ realNameCert.rejection_reason }}</text>
        </view>
      </view>

      <!-- Education certification -->
      <view class="cert-card" @tap="onTapEducation">
        <view class="cert-header">
          <view class="cert-title-row">
            <view class="cert-icon education-icon">
              <view class="icon icon-graduation-cap cert-icon-inner" />
            </view>
            <view class="cert-info">
              <text class="cert-name">学历认证</text>
              <text class="cert-requirement">认证后可发布家教信息（教人）</text>
            </view>
          </view>
          <view :class="['cert-badge', `badge-${certStatus(educationCert)}`]">
            <text class="cert-badge-text">{{ getCertStatusText(educationCert) }}</text>
          </view>
        </view>
        <view v-if="isApproved(educationCert)" class="cert-detail">
          <view class="detail-row">
            <text class="detail-label">学校</text>
            <text class="detail-value">{{ educationCert.school }}</text>
          </view>
          <view class="detail-row">
            <text class="detail-label">学历</text>
            <text class="detail-value">{{ educationCert.education_level }}</text>
          </view>
        </view>
        <view v-if="educationCert?.status === 'rejected'" class="cert-rejection">
          <text class="rejection-text">拒绝原因：{{ educationCert.rejection_reason }}</text>
        </view>
      </view>

      <!-- Teacher certification -->
      <view class="cert-card" @tap="onTapTeacher">
        <view class="cert-header">
          <view class="cert-title-row">
            <view class="cert-icon teacher-icon">
              <view class="icon icon-chalkboard-user cert-icon-inner" />
            </view>
            <view class="cert-info">
              <text class="cert-name">教师资格认证</text>
              <text class="cert-requirement">认证后可发布培训班和家教信息</text>
            </view>
          </view>
          <view :class="['cert-badge', `badge-${certStatus(teacherCert)}`]">
            <text class="cert-badge-text">{{ getCertStatusText(teacherCert) }}</text>
          </view>
        </view>
        <view v-if="isApproved(teacherCert)" class="cert-detail">
          <view class="detail-row">
            <text class="detail-label">证书号</text>
            <text class="detail-value">{{ maskCertificateNumber(teacherCert.teacher_certificate_number) }}</text>
          </view>
          <view class="detail-row">
            <text class="detail-label">科目</text>
            <text class="detail-value">{{ teacherCert.teaching_subject || '未填写' }}</text>
          </view>
        </view>
        <view v-if="teacherCert?.status === 'rejected'" class="cert-rejection">
          <text class="rejection-text">拒绝原因：{{ teacherCert.rejection_reason }}</text>
        </view>
      </view>

      <!-- Permission matrix -->
      <view class="permission-section">
        <text class="permission-title">发布权限说明</text>
        <view class="permission-list">
          <view class="permission-item">
            <view class="permission-icon green">
              <view class="icon icon-check permission-icon-inner" />
            </view>
            <text class="permission-text">实名认证</text>
            <text class="permission-desc">发布需求</text>
          </view>
          <view class="permission-item">
            <view class="permission-icon orange">
              <view class="icon icon-graduation-cap permission-icon-inner" />
            </view>
            <text class="permission-text">+ 学历认证</text>
            <text class="permission-desc highlight">发布家教(教)</text>
          </view>
          <view class="permission-item">
            <view class="permission-icon purple">
              <view class="icon icon-chalkboard-user permission-icon-inner" />
            </view>
            <text class="permission-text">+ 教师资格</text>
            <text class="permission-desc highlight">发布培训班+家教</text>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { getUserCertifications } from '@/api/certification'
import { isLoggedIn, ensureLogin } from '@/utils/auth'

export default {
  data() {
    return {
      statusBarHeight: 0,
      certifications: [],
    }
  },
  computed: {
    realNameCert() {
      return this.certifications.find(c => c.verification_type === 'real_name')
    },
    educationCert() {
      return this.certifications.find(c => c.verification_type === 'education')
    },
    teacherCert() {
      return this.certifications.find(c => c.verification_type === 'teacher')
    },
    verifiedCount() {
      return this.certifications.filter(c => this.isApproved(c)).length
    },
  },
  onShow() {
    if (!ensureLogin()) return
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
    this.loadCertifications()
  },
  methods: {
    async loadCertifications() {
      try {
        const data = await getUserCertifications()
        this.certifications = data || []
      } catch (error) {
        console.error('Failed to load certifications:', error)
        this.certifications = []
      }
    },
    certStatus(cert) {
      if (!cert) return 'none'
      // 账号安全服务（设置页实名认证）写入 verified，与认证模块的 approved 语义等价
      if (cert.status === 'verified') return 'approved'
      return cert.status
    },
    isApproved(cert) {
      return Boolean(cert) && ['approved', 'verified'].includes(cert.status)
    },
    getCertStatusText(cert) {
      if (!cert) return '去认证'
      const statusMap = {
        pending: '审核中',
        approved: '已认证',
        verified: '已认证',
        rejected: '已拒绝',
      }
      return statusMap[cert.status] || '去认证'
    },
    maskCertificateNumber(number) {
      if (!number) return ''
      if (number.length <= 8) return number
      return `${number.substring(0, 4)}****${number.substring(number.length - 4)}`
    },
    onTapRealName() {
      if (this.isApproved(this.realNameCert)) {
        uni.showToast({ title: '已完成实名认证', icon: 'none' })
        return
      }
      uni.navigateTo({ url: '/pages/certification/real-name' })
    },
    onTapEducation() {
      // Check if real name is approved
      if (!this.isApproved(this.realNameCert)) {
        uni.showModal({
          title: '提示',
          content: '请先完成实名认证',
          showCancel: false,
        })
        return
      }

      if (this.isApproved(this.educationCert)) {
        uni.showToast({ title: '已完成学历认证', icon: 'none' })
        return
      }
      uni.navigateTo({ url: '/pages/certification/education' })
    },
    onTapTeacher() {
      // Check if real name is approved
      if (!this.isApproved(this.realNameCert)) {
        uni.showModal({
          title: '提示',
          content: '请先完成实名认证',
          showCancel: false,
        })
        return
      }

      // Check if education is approved
      if (!this.isApproved(this.educationCert)) {
        uni.showModal({
          title: '提示',
          content: '请先完成学历认证，或同时提交学历认证和教师资格认证',
          confirmText: '去认证',
          success: (res) => {
            if (res.confirm) {
              uni.navigateTo({ url: '/pages/certification/education' })
            }
          },
        })
        return
      }

      if (this.isApproved(this.teacherCert)) {
        uni.showToast({ title: '已完成教师资格认证', icon: 'none' })
        return
      }
      uni.navigateTo({ url: '/pages/certification/teacher' })
    },
    goBack() {
      uni.navigateBack()
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: #F5F6FA;
}

.nav-bar {
  display: flex;
  align-items: center;
  height: 88rpx;
  padding: 0 28rpx;
  background: #fff;
  position: relative;
}

.nav-back {
  width: 72rpx;
  height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-back-arrow {
  width: 20rpx;
  height: 20rpx;
  border-left: 4rpx solid #2D3436;
  border-bottom: 4rpx solid #2D3436;
  transform: rotate(45deg);
}

.nav-title {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  font-size: 32rpx;
  font-weight: 600;
  color: #2D3436;
}

.content {
  height: calc(100vh - var(--status-bar-height, 44px) - 88rpx);
  padding: 20rpx 32rpx 40rpx;
  box-sizing: border-box;
}

.status-header {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 32rpx;
  background: linear-gradient(135deg, #4F6EF7, #6C5CE7);
  border-radius: 24rpx;
  margin-bottom: 24rpx;
}

.status-icon {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.status-icon-inner {
  font-size: 48rpx;
  color: #fff;
}

.status-info {
  flex: 1;
}

.status-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #fff;
  display: block;
}

.status-desc {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
  display: block;
  margin-top: 8rpx;
}

.cert-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.cert-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.cert-title-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.cert-icon {
  width: 80rpx;
  height: 80rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.real-name-icon {
  background: rgba(7, 193, 96, 0.1);
}

.education-icon {
  background: rgba(255, 149, 0, 0.1);
}

.teacher-icon {
  background: rgba(79, 110, 247, 0.1);
}

.cert-icon-inner {
  font-size: 40rpx;
}

.real-name-icon .cert-icon-inner {
  color: #07C160;
}

.education-icon .cert-icon-inner {
  color: #FF9500;
}

.teacher-icon .cert-icon-inner {
  color: #4F6EF7;
}

.cert-info {
  flex: 1;
  min-width: 0;
}

.cert-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #2D3436;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cert-requirement {
  font-size: 22rpx;
  color: #999;
  display: block;
  margin-top: 4rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cert-badge {
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  flex-shrink: 0;
}

.badge-none {
  background: #4F6EF7;
}

.badge-none .cert-badge-text {
  color: #fff;
}

.badge-pending {
  background: rgba(255, 149, 0, 0.1);
}

.badge-pending .cert-badge-text {
  color: #FF9500;
}

.badge-approved {
  background: rgba(7, 193, 96, 0.1);
}

.badge-approved .cert-badge-text {
  color: #07C160;
}

.badge-rejected {
  background: rgba(255, 107, 107, 0.1);
}

.badge-rejected .cert-badge-text {
  color: #FF6B6B;
}

.cert-badge-text {
  font-size: 24rpx;
  font-weight: 500;
  white-space: nowrap;
}

.cert-detail {
  margin-top: 24rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid #F0F0F0;
}

.detail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.detail-label {
  font-size: 24rpx;
  color: #999;
}

.detail-value {
  font-size: 24rpx;
  color: #2D3436;
}

.cert-rejection {
  margin-top: 24rpx;
  padding: 16rpx 20rpx;
  background: rgba(255, 107, 107, 0.05);
  border-radius: 12rpx;
}

.rejection-text {
  font-size: 24rpx;
  color: #FF6B6B;
}

.permission-section {
  margin-top: 32rpx;
}

.permission-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #2D3436;
  display: block;
  margin-bottom: 20rpx;
}

.permission-list {
  background: #fff;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.permission-item {
  display: flex;
  align-items: center;
  padding: 24rpx 28rpx;
  border-bottom: 1rpx solid #F5F5F5;
}

.permission-item:last-child {
  border-bottom: none;
}

.permission-icon {
  width: 48rpx;
  height: 48rpx;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.permission-icon.green {
  background: rgba(7, 193, 96, 0.1);
}

.permission-icon.orange {
  background: rgba(255, 149, 0, 0.1);
}

.permission-icon.purple {
  background: rgba(79, 110, 247, 0.1);
}

.permission-icon-inner {
  font-size: 24rpx;
}

.permission-icon.green .permission-icon-inner {
  color: #07C160;
}

.permission-icon.orange .permission-icon-inner {
  color: #FF9500;
}

.permission-icon.purple .permission-icon-inner {
  color: #4F6EF7;
}

.permission-text {
  font-size: 26rpx;
  color: #2D3436;
  flex: 1;
}

.permission-desc {
  font-size: 22rpx;
  color: #999;
}

.permission-desc.highlight {
  color: #4F6EF7;
  font-weight: 500;
}
</style>
