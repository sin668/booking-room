const fs = require('fs')
const path = require('path')

const root = path.resolve(__dirname, '..')

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), 'utf8')
}

function assertContains(file, needle, message) {
  const content = read(file)
  if (!content.includes(needle)) {
    throw new Error(`${message}：${file} 缺少 ${needle}`)
  }
}

function assertMatches(file, pattern, message) {
  const content = read(file)
  if (!pattern.test(content)) {
    throw new Error(`${message}：${file} 未匹配 ${pattern}`)
  }
}

function assertFileExists(relativePath, message) {
  if (!fs.existsSync(path.join(root, relativePath))) {
    throw new Error(`${message}：${relativePath} 不存在`)
  }
}

assertContains(
  'src/api/activities.js',
  'getActivityDetail',
  '活动 API 需要封装详情查询'
)
assertContains(
  'src/api/activities.js',
  'claimActivityCoupon',
  '活动 API 需要封装领券请求'
)
assertMatches(
  'src/api/activities.js',
  /post\(`\/api\/v1\/activities\/\$\{activityId\}\/coupons\/\$\{activityCouponId\}\/claim`/,
  '领券请求路径需要携带活动 ID 和活动卡券 ID'
)

assertMatches(
  'src/pages/index/index.vue',
  /@tap="onTapActivity\(activity\)"/,
  '首页活动卡片需要点击跳转'
)
assertContains(
  'src/pages/index/index.vue',
  '/pages/activity/detail?id=',
  '首页活动跳转需要携带活动 ID'
)

assertContains(
  'src/pages.json',
  '"path": "pages/activity/detail"',
  '需要注册活动详情页路由'
)

assertFileExists('src/pages/activity/detail.vue', '需要新增活动详情页')
assertContains(
  'src/pages/activity/detail.vue',
  '<rich-text',
  '活动详情正文需要使用小程序安全富文本组件'
)
assertContains(
  'src/pages/activity/detail.vue',
  'v-if="hasContent"',
  '活动正文为空时不应展示空模块'
)
;['立即领取', '已领取', '已抢光', '未开始', '已结束'].forEach((text) => {
  assertContains('src/pages/activity/detail.vue', text, `活动详情页需要覆盖“${text}”状态文案`)
})
assertContains(
  'src/pages/activity/detail.vue',
  '/pages/login/login',
  '未登录领券需要引导登录'
)
assertContains(
  'src/pages/activity/detail.vue',
  '领取成功',
  '领券成功需要中文提示'
)

assertContains(
  'src/pages/coupon/index.vue',
  '活动领取',
  '卡券包需要展示活动来源文案'
)
assertContains(
  'src/pages/booking/confirm.vue',
  '活动领取',
  '预约可用券弹层需要展示活动来源文案'
)

console.log('活动领券前端静态验证通过')
