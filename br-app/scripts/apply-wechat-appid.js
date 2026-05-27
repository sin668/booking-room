const fs = require('fs')
const path = require('path')

const DEFAULT_OUTPUT_DIR = path.resolve(__dirname, '../dist/build/mp-weixin')
const DEFAULT_DEV_OUTPUT_DIR = path.resolve(__dirname, '../dist/dev/mp-weixin')
const DEFAULT_SERVER_ENV_PATH = path.resolve(__dirname, '../../br-server/.env')

function parseEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return {}

  return fs
    .readFileSync(filePath, 'utf8')
    .split(/\r?\n/)
    .reduce((acc, line) => {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#')) return acc

      const equalIndex = trimmed.indexOf('=')
      if (equalIndex === -1) return acc

      const key = trimmed.slice(0, equalIndex).trim()
      let value = trimmed.slice(equalIndex + 1).trim()
      if (
        (value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))
      ) {
        value = value.slice(1, -1)
      }
      acc[key] = value
      return acc
    }, {})
}

function resolveWechatAppId({
  env = process.env,
  serverEnvPath = DEFAULT_SERVER_ENV_PATH,
} = {}) {
  if (env.VITE_WECHAT_MINI_APPID) return env.VITE_WECHAT_MINI_APPID
  if (env.WECHAT_MINI_APPID) return env.WECHAT_MINI_APPID

  const serverEnv = parseEnvFile(serverEnvPath)
  return serverEnv.WECHAT_MINI_APPID || ''
}

function applyWechatAppId({
  outputDir = DEFAULT_OUTPUT_DIR,
  appid = resolveWechatAppId(),
} = {}) {
  const projectConfigPath = path.join(outputDir, 'project.config.json')
  if (!fs.existsSync(projectConfigPath)) {
    throw new Error(`未找到微信小程序 project.config.json: ${projectConfigPath}`)
  }

  if (!appid) {
    return { applied: false, reason: 'missing-appid' }
  }

  const projectConfig = JSON.parse(fs.readFileSync(projectConfigPath, 'utf8'))
  projectConfig.appid = appid
  fs.writeFileSync(
    projectConfigPath,
    `${JSON.stringify(projectConfig, null, 2)}\n`,
  )

  return { applied: true, appid }
}

function resolveOutputDirFromArgs(argv = process.argv.slice(2)) {
  const modeIndex = argv.indexOf('--mode')
  const mode = modeIndex >= 0 ? argv[modeIndex + 1] : ''
  if (mode === 'dev') return DEFAULT_DEV_OUTPUT_DIR
  if (mode === 'build') return DEFAULT_OUTPUT_DIR

  const outputIndex = argv.indexOf('--output-dir')
  if (outputIndex >= 0 && argv[outputIndex + 1]) {
    return path.resolve(process.cwd(), argv[outputIndex + 1])
  }

  return DEFAULT_OUTPUT_DIR
}

if (require.main === module) {
  const result = applyWechatAppId({
    outputDir: resolveOutputDirFromArgs(),
  })
  if (result.applied) {
    console.log(`已写入微信小程序 AppID: ${result.appid}`)
  } else {
    console.warn(
      '未配置 WECHAT_MINI_APPID/VITE_WECHAT_MINI_APPID，微信开发者工具将继续使用 touristappid，uni.login 可能失败。',
    )
  }
}

module.exports = {
  applyWechatAppId,
  resolveWechatAppId,
  resolveOutputDirFromArgs,
}
