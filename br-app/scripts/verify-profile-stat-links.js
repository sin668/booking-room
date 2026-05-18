const fs = require('fs')
const path = require('path')

const profilePath = path.resolve(__dirname, '../src/pages/profile/index.vue')
const source = fs.readFileSync(profilePath, 'utf8')

const requiredLinks = [
  { label: '钱包余额', url: '/pages/wallet/transactions' },
  { label: '卡券', url: '/pages/coupon/index' },
  { label: '学习时长', url: '/pages/study-record/index' },
]

const statsCardMatch = source.match(/<view class="stats-card">([\s\S]*?)<\/view>\s*<\/view>/)

if (!statsCardMatch) {
  throw new Error('未找到 profile 页面的 stats-card 区域')
}

const statsCard = statsCardMatch[0]
const failures = requiredLinks.filter(({ label, url }) => {
  const itemPattern = new RegExp(
    `<view\\s+class="stat-item"\\s+@tap="navigateTo\\('${url.replace(/\//g, '\\/')}'\\)"[\\s\\S]*?<text class="stat-label">${label}<\\/text>`,
  )
  return !itemPattern.test(statsCard)
})

if (failures.length > 0) {
  const details = failures.map(({ label, url }) => `${label} -> ${url}`).join(', ')
  throw new Error(`profile 统计项缺少跳转绑定: ${details}`)
}

console.log('profile 统计项跳转绑定验证通过')
