<template>
  <view class="page">
    <view class="nav-bar">
      <view class="nav-back press-effect" @tap="goBack">
        <text class="nav-back-text">‹</text>
      </view>
      <text class="nav-title">设置</text>
      <view class="nav-spacer" />
    </view>

    <scroll-view scroll-y class="content">
      <view class="profile-card">
        <view class="avatar-wrap" @tap="showUnsupported('头像上传暂未开放')">
          <image v-if="userStore.avatar" class="avatar-img" :src="userStore.avatar" mode="aspectFill" />
          <view v-else class="avatar-fallback">
            <text class="avatar-text">{{ avatarText }}</text>
          </view>
          <view class="avatar-camera">
            <text class="camera-text">相</text>
          </view>
        </view>
        <view class="profile-main">
          <view class="profile-name-row">
            <text class="profile-name">{{ displayNickname }}</text>
            <view class="vip-badge">
              <text class="vip-text">VIP</text>
            </view>
          </view>
          <text class="profile-id">ID: {{ displayUsername || '未设置' }}</text>
        </view>
        <view class="edit-icon" @tap="openUsernameEditor">
          <text class="edit-icon-text">✎</text>
        </view>
      </view>

      <view class="section-card">
        <view class="section-title-wrap">
          <text class="section-title">个人资料</text>
        </view>
        <view class="simple-row press-effect" @tap="showUnsupported('昵称修改暂未开放')">
          <text class="row-label">昵称</text>
          <view class="row-value-wrap">
            <text class="row-value">{{ displayNickname }}</text>
            <text class="chevron">›</text>
          </view>
        </view>
        <view class="simple-row press-effect" @tap="openUsernameEditor">
          <text class="row-label">用户名</text>
          <view class="row-value-wrap">
            <text class="row-value">{{ displayUsername || '去设置' }}</text>
            <text class="chevron">›</text>
          </view>
        </view>
        <view class="simple-row press-effect" @tap="openPhoneBinding">
          <text class="row-label">手机号</text>
          <view class="row-value-wrap">
            <text class="row-value" :class="{ muted: !hasBoundPhone }">{{ maskedPhone }}</text>
            <view v-if="!hasBoundPhone" class="status-pill warning"><text class="status-pill-text warning-text">未绑定</text></view>
            <text class="chevron">›</text>
          </view>
        </view>
        <view class="simple-row press-effect" @tap="showUnsupported('性别设置暂未开放')">
          <text class="row-label">性别</text>
          <view class="row-value-wrap">
            <text class="row-value muted">未设置</text>
            <text class="chevron">›</text>
          </view>
        </view>
        <view class="simple-row press-effect" @tap="showUnsupported('生日设置暂未开放')">
          <text class="row-label">生日</text>
          <view class="row-value-wrap">
            <text class="row-value muted">未设置</text>
            <text class="chevron">›</text>
          </view>
        </view>
        <view class="simple-row press-effect" @tap="showUnsupported('个性签名暂未开放')">
          <text class="row-label">个性签名</text>
          <view class="row-value-wrap value-limited">
            <text class="row-value muted">越努力越幸运</text>
            <text class="chevron">›</text>
          </view>
        </view>
      </view>

      <view class="section-card">
        <view class="section-title-wrap">
          <text class="section-title">账号与安全</text>
        </view>
        <view class="icon-row press-effect" @tap="showUnsupported('修改密码暂未开放')">
          <view class="row-icon orange"><text class="row-icon-text">锁</text></view>
          <text class="row-label">修改密码</text>
          <text class="chevron">›</text>
        </view>
        <view class="icon-row press-effect" @tap="showUnsupported('微信绑定暂未开放')">
          <view class="row-icon green"><text class="row-icon-text">微</text></view>
          <text class="row-label">微信绑定</text>
          <view class="status-pill success"><text class="status-pill-text success-text">已绑定</text></view>
          <text class="chevron">›</text>
        </view>
        <view class="icon-row press-effect" @tap="showUnsupported('实名认证暂未开放')">
          <view class="row-icon blue"><text class="row-icon-text">证</text></view>
          <text class="row-label">实名认证</text>
          <view class="status-pill primary"><text class="status-pill-text primary-text">已认证</text></view>
          <text class="chevron">›</text>
        </view>
        <view class="icon-row press-effect" @tap="showUnsupported('账号注销请联系门店客服')">
          <view class="row-icon red"><text class="row-icon-text">销</text></view>
          <text class="row-label danger-text">注销账号</text>
          <text class="chevron">›</text>
        </view>
      </view>

      <view class="section-card">
        <view class="section-title-wrap">
          <text class="section-title">通知设置</text>
        </view>
        <view
          v-for="item in notificationTypes"
          :key="item.key"
          class="setting-row"
        >
          <view class="row-icon" :class="item.colorClass"><text class="row-icon-text">{{ item.iconText }}</text></view>
          <view class="setting-copy">
            <text class="row-label">{{ item.settingLabel }}</text>
            <text class="row-desc">{{ item.settingDescription }}</text>
          </view>
          <view
            class="toggle"
            :class="{
              active: notifications[item.key],
              disabled: notificationPreferencesLoading || savingNotificationPreferenceKey === item.key,
            }"
            @tap="toggleNotify(item.key)"
          >
            <view class="toggle-dot" />
          </view>
        </view>
        <text v-if="notificationPreferencesLoading" class="preference-loading">通知设置同步中</text>
      </view>

      <view class="section-card">
        <view class="section-title-wrap">
          <text class="section-title">通用</text>
        </view>
        <view class="setting-row">
          <view class="row-icon indigo-soft"><text class="row-icon-text">月</text></view>
          <text class="row-label">深色模式</text>
          <view class="toggle" :class="{ active: darkMode }" @tap="darkMode = !darkMode">
            <view class="toggle-dot" />
          </view>
        </view>
        <view class="icon-row press-effect" @tap="showUnsupported('当前仅支持简体中文')">
          <view class="row-icon cyan-soft"><text class="row-icon-text">文</text></view>
          <text class="row-label">语言</text>
          <text class="row-value">简体中文</text>
          <text class="chevron">›</text>
        </view>
        <view class="icon-row press-effect" @tap="showUnsupported('默认门店设置暂未开放')">
          <view class="row-icon teal-soft"><text class="row-icon-text">店</text></view>
          <text class="row-label">默认门店</text>
          <text class="row-value">光谷自习室</text>
          <text class="chevron">›</text>
        </view>
        <view class="icon-row press-effect" @tap="clearCache">
          <view class="row-icon gray-soft"><text class="row-icon-text">扫</text></view>
          <text class="row-label">清除缓存</text>
          <text class="row-value">{{ cacheSize }}</text>
          <text class="chevron">›</text>
        </view>
      </view>

      <view class="section-card">
        <view class="section-title-wrap">
          <text class="section-title">关于</text>
        </view>
        <view class="icon-row">
          <view class="row-icon blue"><text class="row-icon-text">i</text></view>
          <text class="row-label">当前版本</text>
          <text class="row-value muted">v2.1.0</text>
        </view>
        <view class="icon-row press-effect" @tap="showUnsupported('用户协议暂未开放')">
          <view class="row-icon gray-soft"><text class="row-icon-text">协</text></view>
          <text class="row-label">用户协议</text>
          <text class="chevron">›</text>
        </view>
        <view class="icon-row press-effect" @tap="showUnsupported('隐私政策暂未开放')">
          <view class="row-icon gray-soft"><text class="row-icon-text">盾</text></view>
          <text class="row-label">隐私政策</text>
          <text class="chevron">›</text>
        </view>
        <view class="icon-row press-effect" @tap="showToast('已是最新版本')">
          <view class="row-icon green-soft"><text class="row-icon-text">更</text></view>
          <text class="row-label">检查更新</text>
          <view class="status-pill success"><text class="status-pill-text success-text">已是最新</text></view>
          <text class="chevron">›</text>
        </view>
      </view>

      <button class="logout-btn" @tap="showLogoutSheet = true">退出登录</button>
      <text class="copyright">去K书 v2.1.0 · © 2024 All Rights Reserved</text>
    </scroll-view>

    <view v-if="showUsernameSheet" class="sheet-mask" @tap="closeUsernameEditor">
      <view class="sheet" @tap.stop>
        <view class="sheet-handle" />
        <text class="sheet-title">修改用户名</text>
        <text class="sheet-desc">用户名修改后 24 小时内不可再次修改</text>
        <input
          v-model="usernameDraft"
          class="username-input"
          maxlength="32"
          placeholder="请输入用户名"
          placeholder-class="input-placeholder"
          confirm-type="done"
          @confirm="saveUsername"
        />
        <text class="input-hint">仅支持 6-32 位字母、数字或下划线</text>
        <text v-if="usernameError" class="input-error">{{ usernameError }}</text>
        <view class="sheet-actions">
          <button class="sheet-cancel" @tap="closeUsernameEditor">取消</button>
          <button class="sheet-confirm" :loading="savingUsername" :disabled="savingUsername" @tap="saveUsername">保存</button>
        </view>
      </view>
    </view>

    <view v-if="showLogoutSheet" class="sheet-mask" @tap="showLogoutSheet = false">
      <view class="sheet" @tap.stop>
        <view class="sheet-handle" />
        <text class="sheet-title">确认退出登录？</text>
        <text class="sheet-desc">退出后需要重新登录才能使用预约功能</text>
        <view class="sheet-actions">
          <button class="sheet-cancel" @tap="showLogoutSheet = false">取消</button>
          <button class="sheet-confirm danger" :loading="logoutLoading" :disabled="logoutLoading" @tap="confirmLogout">确认退出</button>
        </view>
      </view>
    </view>

    <view v-if="showPhoneBindSheet" class="sheet-mask" @tap="closePhoneBinding">
      <view class="sheet" @tap.stop>
        <view class="sheet-handle" />
        <text class="sheet-title">绑定手机号</text>
        <text class="sheet-desc">绑定后可用于账号找回、订单通知和余额安全校验</text>

        <button
          v-if="!hasBoundPhone"
          class="wechat-bind-btn"
          open-type="getPhoneNumber"
          :loading="bindingWechatPhone"
          :disabled="bindingWechatPhone || bindingBySms"
          @getphonenumber="handleWechatPhoneAuth"
        >
          微信手机号一键绑定
        </button>

        <view v-if="bindError" class="bind-error-box">
          <text class="bind-error-text">{{ bindError }}</text>
        </view>

        <view v-if="showSmsBinding" class="sms-bind-form">
          <view class="bind-input-row">
            <input
              v-model="bindPhoneForm.phone"
              class="bind-input"
              type="number"
              maxlength="11"
              placeholder="请输入手机号"
              placeholder-class="input-placeholder"
            />
          </view>
          <view class="bind-input-row code-input-row">
            <input
              v-model="bindPhoneForm.smsCode"
              class="bind-input"
              type="number"
              maxlength="6"
              placeholder="请输入验证码"
              placeholder-class="input-placeholder"
            />
            <button
              class="bind-code-btn"
              :disabled="bindCodeCountdown > 0 || sendingBindCode"
              :loading="sendingBindCode"
              @tap="sendBindSmsCode"
            >
              {{ bindCodeCountdown > 0 ? bindCodeCountdown + 's' : '获取验证码' }}
            </button>
          </view>
        </view>

        <view class="sheet-actions">
          <button class="sheet-cancel" @tap="showSmsBinding = true">短信绑定</button>
          <button
            class="sheet-confirm"
            :loading="bindingBySms"
            :disabled="!showSmsBinding || bindingWechatPhone || bindingBySms"
            @tap="submitSmsBinding"
          >
            确认绑定
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getNotificationPreferences, updateNotificationPreferences } from '@/api/notifications'
import { useUserStore } from '@/store/modules/user'
import { NOTIFICATION_TYPE_CONFIGS, getNotificationPreferenceField } from '@/utils/notificationTypes'

const USERNAME_PATTERN = /^[A-Za-z0-9_]{6,32}$/

export default {
  data() {
    return {
      userStore: useUserStore(),
      notificationTypes: NOTIFICATION_TYPE_CONFIGS,
      notifications: {
        booking: true,
        activity: true,
        report: true,
        arrival: true,
      },
      notificationPreferencesLoading: false,
      savingNotificationPreferenceKey: '',
      darkMode: false,
      cacheSize: '23.6 MB',
      showUsernameSheet: false,
      usernameDraft: '',
      usernameError: '',
      savingUsername: false,
      showLogoutSheet: false,
      logoutLoading: false,
      showPhoneBindSheet: false,
      showSmsBinding: false,
      bindingWechatPhone: false,
      bindingBySms: false,
      sendingBindCode: false,
      bindCodeCountdown: 0,
      bindCountdownTimer: null,
      bindError: '',
      bindPhoneForm: {
        phone: '',
        smsCode: '',
      },
    }
  },
  computed: {
    displayNickname() {
      return this.userStore.nickname || '学习达人'
    },
    displayUsername() {
      return this.userStore.username || ''
    },
    avatarText() {
      return (this.displayNickname || this.userStore.phone || 'U').charAt(0).toUpperCase()
    },
    maskedPhone() {
      const phone = this.userStore.phone || ''
      if (!phone || phone.length < 7) return phone || '未绑定'
      return `${phone.slice(0, 3)}****${phone.slice(-4)}`
    },
    hasBoundPhone() {
      return !!this.userStore.phone
    },
  },
  beforeUnmount() {
    this.clearBindCountdown()
  },
  onShow() {
    if (this.userStore.isLoggedIn) {
      this.userStore.fetchUserInfo().catch(() => {})
      this.loadNotificationPreferences()
    }
  },
  methods: {
    goBack() {
      const pages = getCurrentPages()
      if (pages.length > 1) {
        uni.navigateBack()
      } else {
        uni.switchTab({ url: '/pages/profile/index' })
      }
    },
    showToast(title) {
      uni.showToast({ title, icon: 'none' })
    },
    showUnsupported(title) {
      this.showToast(title)
    },
    async loadNotificationPreferences() {
      if (this.notificationPreferencesLoading) return
      this.notificationPreferencesLoading = true
      try {
        const preferences = await getNotificationPreferences()
        this.applyNotificationPreferences(preferences)
      } catch {
        this.showToast('通知设置加载失败')
      } finally {
        this.notificationPreferencesLoading = false
      }
    },
    applyNotificationPreferences(preferences = {}) {
      this.notificationTypes.forEach((item) => {
        const field = getNotificationPreferenceField(item.key)
        if (typeof preferences[field] === 'boolean') {
          this.notifications[item.key] = preferences[field]
        }
      })
    },
    buildNotificationPreferencePayload() {
      return this.notificationTypes.reduce((payload, item) => {
        payload[getNotificationPreferenceField(item.key)] = !!this.notifications[item.key]
        return payload
      }, {})
    },
    async toggleNotify(key) {
      if (this.notificationPreferencesLoading || this.savingNotificationPreferenceKey) return
      const previousValue = this.notifications[key]
      this.notifications[key] = !previousValue
      this.savingNotificationPreferenceKey = key
      try {
        const savedPreferences = await updateNotificationPreferences(this.buildNotificationPreferencePayload())
        this.applyNotificationPreferences(savedPreferences)
      } catch {
        this.notifications[key] = previousValue
        this.showToast('通知设置保存失败')
      } finally {
        this.savingNotificationPreferenceKey = ''
      }
    },
    clearCache() {
      this.cacheSize = '0 MB'
      this.showToast('缓存已清除')
    },
    openPhoneBinding() {
      if (this.hasBoundPhone) {
        this.showToast('手机号暂不支持在应用内修改')
        return
      }
      this.bindError = ''
      this.showSmsBinding = false
      this.resetBindForm()
      this.showPhoneBindSheet = true
    },
    closePhoneBinding() {
      if (this.bindingWechatPhone || this.bindingBySms) return
      this.showPhoneBindSheet = false
      this.bindError = ''
      this.showSmsBinding = false
      this.resetBindForm()
    },
    async handleWechatPhoneAuth(event) {
      if (this.bindingWechatPhone || this.bindingBySms) return
      const detail = event?.detail || {}
      if (!detail.code) {
        this.bindError = this.mapPhoneBindError(detail, 'wechat')
        this.showSmsBinding = true
        return
      }

      this.bindingWechatPhone = true
      this.bindError = ''
      try {
        await this.userStore.bindWechatPhone(detail.code)
        this.onPhoneBindSuccess()
      } catch (error) {
        this.bindError = this.mapPhoneBindError(error, 'wechat')
        this.showSmsBinding = true
      } finally {
        this.bindingWechatPhone = false
      }
    },
    async sendBindSmsCode() {
      if (this.sendingBindCode || this.bindCodeCountdown > 0) return
      const phoneError = this.validateBindPhone()
      if (phoneError) {
        this.bindError = phoneError
        return
      }

      this.sendingBindCode = true
      this.bindError = ''
      try {
        await this.userStore.sendCode(this.bindPhoneForm.phone, '')
        this.showToast('验证码已发送')
        this.startBindCountdown()
      } catch (error) {
        this.bindError = this.mapPhoneBindError(error, 'sms')
      } finally {
        this.sendingBindCode = false
      }
    },
    async submitSmsBinding() {
      if (this.bindingBySms) return
      const phoneError = this.validateBindPhone()
      if (phoneError) {
        this.bindError = phoneError
        return
      }
      if (!/^\d{6}$/.test(this.bindPhoneForm.smsCode)) {
        this.bindError = '请输入 6 位短信验证码'
        return
      }

      this.bindingBySms = true
      this.bindError = ''
      try {
        await this.userStore.bindPhoneBySms(this.bindPhoneForm.phone, this.bindPhoneForm.smsCode)
        this.onPhoneBindSuccess()
      } catch (error) {
        this.bindError = this.mapPhoneBindError(error, 'sms')
      } finally {
        this.bindingBySms = false
      }
    },
    onPhoneBindSuccess() {
      this.showPhoneBindSheet = false
      this.showSmsBinding = false
      this.bindError = ''
      this.resetBindForm()
      this.showToast('手机号绑定成功')
    },
    resetBindForm() {
      this.bindPhoneForm.phone = ''
      this.bindPhoneForm.smsCode = ''
      this.bindCodeCountdown = 0
      this.clearBindCountdown()
    },
    validateBindPhone() {
      const phone = this.bindPhoneForm.phone
      if (!phone) return '请输入手机号'
      if (!/^1[3-9]\d{9}$/.test(phone)) return '手机号格式不正确'
      return ''
    },
    startBindCountdown() {
      this.clearBindCountdown()
      this.bindCodeCountdown = 60
      this.bindCountdownTimer = setInterval(() => {
        this.bindCodeCountdown -= 1
        if (this.bindCodeCountdown <= 0) {
          this.clearBindCountdown()
        }
      }, 1000)
    },
    clearBindCountdown() {
      if (this.bindCountdownTimer) {
        clearInterval(this.bindCountdownTimer)
        this.bindCountdownTimer = null
      }
      if (this.bindCodeCountdown < 0) {
        this.bindCodeCountdown = 0
      }
    },
    mapPhoneBindError(error, mode) {
      const detail = typeof error?.detail === 'string' ? error.detail : ''
      const message = error?.errMsg || error?.message || ''
      const text = detail || message

      if (text.includes('getPhoneNumber:fail') || text.includes('deny') || text.includes('cancel') || text.includes('拒绝')) {
        return '未获得微信手机号授权，可使用短信验证码绑定'
      }
      if (text.includes('过期') || text.includes('expired') || text.includes('invalid code') || text.includes('code')) {
        return mode === 'sms' ? '验证码无效或已过期，请重新获取' : '手机号授权已过期，请重试'
      }
      if (text.includes('验证码') || text.includes('sms')) {
        return '验证码无效或已过期，请重新获取'
      }
      if (text.includes('不同') || text.includes('其他微信') || text.includes('wechat_openid')) {
        return '该手机号已绑定其他微信，无法覆盖绑定'
      }
      if (text.includes('资产') || text.includes('余额') || text.includes('订单') || text.includes('优惠券') || text.includes('不能自动合并')) {
        return '当前账号已有资产，暂不能自动合并，请联系门店客服'
      }
      if (text.includes('已存在') || text.includes('已注册') || text.includes('冲突') || text.includes('409')) {
        return '该手机号已存在账号，暂不能直接绑定'
      }
      if (text.includes('登录已过期') || text.includes('401') || text.includes('Unauthorized')) {
        return '登录已过期，请重新登录后绑定'
      }
      return text || '手机号绑定失败，请稍后重试'
    },
    openUsernameEditor() {
      this.usernameDraft = this.displayUsername
      this.usernameError = ''
      this.showUsernameSheet = true
    },
    closeUsernameEditor() {
      if (this.savingUsername) return
      this.showUsernameSheet = false
      this.usernameError = ''
    },
    async saveUsername() {
      const username = this.usernameDraft.trim()
      this.usernameDraft = username
      if (!USERNAME_PATTERN.test(username)) {
        this.usernameError = '用户名仅支持 6-32 位字母、数字或下划线'
        return
      }
      if (username === this.displayUsername) {
        this.showUsernameSheet = false
        return
      }

      this.savingUsername = true
      this.usernameError = ''
      try {
        await this.userStore.updateProfile({ username })
        this.showUsernameSheet = false
        this.showToast('用户名已更新')
      } catch (error) {
        this.usernameError = this.mapUsernameError(error)
      } finally {
        this.savingUsername = false
      }
    },
    mapUsernameError(error) {
      const detail = typeof error?.detail === 'string' ? error.detail : ''
      if (error?.retry_after_seconds !== undefined) {
        return `用户名修改冷却中，请在 ${this.formatCooldown(error.retry_after_seconds)} 后再试`
      }
      if (detail.includes('已存在')) return '该用户名已存在'
      if (detail.includes('6-32') || detail.includes('下划线')) return '用户名仅支持 6-32 位字母、数字或下划线'
      return detail || '用户名保存失败，请稍后再试'
    },
    formatCooldown(secondsValue) {
      const totalMinutes = Math.max(1, Math.ceil(Number(secondsValue || 0) / 60))
      const hours = Math.floor(totalMinutes / 60)
      const minutes = totalMinutes % 60
      if (hours > 0 && minutes > 0) return `${hours} 小时 ${minutes} 分钟`
      if (hours > 0) return `${hours} 小时`
      return `${minutes} 分钟`
    },
    async confirmLogout() {
      this.logoutLoading = true
      try {
        await this.userStore.logout()
        this.showLogoutSheet = false
        uni.reLaunch({ url: '/pages/login/login' })
      } finally {
        this.logoutLoading = false
      }
    },
  },
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
  color: $text-primary;
}

.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 20;
  height: 96rpx;
  padding: 28rpx 28rpx 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: $white;
  border-bottom: 1rpx solid rgba(229, 231, 235, 0.9);
}

.nav-back,
.nav-spacer {
  width: 64rpx;
  height: 64rpx;
}

.nav-back {
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-back-text {
  font-size: 52rpx;
  line-height: 52rpx;
  color: $text-primary;
}

.nav-title {
  font-size: 30rpx;
  font-weight: 700;
  color: $text-primary;
}

.content {
  height: 100vh;
  box-sizing: border-box;
  padding: 120rpx 0 40rpx;
}

.profile-card,
.section-card {
  margin: 24rpx 32rpx 0;
  background: $white;
  border-radius: 32rpx;
  box-shadow: $shadow-sm;
}

.profile-card {
  display: flex;
  align-items: center;
  padding: 32rpx;
  gap: 24rpx;
}

.avatar-wrap {
  position: relative;
  width: 120rpx;
  height: 120rpx;
  flex-shrink: 0;
}

.avatar-img,
.avatar-fallback {
  width: 120rpx;
  height: 120rpx;
  border-radius: 60rpx;
}

.avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, $primary, $purple);
}

.avatar-text {
  color: $white;
  font-size: 42rpx;
  font-weight: 800;
}

.avatar-camera {
  position: absolute;
  right: -2rpx;
  bottom: -2rpx;
  width: 40rpx;
  height: 40rpx;
  border-radius: 20rpx;
  background: rgba(45, 52, 54, 0.78);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4rpx solid $white;
}

.camera-text {
  font-size: 18rpx;
  color: $white;
}

.profile-main {
  flex: 1;
  min-width: 0;
}

.profile-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.profile-name {
  max-width: 280rpx;
  font-size: 32rpx;
  font-weight: 800;
  color: $text-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.vip-badge {
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  background: #facc15;
}

.vip-text {
  font-size: 20rpx;
  font-weight: 700;
  color: #854d0e;
}

.profile-id {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: $text-muted;
}

.edit-icon {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-icon-text {
  color: $primary;
  font-size: 30rpx;
}

.section-card {
  overflow: hidden;
}

.section-title-wrap {
  padding: 24rpx 32rpx 6rpx;
}

.section-title {
  color: #9ca3af;
  font-size: 24rpx;
  font-weight: 700;
}

.simple-row,
.icon-row,
.setting-row {
  min-height: 104rpx;
  padding: 0 32rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.row-label {
  flex: 1;
  min-width: 0;
  font-size: 28rpx;
  color: $text-primary;
}

.row-value-wrap {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
}

.row-value {
  font-size: 26rpx;
  color: $text-secondary;
  max-width: 260rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.value-limited {
  max-width: 340rpx;
}

.muted {
  color: $text-muted;
}

.chevron {
  flex-shrink: 0;
  color: #d1d5db;
  font-size: 38rpx;
  line-height: 38rpx;
}

.row-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.row-icon-text {
  font-size: 24rpx;
  font-weight: 700;
}

.orange { background: #fff7ed; color: #f97316; }
.green { background: rgba(7, 193, 96, 0.1); color: $success; }
.blue { background: rgba(79, 110, 247, 0.1); color: $primary; }
.red { background: #fef2f2; color: #f87171; }
.blue-soft { background: #eff6ff; color: #3b82f6; }
.purple-soft { background: #f5f3ff; color: #8b5cf6; }
.green-soft { background: #f0fdf4; color: #22c55e; }
.yellow-soft { background: #fefce8; color: #eab308; }
.indigo-soft { background: #eef2ff; color: #6366f1; }
.cyan-soft { background: #ecfeff; color: #06b6d4; }
.teal-soft { background: #f0fdfa; color: #14b8a6; }
.gray-soft { background: #f3f4f6; color: #6b7280; }
.danger-text { color: #f87171; }

.status-pill {
  padding: 4rpx 16rpx;
  border-radius: 999rpx;
}

.status-pill.success {
  background: #f0fdf4;
}

.status-pill.primary {
  background: $primary-light;
}

.status-pill.warning {
  background: #fef3c7;
}

.status-pill-text {
  font-size: 22rpx;
}

.success-text { color: #22c55e; }
.primary-text { color: $primary; }
.warning-text { color: #d97706; }

.setting-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.setting-copy .row-label {
  flex: none;
}

.row-desc {
  color: $text-muted;
  font-size: 20rpx;
}

.toggle {
  width: 88rpx;
  height: 52rpx;
  padding: 4rpx;
  border-radius: 26rpx;
  background: #d1d5db;
  transition: background 0.2s ease;
  box-sizing: border-box;
}

.toggle.disabled {
  opacity: 0.58;
}

.toggle-dot {
  width: 44rpx;
  height: 44rpx;
  border-radius: 22rpx;
  background: $white;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.16);
  transition: transform 0.2s ease;
}

.toggle.active {
  background: $primary;
}

.toggle.active .toggle-dot {
  transform: translateX(36rpx);
}

.preference-loading {
  display: block;
  padding: 0 32rpx 24rpx 116rpx;
  color: $text-muted;
  font-size: 22rpx;
}

.logout-btn {
  margin: 48rpx 32rpx 24rpx;
  height: 96rpx;
  line-height: 96rpx;
  border-radius: 28rpx;
  color: #f87171;
  background: $white;
  font-size: 28rpx;
  font-weight: 700;
  box-shadow: 0 8rpx 28rpx rgba(225, 112, 85, 0.16);
  border: none;

  &::after {
    border: none;
  }
}

.copyright {
  display: block;
  text-align: center;
  font-size: 20rpx;
  color: $text-muted;
  padding-bottom: 40rpx;
}

.sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: rgba(0, 0, 0, 0.42);
}

.sheet {
  width: 100%;
  padding: 20rpx 40rpx 56rpx;
  border-radius: 40rpx 40rpx 0 0;
  background: $white;
  box-sizing: border-box;
}

.sheet-handle {
  width: 80rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: #e5e7eb;
  margin: 0 auto 32rpx;
}

.sheet-title {
  display: block;
  text-align: center;
  font-size: 34rpx;
  line-height: 44rpx;
  font-weight: 800;
  color: $text-primary;
}

.sheet-desc {
  display: block;
  margin-top: 12rpx;
  text-align: center;
  font-size: 26rpx;
  color: $text-secondary;
}

.username-input {
  height: 96rpx;
  margin-top: 36rpx;
  padding: 0 28rpx;
  border-radius: 20rpx;
  background: #f7f8fb;
  color: $text-primary;
  font-size: 30rpx;
  box-sizing: border-box;
}

.input-placeholder,
.input-hint {
  color: $text-muted;
}

.input-hint {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
}

.input-error {
  display: block;
  margin-top: 16rpx;
  font-size: 24rpx;
  color: $danger;
}

.wechat-bind-btn {
  height: 92rpx;
  line-height: 92rpx;
  margin-top: 36rpx;
  border-radius: 24rpx;
  background: #07c160;
  color: $white;
  font-size: 28rpx;
  font-weight: 800;
  border: none;

  &::after {
    border: none;
  }
}

.bind-error-box {
  margin-top: 24rpx;
  padding: 20rpx 24rpx;
  border-radius: 18rpx;
  background: #fef2f2;
}

.bind-error-text {
  font-size: 24rpx;
  line-height: 34rpx;
  color: $danger;
}

.sms-bind-form {
  margin-top: 28rpx;
}

.bind-input-row {
  display: flex;
  align-items: center;
  min-height: 92rpx;
  margin-top: 20rpx;
  padding: 0 24rpx;
  border-radius: 20rpx;
  background: #f7f8fb;
  box-sizing: border-box;
}

.code-input-row {
  gap: 18rpx;
}

.bind-input {
  flex: 1;
  min-width: 0;
  height: 92rpx;
  color: $text-primary;
  font-size: 28rpx;
}

.bind-code-btn {
  width: 188rpx;
  height: 68rpx;
  line-height: 68rpx;
  margin: 0;
  padding: 0;
  border-radius: 18rpx;
  background: $primary-light;
  color: $primary;
  font-size: 24rpx;
  font-weight: 700;
  border: none;

  &::after {
    border: none;
  }
}

.sheet-actions {
  display: flex;
  gap: 24rpx;
  margin-top: 40rpx;
}

.sheet-cancel,
.sheet-confirm {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 22rpx;
  font-size: 28rpx;
  font-weight: 700;
  border: none;

  &::after {
    border: none;
  }
}

.sheet-cancel {
  background: #f3f4f6;
  color: $text-secondary;
}

.sheet-confirm {
  background: $primary;
  color: $white;
}

.sheet-confirm.danger {
  background: #f87171;
}

.press-effect:active {
  transform: scale(0.98);
}
</style>
