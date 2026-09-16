<template>
  <view class="page">
    <view :style="{ height: statusBarHeight + 'px', background: '#fff' }" />
    <view class="nav-bar">
      <view class="nav-back" @tap="goBack">
        <view class="nav-back-arrow" />
      </view>
      <text class="nav-title">学历认证</text>
    </view>

    <scroll-view class="content" scroll-y>
      <view class="form-card">
        <view class="form-item">
          <text class="form-label">学校名称</text>
          <input
            v-model="formData.school"
            class="form-input"
            placeholder="请输入学校名称"
            maxlength="100"
          />
        </view>
        <view class="form-item">
          <text class="form-label">学历</text>
          <picker mode="selector" :range="educationLevels" range-key="label" @change="onEducationChange">
            <view class="picker-input">
              <text v-if="formData.education_level" class="picker-value">{{ formData.education_level }}</text>
              <text v-else class="picker-placeholder">请选择学历</text>
              <view class="icon icon-arrow-down picker-arrow" />
            </view>
          </picker>
        </view>
        <view class="form-item">
          <text class="form-label">专业（可选）</text>
          <input
            v-model="formData.major"
            class="form-input"
            placeholder="请输入专业名称"
            maxlength="100"
          />
        </view>
        <view class="form-item">
          <text class="form-label">毕业年份（可选）</text>
          <input
            v-model="graduationYearStr"
            class="form-input"
            placeholder="请输入毕业年份"
            type="number"
            maxlength="4"
            @input="onGraduationYearInput"
          />
        </view>
        <view class="form-item">
          <text class="form-label">学历证书照片</text>
          <view class="upload-area" @tap="chooseImage">
            <image v-if="formData.diploma_image_url" class="uploaded-image" :src="formData.diploma_image_url" mode="aspectFill" />
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
        <text class="tip-text">完成学历认证后，您可以发布家教信息。请确保信息真实有效。</text>
      </view>

      <button class="submit-btn" @tap="handleSubmit" :disabled="submitting">
        {{ submitting ? '提交中...' : '提交认证' }}
      </button>
    </scroll-view>
  </view>
</template>

<script>
import { getUserCertifications, submitEducationCertification } from '@/api/certification'
import { uploadImage } from '@/api/upload'

export default {
  data() {
    return {
      statusBarHeight: 0,
      educationLevels: [
        { label: '本科', value: '本科' },
        { label: '硕士', value: '硕士' },
        { label: '博士', value: '博士' },
      ],
      formData: {
        school: '',
        education_level: '',
        major: '',
        graduation_year: null,
        diploma_image_url: '',
      },
      graduationYearStr: '',
      submitting: false,
      uploading: false,
    }
  },
  onLoad() {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
    this.loadExistingData()
  },
  methods: {
    async loadExistingData() {
      try {
        const certs = await getUserCertifications()
        const eduCert = certs.find(c => c.verification_type === 'education')
        if (eduCert) {
          this.formData.school = eduCert.school || ''
          this.formData.education_level = eduCert.education_level || ''
          this.formData.major = eduCert.major || ''
          this.formData.graduation_year = eduCert.graduation_year || null
          this.formData.diploma_image_url = eduCert.diploma_image_url || ''
          if (eduCert.graduation_year) {
            this.graduationYearStr = String(eduCert.graduation_year)
          }
        }
      } catch (error) {
        console.error('加载认证数据失败:', error)
      }
    },
    onEducationChange(e) {
      const index = e.detail.value
      this.formData.education_level = this.educationLevels[index].value
    },
    onGraduationYearInput(e) {
      const value = e.detail.value
      this.graduationYearStr = value
      if (value && /^\d{4}$/.test(value)) {
        const year = parseInt(value)
        if (year >= 1950 && year <= 2030) {
          this.formData.graduation_year = year
        }
      } else {
        this.formData.graduation_year = null
      }
    },
    async chooseImage() {
      uni.chooseImage({
        count: 1,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: async (res) => {
          const filePath = res.tempFilePaths[0]
          this.uploading = true
          uni.showLoading({ title: '上传中...', mask: true })
          try {
            const result = await uploadImage(filePath, 'certification')
            this.formData.diploma_image_url = result.url
            uni.showToast({ title: '上传成功', icon: 'success' })
          } catch (error) {
            uni.showToast({
              title: error.message || '图片上传失败',
              icon: 'none',
            })
          } finally {
            this.uploading = false
            uni.hideLoading()
          }
        },
      })
    },
    async handleSubmit() {
      if (!this.formData.school.trim()) {
        uni.showToast({ title: '请输入学校名称', icon: 'none' })
        return
      }
      if (!this.formData.education_level) {
        uni.showToast({ title: '请选择学历', icon: 'none' })
        return
      }
      if (!this.formData.diploma_image_url) {
        uni.showToast({ title: '请上传学历证书照片', icon: 'none' })
        return
      }

      this.submitting = true
      try {
        await submitEducationCertification(this.formData)
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

.picker-input {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 88rpx;
  padding: 0 24rpx;
  background: #F5F6FA;
  border-radius: 16rpx;
  box-sizing: border-box;
}

.picker-value {
  font-size: 28rpx;
  color: #2D3436;
}

.picker-placeholder {
  font-size: 28rpx;
  color: #999;
}

.picker-arrow {
  font-size: 24rpx;
  color: #999;
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
  background: rgba(255, 149, 0, 0.05);
  border-radius: 16rpx;
  margin-bottom: 32rpx;
}

.tip-icon {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: rgba(255, 149, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tip-icon-inner {
  font-size: 20rpx;
  color: #FF9500;
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
  background: linear-gradient(135deg, #FF9500, #FFA726);
  color: #fff;
  box-shadow: 0 8rpx 24rpx rgba(255, 149, 0, 0.25);
  border: none;
}

.submit-btn::after {
  border: none;
}

.submit-btn[disabled] {
  opacity: 0.6;
}
</style>
