// 富媒体（视频/图片）发送失败必须可见：选择器要有 fail 出口、发送要 try-catch、
// Toast 要带上真实上传 host + errMsg + SDK 错误码，否则真机上分不清是域名还是权限。
const assert = require('assert')
const fs = require('fs')
const path = require('path')

const ROOT = path.resolve(__dirname, '..')

function read(relative) {
  return fs.readFileSync(path.join(ROOT, relative), 'utf8')
}

// 断言相对 import 能解析到真实文件（TUIKit 里层级容易写错一级），@ 按 uni-app 别名指向 src
function assertResolves(fromFile, spec) {
  const base = spec.startsWith('@/')
    ? path.join(ROOT, 'src', spec.slice(2))
    : path.resolve(path.join(ROOT, fromFile), '..', spec)
  const ok = ['', '.ts', '.js', '.vue', '/index.ts', '/index.js'].some(ext => fs.existsSync(base + ext))
  assert.ok(ok, `${fromFile} 的 import "${spec}" 解析不到文件`)
}

const useUploadPath = 'src/TUIKit/components/TUIChat/message-input-toolbar/uploadToolkit/useUpload.ts'
const utilsPath = 'src/TUIKit/components/TUIChat/message-input-toolbar/uploadToolkit/utils.ts'

assertResolves(useUploadPath, '../../../common/Toast/index')
assertResolves(utilsPath, '../../../common/Toast/index')
assertResolves(utilsPath, '@/utils/im')

const useUpload = read(useUploadPath)

// chooseVideo 的两个入口（chooseVideoInUniApp / chooseCameraInUniApp）必须有 try-catch 包裹，
// 因为 SDK createVideoMessage 会同步抛错，被 wx success 回调吞掉就完全看不到。
const videoFns = [...useUpload.matchAll(/const (choose\w+InUniApp)\s*=\s*\(\)\s*=>\s*\{([\s\S]*?)\n {2}\};/g)]
  .filter(m => m[2].includes('chooseVideo'))
assert.strictEqual(videoFns.length, 2, `chooseVideo 入口数量变化，实际 ${videoFns.length} 个`)
for (const fn of videoFns) {
  assert.ok(/try\s*\{/.test(fn[2]), `${fn[1]} 缺少 try-catch 包裹 chooseVideo`)
  assert.ok(/TUIGlobal\.chooseVideo\(/.test(fn[2]), `${fn[1]} 未显式调用 chooseVideo（不能只用 ?.）`)
  assert.ok(/\bfail:/.test(fn[2]), `${fn[1]} 缺少 fail 回调`)
  assert.ok(/genChooseFailHandler/.test(fn[2]), `${fn[1]} 的 fail 未走统一提示`)
}
// 用户取消不能报错误提示
assert.ok(/includes\('cancel'\)/.test(useUpload), '取消选择未被排除')

// success 回调里 currentConversation 为空时必须提示，否则点了视频选了之后完全没反应
assert.ok(
  useUpload.match(/success:[\s\S]*?会话未加载/),
  '视频 success 回调未处理 currentConversation 为空的情况',
)

const utils = read(utilsPath)
// sendVideoMessage 必须用 try-catch 包裹 TUIChatService.sendVideoMessage，
// 因为 createVideoMessage 内部同步抛错不会走 Promise.reject
assert.ok(
  /try\s*\{[\s\S]*?TUIChatService\.sendVideoMessage\(/.test(utils),
  'sendVideoMessage 未用 try-catch 包裹 TUIChatService.sendVideoMessage',
)
assert.ok(/function reportSendFailure/.test(utils), '缺少 reportSendFailure')
assert.ok(/getIMLastUploadError\(\)/.test(utils), '未读取 uploadFile 拦截到的真实失败')
// host 取自真实上传 url，这是判断域名是否过白名单的关键
assert.ok(/upload\.url\.split\('\/'\)\[2\]/.test(utils), 'Toast 未显示真实上传 host')
assert.ok(/err\?\.code/.test(utils), 'Toast 未显示 SDK 错误码')

// 诊断日志：真机排查时看 chooseVideo 返回的数据结构
assert.ok(/视频发送入参/.test(utils), '缺少视频入参诊断日志')
assert.ok(/tempFilePath/.test(utils), '诊断日志未记录 tempFilePath')

// im.js 侧的拦截出口必须还在，否则上面拿到的一律是空
const im = read('src/utils/im.js')
assert.ok(/export function getIMLastUploadError/.test(im), 'im.js 缺少 getIMLastUploadError')
assert.ok(/url:\s*options\.url/.test(im), '上传失败未记录真实 url')

console.log('media send diagnostics checks passed')
