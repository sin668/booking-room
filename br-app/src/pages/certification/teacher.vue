<template>
  <view class="page">
    <view :style="{ height: statusBarHeight + 'px', background: '#fff' }" />
    <view class="nav-bar">
      <view class="nav-back" @tap="goBack">
        <view class="nav-back-arrow" />
      </view>
      <text class="nav-title">教师资格认证</text>
    </view>

    <scroll-view class="content" scroll-y>
      <view class="form-card">
        <view class="form-item">
          <text class="form-label">教师资格证号</text>
          <input
            v-model="formData.teacher_certificate_number"
            class="form-input"
            placeholder="请输入教师资格证号"
            maxlength="50"
          />
        </view>
        <view class="form-item">
          <text class="form-label">任教科目（可选）</text>
          <input
            v-model="formData.teaching_subject"
            class="form-input"
            placeholder="请输入任教科目"
            maxlength="50"
          />
        </view>
        <view class="form-item">
          <text class="form-label">教师资格证书照片（可选）</text>
          <view class="upload-area" @tap="chooseImage">
            <image v-if="formData.certificate_image_url" class="uploaded-image" :src="formData.certificate_image_url" mode="aspectFill" />
            <view v-else class="upload-placeholder">
              <view class="icon icon-camera upload-icon" />
              <text class="upload-text">点击上传</text>
            </view>
          </view>
        </view>
      </view>

      <view class="tip-card">
        <view class="tip-icon">
          <view class="icon icon-info tip-icon-inner" />
        </view>
        <text class="tip-text">完成教师资格认证后，您可以发布培训班和家教信息。请确保信息真实有效。</text>
      </view>

      <button class="submit-btn" @tap="handleSubmit" :disabled="submitting">
        {{ submitting ? '提交中...' : '提交认证' }}
      </button>
    </scroll-view>
  </view>
</template>

<script>
import { submitTeacherCertification } from '@/api/certification'

export default {
  data() {
    return {
      statusBarHeight: 0,
      formData: {
        teacher_certificate_number: '',
        teaching_subject: '',
        certificate_image_url: '',
      },
      submitting: false,
    }
  },
  onLoad() {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
  },
  methods: {
    chooseImage() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => {
          // TODO: Upload to server and get URL
          this.formData.certificate_image_url = res.tempFilePaths[0]
          uni.showToast({ title: '图片已选择（需实现上传）', icon: 'none' })
        },
      })
    },
    async handleSubmit() {
      if (!this.formData.teacher_certificate_number.trim()) {
        uni.showToast({ title: '请输入教师资格证号', icon: 'none' })
        return
      }
      if (this.formData.teacher_certificate_number.length < 10) {
        uni.showToast({ title: '教师资格证号格式不正确', icon: 'none' })
        return
      }

      this.submitting = true
      try {
        await submitTeacherCertification(this.formData)
        uni.showToast({ title: '提交成功，等待审核', icon: 'success' })
        setTimeout(() => {
          uni.navigateBack()
        }, 1500)
      } catch (error) {
        uni.showToast({
          title: error.detail || error.message || '提交失败',
          icon: 'none',
        })
      } finally {
        this.submitting = false
      }
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
  padding: 32rpx;
  box-sizing: border-box;
}

.form-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 24rpx;
}

.form-item {
  margin-bottom: 32rpx;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-label {
  font-size: 28rpx;
  color: #2D3436;
  display: block;
  margin-bottom: 16rpx;
  font-weight: 500;
}

.form-input {
  width: 100%;
  height: 88rpx;
  padding: 0 24rpx;
  background: #F5F6FA;
  border-radius: 16rpx;
  font-size: 28rpx;
  color: #2D3436;
  box-sizing: border-box;
}

.upload-area {
  width: 100%;
  height: 240rpx;
  border-radius: 16rpx;
  overflow: hidden;
}

.uploaded-image {
  width: 100%;
  height: 100%;
}

.upload-placeholder {
  width: 100%;
  height: 100%;
  background: #F5F6FA;
  border: 2rpx dashed #DDD;
  border-radius: 16rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}

.upload-icon {
  font-size: 48rpx;
  color: #999;
}

.upload-text {
  font-size: 24rpx;
  color: #999;
}

.tip-card {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  padding: 24rpx;
  background: rgba(79, 110, 247, 0.05);
  border-radius: 16rpx;
  margin-bottom: 32rpx;
}

.tip-icon {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: rgba(79, 110, 247, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tip-icon-inner {
  font-size: 20rpx;
  color: #4F6EF7;
}

.tip-text {
  flex: 1;
  font-size: 24rpx;
  color: #666;
  line-height: 1.6;
}

.submit-btn {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  text-align: center;
  border-radius: 48rpx;
  font-size: 32rpx;
  font-weight: 600;
  background: linear-gradient(135deg, #4F6EF7, #6C5CE7);
  color: #fff;
  box-shadow: 0 8rpx 24rpx rgba(79, 110, 247, 0.25);
  border: none;
}

.submit-btn::after {
  border: none;
}

.submit-btn[disabled] {
  opacity: 0.6;
}
</style>
