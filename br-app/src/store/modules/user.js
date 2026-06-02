import { defineStore } from 'pinia'
import {
  getRefreshToken,
  getToken,
  removeRefreshToken,
  removeToken,
  refreshAccessToken,
  setRefreshToken,
  setToken,
} from '@/utils/request'
import * as authApi from '@/api/auth'
import * as userProfileApi from '@/api/userProfile'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken(),
    refreshToken: getRefreshToken(),
    userInfo: null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    nickname: (state) => state.userInfo?.nickname || '',
    phone: (state) => state.userInfo?.phone || '',
    username: (state) => state.userInfo?.username || '',
    avatar: (state) => state.userInfo?.avatar || '',
    usernameUpdatedAt: (state) => state.userInfo?.username_updated_at || null,
  },

  actions: {
    /** 保存认证响应中的 Token */
    applyTokenResponse(res) {
      if (!res?.access_token) return
      this.token = res.access_token
      this.refreshToken = res.refresh_token || ''
      setToken(res.access_token)
      if (res.refresh_token) {
        setRefreshToken(res.refresh_token)
      } else if (Object.prototype.hasOwnProperty.call(res, 'refresh_token')) {
        removeRefreshToken()
      }
    },

    /** 发送短信验证码 */
    async sendCode(phone, captchaToken) {
      return authApi.sendCode({ phone, captcha_token: captchaToken })
    },

    /** 用户注册 */
    async register(data) {
      const res = await authApi.register(data)
      this.applyTokenResponse(res)
      // 注册成功后获取用户信息（失败不阻塞注册流程）
      this.fetchUserInfo().catch(() => {})
      return res
    },

    /** 用户登录 */
    async login(phone, password) {
      const res = await authApi.login({ phone, password })
      this.applyTokenResponse(res)
      // 登录成功后获取用户信息（失败不阻塞登录流程）
      this.fetchUserInfo().catch(() => {})
      return res
    },

    /** 微信快速登录 */
    async wechatLogin(code) {
      const res = await authApi.wechatLogin({ code })
      this.applyTokenResponse(res)
      // 微信登录成功后获取用户信息（失败不阻塞登录流程）
      this.fetchUserInfo().catch(() => {})
      return res
    },

    /** 获取当前用户信息 */
    async fetchUserInfo() {
      const user = await userProfileApi.getMe()
      this.userInfo = user
    },

    /** 更新当前用户资料 */
    async updateProfile(payload) {
      const user = await userProfileApi.updateMe(payload)
      this.userInfo = user
      return user
    },

    /** 微信手机号授权绑定 */
    async bindWechatPhone(code) {
      const res = await authApi.bindWechatPhone({ code })
      return this.applyPhoneBindingResult(res)
    },

    /** 短信备用绑定手机号 */
    async bindPhoneBySms(phone, smsCode) {
      const res = await authApi.bindPhoneBySms({ phone, sms_code: smsCode })
      return this.applyPhoneBindingResult(res)
    },

    /** 处理手机号绑定结果；合并账号时后端会返回新的 TokenResponse */
    async applyPhoneBindingResult(res) {
      if (res?.access_token) {
        this.applyTokenResponse(res)
        await this.fetchUserInfo()
        return this.userInfo
      }

      if (res?.id !== undefined || res?.phone !== undefined || res?.username !== undefined) {
        this.userInfo = res
      }

      await this.fetchUserInfo()
      return this.userInfo
    },

    /** 退出登录 */
    async logout() {
      try {
        if (this.token) {
          await authApi.logout()
        }
      } catch {
        // 即使 API 调用失败也要清理本地状态
      }
      this.clearLocalSession()
    },

    /** 清理本地登录态，不依赖后端会话状态 */
    clearLocalSession() {
      this.token = ''
      this.refreshToken = ''
      this.userInfo = null
      removeToken()
      removeRefreshToken()
    },

    /** 自动登录（检查本地 Token 有效性） */
    async autoLogin() {
      if (!this.token && !this.refreshToken) return false

      try {
        if (!this.token && this.refreshToken) {
          const res = await refreshAccessToken()
          this.token = res
        }
        await this.fetchUserInfo()
        return true
      } catch {
        this.logout()
        return false
      }
    },
  },
})
