export function formatWechatBindingStatus(summary = {}) {
  return summary.wechat_bound ? '已绑定' : '未绑定'
}

export function formatIdentityVerificationStatus(status) {
  if (status === 'verified') return '已认证'
  if (status === 'pending') return '审核中'
  if (status === 'rejected') return '未通过'
  return '未认证'
}

export function formatAccountStatus(status) {
  if (status === 'deleted') return '已注销'
  if (status === 'banned') return '已封禁'
  if (status === 'disabled') return '已停用'
  return '正常'
}

export function formatDeactivationRiskReasons(risks = []) {
  if (!Array.isArray(risks) || risks.length === 0) return []
  return risks.map((risk) => risk.message || mapRiskCode(risk.code)).filter(Boolean)
}

export function mapRiskCode(code) {
  const messages = {
    wallet_balance: '钱包余额需清零后才能注销',
    unfinished_booking: '存在未完成预约',
    pending_booking_payment: '存在待处理预约支付',
    pending_wallet_transaction: '存在待处理支付或退款',
    available_coupon: '存在未使用卡券',
  }
  return messages[code] || '存在未处理事项'
}

export function validateIdentityCard(value) {
  const id = String(value || '').trim().toUpperCase()
  if (!/^\d{17}[\dX]$/.test(id)) return false
  const factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
  const checks = '10X98765432'
  const total = factors.reduce((sum, factor, index) => sum + Number(id[index]) * factor, 0)
  return checks[total % 11] === id[17]
}

export function mapAccountSecurityError(error, action = '') {
  const detail = typeof error?.detail === 'string' ? error.detail : ''
  const nestedMessage = typeof error?.detail?.message === 'string' ? error.detail.message : ''
  const text = detail || nestedMessage || error?.message || ''
  if (text.includes('旧密码')) return '旧密码不正确'
  if (text.includes('不一致')) return '两次输入的新密码不一致'
  if (text.includes('弱') || text.includes('6') || text.includes('20')) return '新密码需为 6-20 位'
  if (text.includes('身份证')) return '身份证号格式不正确'
  if (text.includes('实名') || text.includes('覆盖')) return '已完成实名认证，不能覆盖为不同实名资料'
  if (text.includes('注销') || text.includes('未处理事项')) return '账号存在未处理事项，暂不能注销'
  if (text.includes('401') || text.includes('登录')) return '登录已过期，请重新登录'
  if (action === 'password') return '密码修改失败，请稍后再试'
  if (action === 'identity') return '实名认证提交失败，请稍后再试'
  if (action === 'deactivation') return '注销失败，请稍后再试'
  return text || '操作失败，请稍后再试'
}
