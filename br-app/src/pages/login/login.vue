<template>
  <view class="page">
    <!-- 装饰背景 -->
    <view class="deco deco-1"></view>
    <view class="deco deco-2"></view>

    <view class="content">
      <!-- Logo & 品牌 -->
      <view class="brand">
        <view class="logo">
          <text class="logo-icon">📖</text>
        </view>
        <text class="brand-title">去K书</text>
        <text class="brand-desc">专注学习，遇见更好的自己</text>
      </view>

      <!-- 登录/注册 Tab -->
      <view class="tab-bar">
        <view class="tab-indicator" :class="{ 'tab-right': currentTab === 'register' }"></view>
        <view
          class="tab-item"
          :class="{ active: currentTab === 'login' }"
          @tap="switchTab('login')"
        >
          <text class="tab-text">登录</text>
        </view>
        <view
          class="tab-item"
          :class="{ active: currentTab === 'register' }"
          @tap="switchTab('register')"
        >
          <text class="tab-text">注册</text>
        </view>
      </view>

      <!-- ===== 登录表单 ===== -->
      <view v-if="currentTab === 'login'" class="form">
        <!-- 手机号 -->
        <view class="field">
          <text class="field-label">手机号</text>
          <view class="input-wrap">
            <view class="area-code">
              <text class="area-code-text">+86</text>
              <text class="area-code-arrow">▼</text>
            </view>
            <view class="input-divider"></view>
            <input
              v-model="loginForm.phone"
              type="number"
              maxlength="11"
              placeholder="请输入手机号"
              placeholder-class="placeholder"
              class="input"
            />
          </view>
        </view>

        <!-- 密码 -->
        <view class="field">
          <text class="field-label">密码</text>
          <view class="input-wrap">
            <text class="input-icon">🔒</text>
            <input
              v-model="loginForm.password"
              :password="!showLoginPwd"
              maxlength="20"
              placeholder="请输入密码"
              placeholder-class="placeholder"
              class="input"
            />
            <text class="pwd-toggle" @tap="showLoginPwd = !showLoginPwd">
              {{ showLoginPwd ? '🙈' : '👁' }}
            </text>
          </view>
        </view>

        <!-- 登录按钮 -->
        <button
          class="btn-primary"
          :loading="loginLoading"
          :disabled="loginLoading"
          @tap="handleLogin"
        >
          登录
        </button>

        <!-- 分割线 -->
        <view class="divider">
          <view class="divider-line"></view>
          <text class="divider-text">其他方式登录</text>
          <view class="divider-line"></view>
        </view>

        <!-- 第三方登录 -->
        <view class="social-login">
          <view class="social-item" @tap="onSocialLogin('wechat')">
            <view class="social-icon social-wechat">
              <text class="social-icon-text">微</text>
            </view>
            <text class="social-label">微信</text>
          </view>
          <view class="social-item" @tap="onSocialLogin('apple')">
            <view class="social-icon social-apple">
              <text class="social-icon-text">A</text>
            </view>
            <text class="social-label">Apple</text>
          </view>
          <view class="social-item" @tap="onSocialLogin('qq')">
            <view class="social-icon social-qq">
              <text class="social-icon-text">Q</text>
            </view>
            <text class="social-label">QQ</text>
          </view>
        </view>

        <!-- 协议 -->
        <view class="agreement">
          <view class="checkbox-wrap" @tap="loginAgreed = !loginAgreed">
            <view class="checkbox" :class="{ checked: loginAgreed }">
              <text v-if="loginAgreed" class="check-mark">✓</text>
            </view>
          </view>
          <text class="agreement-text">
            登录即表示同意
          </text>
          <text class="agreement-link" @tap="openAgreement('service')">《用户服务协议》</text>
          <text class="agreement-text">和</text>
          <text class="agreement-link" @tap="openAgreement('privacy')">《隐私政策》</text>
        </view>
      </view>

      <!-- ===== 注册表单 ===== -->
      <view v-else class="form">
        <!-- 昵称 -->
        <view class="field">
          <text class="field-label">昵称</text>
          <view class="input-wrap">
            <text class="input-icon">👤</text>
            <input
              v-model="regForm.nickname"
              type="text"
              maxlength="20"
              placeholder="请输入昵称"
              placeholder-class="placeholder"
              class="input"
            />
            <text class="input-hint">2-20字</text>
          </view>
        </view>

        <!-- 手机号 -->
        <view class="field">
          <text class="field-label">手机号</text>
          <view class="input-wrap">
            <view class="area-code">
              <text class="area-code-text">+86</text>
              <text class="area-code-arrow">▼</text>
            </view>
            <view class="input-divider"></view>
            <input
              v-model="regForm.phone"
              type="number"
              maxlength="11"
              placeholder="请输入手机号"
              placeholder-class="placeholder"
              class="input"
            />
          </view>
        </view>

        <!-- 验证码 -->
        <view class="field">
          <text class="field-label">验证码</text>
          <view class="input-wrap code-wrap">
            <text class="input-icon">🛡</text>
            <input
              v-model="regForm.smsCode"
              type="number"
              maxlength="6"
              placeholder="请输入验证码"
              placeholder-class="placeholder"
              class="input"
            />
            <view
              class="code-btn"
              :class="{ disabled: codeCountdown > 0 }"
              @tap="handleSendCode"
            >
              <text class="code-btn-text">
                {{ codeCountdown > 0 ? codeCountdown + 's 后重发' : '获取验证码' }}
              </text>
            </view>
          </view>
        </view>

        <!-- 密码 -->
        <view class="field">
          <text class="field-label">设置密码</text>
          <view class="input-wrap">
            <text class="input-icon">🔒</text>
            <input
              v-model="regForm.password"
              :password="!showRegPwd"
              maxlength="20"
              placeholder="请设置6-20位密码"
              placeholder-class="placeholder"
              class="input"
              @input="onPasswordInput"
            />
            <text class="pwd-toggle" @tap="showRegPwd = !showRegPwd">
              {{ showRegPwd ? '🙈' : '👁' }}
            </text>
          </view>
          <!-- 密码强度 -->
          <view v-if="regForm.password" class="pwd-strength">
            <view class="strength-bars">
              <view class="strength-bar" :class="{ active: pwdStrength >= 1, weak: pwdStrength === 1, medium: pwdStrength === 2, strong: pwdStrength >= 3 }"></view>
              <view class="strength-bar" :class="{ active: pwdStrength >= 2, medium: pwdStrength === 2, strong: pwdStrength >= 3 }"></view>
              <view class="strength-bar" :class="{ active: pwdStrength >= 3, strong: pwdStrength >= 3 }"></view>
            </view>
            <text class="strength-text">{{ pwdStrengthText }}</text>
          </view>
        </view>

        <!-- 确认密码 -->
        <view class="field">
          <text class="field-label">确认密码</text>
          <view class="input-wrap">
            <text class="input-icon">🔒</text>
            <input
              v-model="regForm.confirmPassword"
              :password="!showRegPwdConfirm"
              maxlength="20"
              placeholder="请再次输入密码"
              placeholder-class="placeholder"
              class="input"
            />
            <text class="pwd-toggle" @tap="showRegPwdConfirm = !showRegPwdConfirm">
              {{ showRegPwdConfirm ? '🙈' : '👁' }}
            </text>
          </view>
        </view>

        <!-- 邀请码 -->
        <view class="field">
          <text class="field-label">
            邀请码 <text class="field-label-muted">（选填）</text>
          </text>
          <view class="input-wrap">
            <text class="input-icon">🎁</text>
            <input
              v-model="regForm.inviteCode"
              type="text"
              maxlength="10"
              placeholder="输入邀请码可获额外优惠"
              placeholder-class="placeholder"
              class="input"
            />
          </view>
        </view>

        <!-- 注册按钮 -->
        <button
          class="btn-primary"
          :loading="regLoading"
          :disabled="regLoading"
          @tap="handleRegister"
        >
          注册
        </button>

        <!-- 协议 -->
        <view class="agreement">
          <view class="checkbox-wrap" @tap="regAgreed = !regAgreed">
            <view class="checkbox" :class="{ checked: regAgreed }">
              <text v-if="regAgreed" class="check-mark">✓</text>
            </view>
          </view>
          <text class="agreement-text">
            注册即表示同意
          </text>
          <text class="agreement-link" @tap="openAgreement('service')">《用户服务协议》</text>
          <text class="agreement-text">和</text>
          <text class="agreement-link" @tap="openAgreement('privacy')">《隐私政策》</text>
        </view>
      </view>

      <!-- 底部安全提示 -->
      <view class="footer-tip">
        <text class="footer-tip-text">🛡 您的信息已加密传输，请放心使用</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, computed, onUnmounted } from 'vue'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()

// ===== Tab 切换 =====
const currentTab = ref('login')

function switchTab(tab) {
  currentTab.value = tab
}

// ===== 登录表单 =====
const loginForm = reactive({
  phone: '',
  password: '',
})
const showLoginPwd = ref(false)
const loginLoading = ref(false)
const loginAgreed = ref(true)

// ===== 注册表单 =====
const regForm = reactive({
  nickname: '',
  phone: '',
  smsCode: '',
  password: '',
  confirmPassword: '',
  inviteCode: '',
  captchaToken: '', // 图形验证码 token（TODO: 接入阿里云验证码 2.0）
})
const showRegPwd = ref(false)
const showRegPwdConfirm = ref(false)
const regLoading = ref(false)
const regAgreed = ref(true)
const codeCountdown = ref(0)
const sendCodeLoading = ref(false)
let countdownTimer = null

// 页面卸载时清理定时器
onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
})

// ===== 密码强度 =====
const pwdStrength = computed(() => {
  const pwd = regForm.password
  if (!pwd) return 0
  let score = 0
  if (pwd.length >= 6) score++
  if (/[a-zA-Z]/.test(pwd) && /\d/.test(pwd)) score++
  if (/[^a-zA-Z0-9]/.test(pwd) || pwd.length >= 12) score++
  return score
})

const pwdStrengthText = computed(() => {
  const map = { 0: '', 1: '弱', 2: '中', 3: '强' }
  return map[pwdStrength.value]
})

function onPasswordInput() {
  // 密码变化时同步清空确认密码
  if (regForm.confirmPassword && regForm.password !== regForm.confirmPassword) {
    regForm.confirmPassword = ''
  }
}

// ===== 校验工具 =====
const PHONE_REG = /^1[3-9]\d{9}$/

function validatePhone(phone) {
  if (!phone) return '请输入手机号'
  if (!PHONE_REG.test(phone)) return '手机号格式不正确'
  return ''
}

function validatePassword(pwd) {
  if (!pwd) return '请输入密码'
  if (pwd.length < 6) return '密码长度不能少于6位'
  if (pwd.length > 20) return '密码长度不能超过20位'
  return ''
}

function showToast(msg, icon = 'none') {
  uni.showToast({ title: msg, icon, duration: 2000 })
}

// ===== 发送验证码 =====
function handleSendCode() {
  if (codeCountdown.value > 0 || sendCodeLoading.value) return

  const err = validatePhone(regForm.phone)
  if (err) {
    showToast(err)
    return
  }

  // TODO: 接入阿里云验证码 2.0 后，先获取 captchaToken
  // 目前直接发送（后端开发阶段用 mock）
  sendCodeLoading.value = true
  userStore
    .sendCode(regForm.phone, regForm.captchaToken)
    .then(() => {
      showToast('验证码已发送', 'success')
      startCountdown()
    })
    .catch((e) => {
      showToast(e.detail || '发送失败，请稍后重试')
    })
    .finally(() => {
      sendCodeLoading.value = false
    })
}

function startCountdown() {
  codeCountdown.value = 60
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    codeCountdown.value--
    if (codeCountdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

// ===== 登录 =====
function handleLogin() {
  const phoneErr = validatePhone(loginForm.phone)
  if (phoneErr) {
    showToast(phoneErr)
    return
  }

  const pwdErr = validatePassword(loginForm.password)
  if (pwdErr) {
    showToast(pwdErr)
    return
  }

  if (!loginAgreed.value) {
    showToast('请先同意用户协议')
    return
  }

  loginLoading.value = true
  userStore
    .login(loginForm.phone, loginForm.password)
    .then(() => {
      showToast('登录成功', 'success')
      setTimeout(() => {
        // 返回上一页或跳转首页
        const pages = getCurrentPages()
        if (pages.length > 1) {
          uni.navigateBack()
        } else {
          uni.reLaunch({ url: '/pages/index/index' })
        }
      }, 500)
    })
    .catch((e) => {
      showToast(e.detail || '登录失败')
    })
    .finally(() => {
      loginLoading.value = false
    })
}

// ===== 注册 =====
function handleRegister() {
  // 昵称（选填但填写后需校验长度）
  if (regForm.nickname && (regForm.nickname.length < 2 || regForm.nickname.length > 20)) {
    showToast('昵称长度为2-20个字符')
    return
  }

  const phoneErr = validatePhone(regForm.phone)
  if (phoneErr) {
    showToast(phoneErr)
    return
  }

  if (!regForm.smsCode || regForm.smsCode.length !== 6) {
    showToast('请输入6位验证码')
    return
  }

  const pwdErr = validatePassword(regForm.password)
  if (pwdErr) {
    showToast(pwdErr)
    return
  }

  if (regForm.password !== regForm.confirmPassword) {
    showToast('两次密码输入不一致')
    return
  }

  if (!regAgreed.value) {
    showToast('请先同意用户协议')
    return
  }

  regLoading.value = true
  const data = {
    phone: regForm.phone,
    sms_code: regForm.smsCode,
    password: regForm.password,
    captcha_token: regForm.captchaToken,
    agree_terms: true,
  }
  if (regForm.nickname) data.nickname = regForm.nickname
  if (regForm.inviteCode) data.invite_code = regForm.inviteCode

  userStore
    .register(data)
    .then(() => {
      showToast('注册成功', 'success')
      setTimeout(() => {
        uni.reLaunch({ url: '/pages/index/index' })
      }, 500)
    })
    .catch((e) => {
      showToast(e.detail || '注册失败')
    })
    .finally(() => {
      regLoading.value = false
    })
}

// ===== 第三方登录（预留） =====
function onSocialLogin(platform) {
  showToast('暂未开放，敬请期待')
}

// ===== 用户协议 =====
function openAgreement(type) {
  // TODO: 跳转协议页面
  showToast(type === 'service' ? '用户服务协议' : '隐私政策')
}
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: $bg-color;
  position: relative;
  overflow: hidden;
}

// 装饰背景
.deco {
  position: absolute;
  border-radius: 50%;
  filter: blur(60rpx);
  pointer-events: none;
}
.deco-1 {
  width: 400rpx;
  height: 400rpx;
  background: rgba(79, 110, 247, 0.06);
  top: 160rpx;
  right: -120rpx;
}
.deco-2 {
  width: 440rpx;
  height: 440rpx;
  background: rgba(108, 92, 231, 0.05);
  top: 560rpx;
  left: -140rpx;
}

.content {
  position: relative;
  z-index: 1;
  padding: 0 48rpx;
  padding-top: 160rpx;
}

// 品牌
.brand {
  text-align: center;
  margin-bottom: 64rpx;
}
.logo {
  width: 140rpx;
  height: 140rpx;
  border-radius: 48rpx;
  background: linear-gradient(135deg, $primary, $purple);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24rpx;
  box-shadow: $shadow-md;
}
.logo-icon {
  font-size: 56rpx;
}
.brand-title {
  display: block;
  font-size: 44rpx;
  font-weight: 700;
  color: $text-primary;
}
.brand-desc {
  display: block;
  font-size: 26rpx;
  color: $text-secondary;
  margin-top: 8rpx;
}

// Tab 栏
.tab-bar {
  position: relative;
  display: flex;
  background: $white;
  border-radius: $radius-lg;
  padding: 4rpx;
  margin-bottom: 48rpx;
  box-shadow: $shadow-sm;
}
.tab-indicator {
  position: absolute;
  top: 4rpx;
  left: 4rpx;
  width: calc(50% - 8rpx);
  height: calc(100% - 8rpx);
  background: $primary;
  border-radius: $radius-md;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.tab-indicator.tab-right {
  transform: translateX(100%);
}
.tab-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20rpx 0;
  position: relative;
  z-index: 1;
}
.tab-text {
  font-size: 28rpx;
  font-weight: 600;
  color: $text-secondary;
  transition: color 0.3s;
}
.tab-item.active .tab-text {
  color: $white;
}

// 表单
.form {
  position: relative;
}

// 字段
.field {
  margin-bottom: 24rpx;
}
.field-label {
  display: block;
  font-size: 24rpx;
  font-weight: 500;
  color: $text-secondary;
  margin-bottom: 12rpx;
  padding-left: 8rpx;
}
.field-label-muted {
  color: $text-muted;
}

// 输入框容器
.input-wrap {
  display: flex;
  align-items: center;
  background: $white;
  border-radius: $radius-lg;
  border: 2rpx solid $border-color;
  padding: 0 24rpx;
  height: 96rpx;
  transition: border-color 0.2s;
}
.input-wrap:focus-within {
  border-color: $primary;
  box-shadow: 0 0 0 6rpx rgba(79, 110, 247, 0.1);
}

.input-icon {
  font-size: 28rpx;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.input {
  flex: 1;
  height: 100%;
  font-size: 28rpx;
  color: $text-primary;
}
.placeholder {
  color: #ccc;
}

.input-hint {
  font-size: 20rpx;
  color: $text-muted;
  flex-shrink: 0;
}

// 区号选择
.area-code {
  display: flex;
  align-items: center;
  gap: 8rpx;
  padding-right: 20rpx;
  flex-shrink: 0;
}
.area-code-text {
  font-size: 28rpx;
  font-weight: 500;
  color: $text-primary;
}
.area-code-arrow {
  font-size: 16rpx;
  color: $text-muted;
}
.input-divider {
  width: 2rpx;
  height: 32rpx;
  background: $border-color;
  flex-shrink: 0;
}

// 密码显隐
.pwd-toggle {
  font-size: 28rpx;
  padding: 8rpx;
  flex-shrink: 0;
}

// 验证码按钮
.code-wrap {
  padding-right: 0;
}
.code-btn {
  padding: 0 24rpx;
  height: 100%;
  display: flex;
  align-items: center;
  border-left: 2rpx solid $border-color;
  flex-shrink: 0;
}
.code-btn.disabled {
  opacity: 0.5;
}
.code-btn-text {
  font-size: 24rpx;
  font-weight: 600;
  color: $primary;
  white-space: nowrap;
}
.code-btn.disabled .code-btn-text {
  color: $text-muted;
}

// 密码强度
.pwd-strength {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 8rpx;
  padding-left: 8rpx;
}
.strength-bars {
  display: flex;
  gap: 6rpx;
}
.strength-bar {
  width: 56rpx;
  height: 6rpx;
  border-radius: 3rpx;
  background: $border-color;
}
.strength-bar.active.weak {
  background: $danger;
}
.strength-bar.active.medium {
  background: #FFA726;
}
.strength-bar.active.strong {
  background: $success;
}
.strength-text {
  font-size: 20rpx;
  color: $text-secondary;
}

// 主按钮
.btn-primary {
  width: 100%;
  height: 96rpx;
  background: linear-gradient(135deg, $primary, $purple);
  color: $white;
  border-radius: $radius-lg;
  font-size: 30rpx;
  font-weight: 600;
  border: none;
  margin-top: 16rpx;
  box-shadow: $shadow-md;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-primary::after {
  border: none;
}
.btn-primary[disabled] {
  opacity: 0.7;
}

// 分割线
.divider {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin: 48rpx 0;
}
.divider-line {
  flex: 1;
  height: 2rpx;
  background: $border-color;
}
.divider-text {
  font-size: 22rpx;
  color: $text-muted;
  white-space: nowrap;
}

// 第三方登录
.social-login {
  display: flex;
  justify-content: center;
  gap: 56rpx;
}
.social-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}
.social-icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.social-icon-text {
  font-size: 32rpx;
  font-weight: 700;
}
.social-wechat {
  background: rgba(7, 193, 96, 0.1);
}
.social-wechat .social-icon-text {
  color: #07C160;
}
.social-apple {
  background: rgba(0, 0, 0, 0.05);
}
.social-apple .social-icon-text {
  color: $text-primary;
}
.social-qq {
  background: rgba(18, 183, 245, 0.1);
}
.social-qq .social-icon-text {
  color: #12B7F5;
}
.social-label {
  font-size: 20rpx;
  color: $text-secondary;
}

// 协议
.agreement {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
  margin-top: 32rpx;
  padding: 0 8rpx;
  flex-wrap: wrap;
}
.checkbox-wrap {
  flex-shrink: 0;
  margin-top: 2rpx;
}
.checkbox {
  width: 28rpx;
  height: 28rpx;
  border-radius: 6rpx;
  border: 2rpx solid $border-color;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.checkbox.checked {
  background: $primary;
  border-color: $primary;
}
.check-mark {
  color: $white;
  font-size: 18rpx;
  line-height: 1;
}
.agreement-text {
  font-size: 20rpx;
  color: $text-muted;
  line-height: 32rpx;
}
.agreement-link {
  font-size: 20rpx;
  color: $primary;
  line-height: 32rpx;
}

// 底部提示
.footer-tip {
  text-align: center;
  margin-top: 64rpx;
  padding-bottom: 48rpx;
}
.footer-tip-text {
  font-size: 20rpx;
  color: $text-muted;
}
</style>
