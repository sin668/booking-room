<template>
  <view class="page">
    <!-- 状态栏占位 -->
    <view :style="{ height: statusBarHeight + 'px', background: '#fff' }" />

    <!-- 导航栏 -->
    <view class="nav-bar">
      <view class="nav-back" @tap="goBack">
        <view class="nav-back-arrow" />
      </view>
      <text class="nav-title">发布教培信息</text>
      <text class="nav-submit" :class="{ 'nav-submit-off': submitting }" @tap="onSubmit">发布</text>
    </view>

    <scroll-view class="content" scroll-y>
      <!-- 类型选择 -->
      <view class="section">
        <text class="section-label">选择发布类型</text>
        <view class="type-row">
          <view
            v-for="opt in typeOptions"
            :key="opt.key"
            :class="['type-card', { 'type-card-on': form.listing_type === opt.key }]"
            @tap="selectType(opt.key)"
          >
            <view class="icon type-icon" :class="opt.icon" />
            <text class="type-name">{{ opt.label }}</text>
            <text class="type-req">{{ opt.req }}</text>
          </view>
        </view>
      </view>

      <!-- 表单 -->
      <view class="form-card">
        <view class="field">
          <text class="field-label">标题<text class="field-star">*</text></text>
          <input
            v-model="form.title"
            class="field-input"
            type="text"
            :placeholder="titlePlaceholder"
            placeholder-class="field-ph"
            maxlength="100"
            confirm-type="done"
            @confirm="onSubmit"
          />
        </view>

        <view class="field">
          <text class="field-label">科目分类</text>
          <view class="chip-row">
            <text
              v-for="sub in SUBJECTS"
              :key="sub"
              :class="['chip', { 'chip-on': form.subject === sub }]"
              @tap="form.subject = form.subject === sub ? '' : sub"
            >{{ sub }}</text>
          </view>
        </view>

        <view class="field">
          <text class="field-label">授课方式</text>
          <view class="chip-row">
            <text
              v-for="mode in MODES"
              :key="mode"
              :class="['chip', { 'chip-on': form.teaching_mode === mode }]"
              @tap="form.teaching_mode = form.teaching_mode === mode ? '' : mode"
            >{{ mode }}</text>
          </view>
        </view>

        <view class="field">
          <text class="field-label">价格</text>
          <view class="price-row">
            <input
              v-model="form.price"
              class="field-input price-input"
              type="digit"
              placeholder="面议可不填"
              placeholder-class="field-ph"
              confirm-type="done"
            />
            <view class="chip-row price-units">
              <text
                v-for="unit in UNITS"
                :key="unit"
                :class="['chip chip-sm', { 'chip-on': form.price_unit === unit }]"
                @tap="form.price_unit = form.price_unit === unit ? '' : unit"
              >{{ unit }}</text>
            </view>
          </view>
        </view>

        <view class="field">
          <text class="field-label">服务区域</text>
          <input
            v-model="form.area"
            class="field-input"
            type="text"
            placeholder="例如：广州市天河区 / 线上不限"
            placeholder-class="field-ph"
            maxlength="100"
            confirm-type="done"
          />
        </view>

        <view class="field">
          <text class="field-label">详细描述</text>
          <textarea
            v-model="form.description"
            class="field-textarea"
            placeholder="介绍教学经验、教学特色、目标学员等，真实详细的描述更容易被联系"
            placeholder-class="field-ph"
            maxlength="2000"
            confirm-type="done"
            auto-height
          />
        </view>

        <view class="field">
          <text class="field-label">可授课时间</text>
          <view class="chip-row">
            <text
              v-for="t in TIME_SLOTS"
              :key="t"
              :class="['chip', { 'chip-on': form.available_times.indexOf(t) !== -1 }]"
              @tap="toggleTime(t)"
            >{{ t }}</text>
          </view>
        </view>

        <view class="field field-last">
          <text class="field-label">相关图片（最多 3 张）</text>
          <view class="image-row">
            <view v-for="(img, index) in form.images" :key="img" class="image-item">
              <image class="image-thumb" :src="img" mode="aspectFill" @tap="previewImage(img)" />
              <view class="image-remove" @tap.stop="removeImage(index)">
                <text class="image-remove-text">×</text>
              </view>
            </view>
            <view v-if="uploading" class="image-item image-add image-add-busy">
              <text class="image-add-text">上传中</text>
            </view>
            <view v-else-if="form.images.length < MAX_IMAGES" class="image-add" @tap="chooseImages">
              <text class="image-add-icon">＋</text>
              <text class="image-add-text">{{ form.images.length }}/3</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 认证提醒 -->
      <view v-if="missingCert" class="cert-notice" @tap="goCertify">
        <view class="icon icon-shield cert-notice-icon" />
        <view class="cert-notice-body">
          <text class="cert-notice-title">认证提醒</text>
          <text class="cert-notice-text">发布{{ activeTypeLabel }}需先完成{{ missingCert.label }}</text>
        </view>
        <text class="cert-notice-link">去认证 ›</text>
      </view>
      <view v-else class="plain-notice">
        <view class="icon icon-shield plain-notice-icon" />
        <text class="plain-notice-text">信息将经过审核后展示，请勿包含广告、联系方式或不实内容</text>
      </view>

      <view class="bottom-space" />
    </scroll-view>
  </view>
</template>

<script>
import { createEduListing } from '@/api/eduMarket'
import { getUserCertifications } from '@/api/certification'
import { uploadImage } from '@/api/upload'
import { ensureLogin } from '@/utils/auth'
import { formatErrorDetail } from '@/utils/formatters'

const MAX_IMAGES = 3
const SUBJECTS = ['英语', '数学', '物理', '化学', '语文', '编程', '钢琴', '美术', '其他']
const MODES = ['一对一', '小班', '大班', '线上', '上门', '线下面授']
const UNITS = ['元/小时', '元/次', '元/期', '元/月']
const TIME_SLOTS = ['工作日白天', '工作日晚', '周末上午', '周末下午', '周末全天', '时间可议']

// 类型 → 所需认证（与后端 REQUIRED_CERTIFICATION 对齐）
const TYPE_OPTIONS = [
  { key: 'tutor', label: '家教(教人)', req: '需学历认证', icon: 'icon-graduation-cap', cert: 'education', certLabel: '学历认证', certRoute: '/pages/certification/education' },
  { key: 'training', label: '培训班', req: '需教师资格', icon: 'icon-chalkboard-user', cert: 'teacher', certLabel: '教师资格认证', certRoute: '/pages/certification/teacher' },
  { key: 'demand', label: '求教(被教)', req: '需实名认证', icon: 'icon-user', cert: 'real_name', certLabel: '实名认证', certRoute: '/pages/certification/real-name' },
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
      statusBarHeight: 0,
      MAX_IMAGES,
      SUBJECTS,
      MODES,
      UNITS,
      TIME_SLOTS,
      typeOptions: TYPE_OPTIONS,
      certifications: [],
      uploading: false,
      submitting: false,
      form: {
        listing_type: 'tutor',
        title: '',
        subject: '',
        teaching_mode: '',
        price: '',
        price_unit: '元/小时',
        area: '',
        description: '',
        images: [],
        available_times: [],
      },
    }
  },

  computed: {
    activeTypeOption() {
      return TYPE_OPTIONS.find((o) => o.key === this.form.listing_type) || TYPE_OPTIONS[0]
    },
    activeTypeLabel() {
      return this.activeTypeOption.label
    },
    titlePlaceholder() {
      return this.form.listing_type === 'demand'
        ? '例如：求推荐靠谱的高中化学家教'
        : '例如：英语专业八级 | 一对一口语辅导'
    },
    isCertApproved() {
      const cert = this.certifications.find((c) => c.verification_type === this.activeTypeOption.cert)
      return Boolean(cert) && ['approved', 'verified'].includes(cert.status)
    },
    // 当前类型缺少认证时返回 {label, route}，否则 null
    missingCert() {
      if (this.isCertApproved) return null
      return { label: this.activeTypeOption.certLabel, route: this.activeTypeOption.certRoute }
    },
  },

  onLoad() {
    if (!ensureLogin()) return
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
    try {
      const stored = uni.getStorageSync('current_city')
      if (stored?.name) this.form.area = stored.name
    } catch {
      // 忽略城市预填失败
    }
    this.loadCertifications()
  },

  methods: {
    async loadCertifications() {
      try {
        const data = await getUserCertifications()
        this.certifications = data || []
      } catch {
        this.certifications = []
      }
    },

    selectType(key) {
      this.form.listing_type = key
    },

    toggleTime(t) {
      const idx = this.form.available_times.indexOf(t)
      if (idx === -1) {
        this.form.available_times.push(t)
      } else {
        this.form.available_times.splice(idx, 1)
      }
    },

    goCertify() {
      if (!this.missingCert) return
      uni.navigateTo({ url: this.missingCert.route })
    },

    async chooseImages() {
      const remain = MAX_IMAGES - this.form.images.length
      if (remain <= 0) return
      let paths = []
      try {
        paths = await chooseImagePaths(remain)
      } catch {
        return
      }
      if (!paths.length) return
      this.uploading = true
      for (const path of paths) {
        try {
          const result = await uploadImage(path, 'common')
          this.form.images.push(result.url)
        } catch (error) {
          uni.showToast({ title: formatErrorDetail(error, '图片上传失败'), icon: 'none' })
        }
      }
      this.uploading = false
    },

    removeImage(index) {
      this.form.images.splice(index, 1)
    },

    previewImage(current) {
      uni.previewImage({ current, urls: this.form.images })
    },

    goBack() {
      uni.navigateBack()
    },

    async onSubmit() {
      if (this.submitting) return
      const title = this.form.title.trim()
      if (!title) {
        uni.showToast({ title: '请填写标题', icon: 'none' })
        return
      }
      if (!this.isCertApproved) {
        uni.showModal({
          title: '需要认证',
          content: `发布${this.activeTypeLabel}需先完成${this.activeTypeOption.certLabel}`,
          confirmText: '去认证',
          success: (res) => {
            if (res.confirm) this.goCertify()
          },
        })
        return
      }

      const priceText = String(this.form.price).trim()
      let price = null
      if (priceText) {
        const num = Number(priceText)
        if (!Number.isFinite(num) || num < 0) {
          uni.showToast({ title: '价格格式不正确', icon: 'none' })
          return
        }
        price = num
      }

      const payload = {
        listing_type: this.form.listing_type,
        title,
        subject: this.form.subject || null,
        teaching_mode: this.form.teaching_mode || null,
        price,
        price_unit: price ? (this.form.price_unit || null) : null,
        area: this.form.area.trim() || null,
        description: this.form.description.trim() || null,
        images: this.form.images,
        available_times: this.form.available_times,
      }

      this.submitting = true
      try {
        await createEduListing(payload)
        uni.showToast({ title: '提交成功，审核通过后展示', icon: 'none' })
        setTimeout(() => uni.navigateBack(), 1200)
      } catch (error) {
        uni.showToast({ title: formatErrorDetail(error, '发布失败'), icon: 'none' })
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

/* ── 导航栏 ── */
.nav-bar {
  display: flex;
  align-items: center;
  height: 88rpx;
  padding: 0 28rpx;
  background: $surface;
  position: relative;
  flex-shrink: 0;
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
  border-left: 4rpx solid $text-primary;
  border-bottom: 4rpx solid $text-primary;
  transform: rotate(45deg);
}

.nav-title {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  font-size: 32rpx;
  font-weight: 600;
  color: $text-primary;
}

.nav-submit {
  margin-left: auto;
  font-size: 28rpx;
  font-weight: 600;
  color: $primary;
}

.nav-submit-off {
  color: $text-muted;
}

.content {
  flex: 1;
  height: 0;
}

/* ── 类型选择 ── */
.section {
  padding: 24rpx 24rpx 0;
}

.section-label {
  display: block;
  font-size: 24rpx;
  color: $text-muted;
  margin-bottom: 16rpx;
}

.type-row {
  display: flex;
  gap: 18rpx;
}

.type-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 24rpx 12rpx;
  background: $surface;
  border: 2rpx solid $border-color;
  border-radius: $radius-lg;
}

.type-card-on {
  background: $primary-soft;
  border-color: $primary;
}

.type-icon {
  font-size: 40rpx;
  color: $text-muted;
}

.type-card-on .type-icon {
  color: $primary;
}

.type-name {
  font-size: 24rpx;
  font-weight: 500;
  color: $text-secondary;
}

.type-card-on .type-name {
  color: $primary;
}

.type-req {
  font-size: 18rpx;
  color: $text-muted;
}

/* ── 表单 ── */
.form-card {
  margin: 24rpx;
  padding: 8rpx 28rpx;
  background: $surface;
  border-radius: $radius-xl;
  box-shadow: $shadow-card;
}

.field {
  padding: 24rpx 0;
  border-bottom: 1rpx solid $border-soft;
}

.field-last {
  border-bottom: none;
}

.field-label {
  display: block;
  font-size: 24rpx;
  color: $text-muted;
  margin-bottom: 16rpx;
}

.field-star {
  color: $danger;
  margin-left: 4rpx;
}

.field-input {
  width: 100%;
  box-sizing: border-box;
  padding: 18rpx 22rpx;
  background: $surface-soft;
  border: 1rpx solid $border-soft;
  border-radius: $radius-md;
  font-size: 27rpx;
  color: $text-primary;
}

.field-ph {
  color: #C8C9CB;
}

.field-textarea {
  width: 100%;
  box-sizing: border-box;
  height: 180rpx;
  padding: 18rpx 22rpx;
  background: $surface-soft;
  border: 1rpx solid $border-soft;
  border-radius: $radius-md;
  font-size: 27rpx;
  line-height: 1.6;
  color: $text-primary;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
}

.chip {
  padding: 12rpx 26rpx;
  background: $bg-color;
  border: 2rpx solid transparent;
  border-radius: 999rpx;
  font-size: 24rpx;
  color: $text-secondary;
}

.chip-sm {
  padding: 8rpx 18rpx;
  font-size: 22rpx;
}

.chip-on {
  background: $primary-light;
  border-color: rgba(79, 110, 247, 0.35);
  color: $primary;
  font-weight: 500;
}

.price-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.price-input {
  width: 220rpx;
  flex-shrink: 0;
}

.price-units {
  flex: 1;
  min-width: 0;
}

/* ── 图片 ── */
.image-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.image-item {
  position: relative;
  width: 160rpx;
  height: 160rpx;
}

.image-thumb {
  width: 160rpx;
  height: 160rpx;
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
  width: 160rpx;
  height: 160rpx;
  box-sizing: border-box;
  background: $surface-soft;
  border: 2rpx dashed rgba(79, 110, 247, 0.28);
  border-radius: $radius-md;
}

.image-add-busy {
  border-style: solid;
  border-color: $border-color;
}

.image-add-icon {
  font-size: 40rpx;
  line-height: 1;
  color: $primary;
}

.image-add-text {
  font-size: 20rpx;
  color: $text-muted;
}

/* ── 提醒 ── */
.cert-notice {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin: 0 24rpx;
  padding: 24rpx;
  background: $orange-light;
  border-radius: $radius-lg;
}

.cert-notice-icon {
  font-size: 30rpx;
  color: $orange;
  flex-shrink: 0;
}

.cert-notice-body {
  flex: 1;
  min-width: 0;
}

.cert-notice-title {
  display: block;
  font-size: 24rpx;
  font-weight: 600;
  color: #B36A00;
}

.cert-notice-text {
  display: block;
  margin-top: 4rpx;
  font-size: 21rpx;
  color: #CC7A00;
}

.cert-notice-link {
  font-size: 24rpx;
  font-weight: 500;
  color: $primary;
  flex-shrink: 0;
}

.plain-notice {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  margin: 0 24rpx;
  padding: 24rpx;
  background: $surface;
  border-radius: $radius-lg;
}

.plain-notice-icon {
  margin-top: 2rpx;
  font-size: 24rpx;
  color: $primary;
  flex-shrink: 0;
}

.plain-notice-text {
  flex: 1;
  font-size: 21rpx;
  line-height: 1.6;
  color: $text-muted;
}

.bottom-space {
  height: 60rpx;
}
</style>
