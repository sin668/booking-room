import { get, post } from '@/utils/request'

/**
 * 发送短信验证码
 */
export function sendCode(data) {
  return post('/api/v1/auth/send-code', data)
}

/**
 * 用户注册
 */
export function register(data) {
  return post('/api/v1/auth/register', data)
}

/**
 * 用户登录（手机号 + 密码）
 */
export function login(data) {
  return post('/api/v1/auth/login', data)
}

/**
 * 微信快速登录
 */
export function wechatLogin(data) {
  return post('/api/v1/auth/wechat-login', data)
}

/**
 * 微信手机号授权绑定
 */
export function bindWechatPhone(data) {
  return post('/api/v1/auth/wechat/bind-phone', data)
}

/**
 * 短信备用绑定手机号
 */
export function bindPhoneBySms(data) {
  return post('/api/v1/auth/wechat/bind-phone/sms', data)
}

/**
 * 刷新 Token
 */
export function refreshToken() {
  return post('/api/v1/auth/refresh')
}

/**
 * 退出登录
 */
export function logout() {
  return post('/api/v1/auth/logout')
}

/**
 * 获取当前用户信息
 */
export function getMe() {
  return get('/api/v1/auth/me')
}
