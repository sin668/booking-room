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
  const { formatCourseSchedule, formatCourseStartDate } = loadModule('src/utils/formatters.js')

  // 空值返回空字符串
  assert.equal(formatCourseSchedule(null), '')
  assert.equal(formatCourseSchedule(undefined), '')
  assert.equal(formatCourseSchedule(''), '')
  assert.equal(formatCourseSchedule('   '), '')

  // 单个时间段：每周三 14:00上课
  assert.equal(
    formatCourseSchedule('[{"weekday":3,"time_slot":"14:00-16:00"}]'),
    '每周三 14:00上课',
  )

  // 多个时间段：每周三 14:00，周四 15:00上课（乱序输入按周几排序）
  assert.equal(
    formatCourseSchedule('[{"weekday":4,"time_slot":"15:00-17:00"},{"weekday":3,"time_slot":"14:00-16:00"}]'),
    '每周三 14:00，周四 15:00上课',
  )

  // 周一至周五同一时间段：工作日 14:00上课
  assert.equal(
    formatCourseSchedule(JSON.stringify([1, 2, 3, 4, 5].map((weekday) => ({ weekday, time_slot: '14:00-16:00' })))),
    '工作日 14:00上课',
  )

  // 周一至周五时间段不同：逐项列出
  assert.equal(
    formatCourseSchedule(JSON.stringify([
      { weekday: 1, time_slot: '14:00-16:00' },
      { weekday: 2, time_slot: '14:00-16:00' },
      { weekday: 3, time_slot: '15:00-17:00' },
      { weekday: 4, time_slot: '14:00-16:00' },
      { weekday: 5, time_slot: '14:00-16:00' },
    ])),
    '每周一 14:00，周二 14:00，周三 15:00，周四 14:00，周五 14:00上课',
  )

  // 含周末不使用工作日文案
  assert.equal(
    formatCourseSchedule(JSON.stringify([1, 2, 3, 4, 5, 6].map((weekday) => ({ weekday, time_slot: '14:00-16:00' })))),
    '每周一 14:00，周二 14:00，周三 14:00，周四 14:00，周五 14:00，周六 14:00上课',
  )

  // 兼容 {weekday, start, end} 对象格式
  assert.equal(
    formatCourseSchedule('[{"weekday":1,"start":"09:00","end":"11:00"}]'),
    '每周一 09:00上课',
  )

  // 旧版纯文本原样返回
  assert.equal(formatCourseSchedule('预约制'), '预约制')
  assert.equal(formatCourseSchedule('周六 9:00-11:30'), '周六 9:00-11:30')

  // JSON 解析失败原样返回
  assert.equal(formatCourseSchedule('[broken json'), '[broken json')

  // 全部非法项时回退原样返回字符串输入
  assert.equal(
    formatCourseSchedule('[{"weekday":9,"time_slot":"14:00-16:00"}]'),
    '[{"weekday":9,"time_slot":"14:00-16:00"}]',
  )

  // 开课时间：标准日期
  assert.equal(formatCourseStartDate('2026-08-18'), '于 2026-08-18日 后开课')

  // 开课时间：兼容 datetime 格式，只取日期部分
  assert.equal(formatCourseStartDate('2026-08-18T09:00:00'), '于 2026-08-18日 后开课')

  // 开课时间：空值返回空字符串
  assert.equal(formatCourseStartDate(null), '')
  assert.equal(formatCourseStartDate(undefined), '')
  assert.equal(formatCourseStartDate(''), '')
  assert.equal(formatCourseStartDate('   '), '')

  console.log('verify-course-schedule-format: all assertions passed')
}

main()
