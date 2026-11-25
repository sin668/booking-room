const assert = require('assert')
const fs = require('fs')
const path = require('path')
const vm = require('vm')

const appRoot = path.resolve(__dirname, '..')

function loadModule(relativePath, injected = {}, cache = {}) {
  const filename = path.join(appRoot, relativePath)
  if (cache[filename]) return cache[filename]

  let source = fs.readFileSync(filename, 'utf8')
  const exportedNames = []
  source = source.replace(/import\s+\{([^}]+)\}\s+from\s+['"]([^'"]+)['"];?/g, (_match, names, request) => {
    return `const { ${names.trim()} } = __resolveImport(${JSON.stringify(request)})`
  })
  source = source.replace(/export\s+const\s+([A-Za-z0-9_$]+)\s*=/g, (_match, name) => {
    exportedNames.push(name)
    return `const ${name} =`
  })
  source = source.replace(/export\s+function\s+([A-Za-z0-9_$]+)\s*\(/g, (_match, name) => {
    exportedNames.push(name)
    return `function ${name}(`
  })
  source = source.replace(/export\s+\{([^}]+)\}/g, (_match, names) => {
    names.split(',').forEach((name) => {
      const trimmed = name.trim()
      if (trimmed) exportedNames.push(trimmed)
    })
    return ''
  })
  source += `\n${[...new Set(exportedNames)].map((name) => `exports.${name} = ${name}`).join('\n')}`

  const exports = {}
  cache[filename] = exports

  function resolveImport(request) {
    if (injected[request]) return injected[request]
    if (request.startsWith('@/')) {
      return loadModule(`src/${request.slice(2)}.js`, injected, cache)
    }
    throw new Error(`Unsupported test import: ${request}`)
  }

  const sandbox = {
    exports,
    console,
    setTimeout,
    clearTimeout,
    uni: global.uni,
    __resolveImport: resolveImport,
  }
  vm.runInNewContext(source, sandbox, { filename })
  return exports
}

function main() {
  const { formatNotificationTime } = loadModule('src/utils/formatters.js')

  // 后端无时区 UTC 字符串：+8 小时且不出现 T
  assert.equal(formatNotificationTime('2020-11-25T03:08:00'), '11-25 11:08')
  assert.equal(formatNotificationTime('2020-11-25 03:08:00'), '11-25 11:08')
  assert.equal(formatNotificationTime('2020-11-25T03:08'), '11-25 11:08')

  // 跨日 +8：UTC 16:30 属于北京次日
  assert.equal(formatNotificationTime('2020-11-24T16:30:00'), '11-25 00:30')

  // 已带时区的值不重复偏移
  assert.equal(formatNotificationTime('2020-11-25T03:08:00Z'), '11-25 11:08')
  assert.equal(formatNotificationTime('2020-11-25T11:08:00+08:00'), '11-25 11:08')

  // 空值与非法值
  assert.equal(formatNotificationTime(''), '')
  assert.equal(formatNotificationTime(null), '')
  assert.equal(formatNotificationTime('not-a-time'), 'not-a-time')

  // 相对时间
  const toNaiveUtc = (date) => date.toISOString().slice(0, 19)
  assert.equal(formatNotificationTime(toNaiveUtc(new Date(Date.now() - 30 * 1000))), '刚刚')
  assert.equal(formatNotificationTime(toNaiveUtc(new Date(Date.now() - 5 * 60 * 1000))), '5分钟前')
  assert.equal(formatNotificationTime(toNaiveUtc(new Date(Date.now() - 2 * 60 * 60 * 1000))), '2小时前')

  console.log('verify-notification-time: all assertions passed')
}

main()
