// 富媒体（视频/图片）发送失败必须可见：选择器要有 fail 出口、发送要 catch、
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
const calls = [...useUpload.matchAll(/TUIGlobal\?\.(chooseImage|chooseVideo)\(\{([\s\S]*?)\n {4}\}\)/g)]
assert.strictEqual(calls.length, 4, `choose* 调用数量变化，实际 ${calls.length} 个`)
for (const call of calls) {
  assert.ok(/\bfail:/.test(call[2]), `${call[1]} 调用缺少 fail 回调`)
  assert.ok(/genChooseFailHandler/.test(call[2]), `${call[1]} 的 fail 未走统一提示`)
}
// 用户取消不能报错误提示
assert.ok(/includes\('cancel'\)/.test(useUpload), '取消选择未被排除')

const utils = read(utilsPath)
assert.ok(
  /TUIChatService\.sendVideoMessage\([^)]*\)\?\.catch\(reportSendFailure\('视频'\)\)/.test(utils.replace(/\n\s*/g, ' ')),
  'sendVideoMessage 未 catch 失败原因',
)
assert.ok(/function reportSendFailure/.test(utils), '缺少 reportSendFailure')
assert.ok(/getIMLastUploadError\(\)/.test(utils), '未读取 uploadFile 拦截到的真实失败')
// host 取自真实上传 url，这是判断域名是否过白名单的关键
assert.ok(/upload\.url\.split\('\/'\)\[2\]/.test(utils), 'Toast 未显示真实上传 host')
assert.ok(/err\?\.code/.test(utils), 'Toast 未显示 SDK 错误码')

// im.js 侧的拦截出口必须还在，否则上面拿到的一律是空
const im = read('src/utils/im.js')
assert.ok(/export function getIMLastUploadError/.test(im), 'im.js 缺少 getIMLastUploadError')
assert.ok(/url:\s*options\.url/.test(im), '上传失败未记录真实 url')

console.log('media send diagnostics checks passed')
