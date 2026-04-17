import { defineStore } from 'pinia'
import { getToken, setToken, removeToken } from '@/utils/request'
import * as authApi from '@/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken(),
    userInfo: null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    nickname: (state) => state.userInfo?.nickname || '',
    phone: (state) => state.userInfo?.phone || '',
  },

  actions: {
    /** 发送短信验证码 */
    async sendCode(phone, captchaToken) {
      return authApi.sendCode({ phone, captcha_token: captchaToken })
    },

    /** 用户注册 */
    async register(data) {
      const res = await authApi.register(data)
      this.token = res.access_token
      setToken(res.access_token)
      // 注册成功后获取用户信息（失败不阻塞注册流程）
      this.fetchUserInfo().catch(() => {})
      return res
    },

    /** 用户登录 */
    async login(phone, password) {
      const res = await authApi.login({ phone, password })
      this.token = res.access_token
      setToken(res.access_token)
      // 登录成功后获取用户信息（失败不阻塞登录流程）
      this.fetchUserInfo().catch(() => {})
      return res
    },

    /** 获取当前用户信息 */
    async fetchUserInfo() {
      const user = await authApi.getMe()
      this.userInfo = user
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
      this.token = ''
      this.userInfo = null
      removeToken()
    },

    /** 自动登录（检查本地 Token 有效性） */
    async autoLogin() {
      if (!this.token) return false
      try {
        await this.fetchUserInfo()
        return true
      } catch {
        this.logout()
        return false
      }
    },
  },
})
