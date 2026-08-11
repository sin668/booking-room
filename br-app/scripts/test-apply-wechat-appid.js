const assert = require('assert')
const fs = require('fs')
const os = require('os')
const path = require('path')

const {
  applyWechatAppId,
  resolveWechatAppId,
  resolveOutputDirFromArgs,
} = require('./apply-wechat-appid')

const TEST_APPID = 'test-wechat-mini-appid'
const TEST_ENV_APPID = 'test-env-wechat-mini-appid'

function makeTempProject(appid = 'touristappid') {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'wechat-appid-test-'))
  const outputDir = path.join(root, 'dist/build/mp-weixin')
  fs.mkdirSync(outputDir, { recursive: true })
  fs.writeFileSync(
    path.join(outputDir, 'project.config.json'),
    JSON.stringify({ appid, projectname: '去静界' }, null, 2),
  )
  return { root, outputDir }
}

function readProjectAppId(outputDir) {
  return JSON.parse(
    fs.readFileSync(path.join(outputDir, 'project.config.json'), 'utf8'),
  ).appid
}

{
  const { outputDir } = makeTempProject()
  const result = applyWechatAppId({
    outputDir,
    appid: TEST_APPID,
  })

  assert.equal(result.applied, true)
  assert.equal(readProjectAppId(outputDir), TEST_APPID)
}

{
  const { outputDir } = makeTempProject('touristappid')
  const result = applyWechatAppId({ outputDir, appid: '' })

  assert.equal(result.applied, false)
  assert.equal(readProjectAppId(outputDir), 'touristappid')
}

{
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'wechat-env-test-'))
  const envPath = path.join(root, 'br-server/.env')
  fs.mkdirSync(path.dirname(envPath), { recursive: true })
  fs.writeFileSync(envPath, `WECHAT_MINI_APPID=${TEST_ENV_APPID}\n`)

  const appid = resolveWechatAppId({
    env: {},
    serverEnvPath: envPath,
  })

  assert.equal(appid, TEST_ENV_APPID)
}

function normalizePathSeparators(filePath) {
  return filePath.replace(/\\/g, '/')
}

assert.ok(normalizePathSeparators(resolveOutputDirFromArgs(['--mode', 'dev'])).endsWith('dist/dev/mp-weixin'))
assert.ok(normalizePathSeparators(resolveOutputDirFromArgs(['--mode', 'build'])).endsWith('dist/build/mp-weixin'))

console.log('微信小程序 AppID 注入脚本验证通过')
