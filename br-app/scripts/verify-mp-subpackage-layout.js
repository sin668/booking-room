// 校验小程序产物的分包归属：主包里不能留着只有子包用到的 JS，
// 且搬家改写过路径后每条相对 require 都必须还能解析到真实文件。
// 运行：node scripts/verify-mp-subpackage-layout.js（需在 npm run build:mp-weixin 之后）
const fs = require('fs')
const path = require('path')

const BUILD_DIR = path.join(__dirname, '../dist/build/mp-weixin')
const assert = require('assert')

assert(fs.existsSync(BUILD_DIR), `产物目录不存在：${BUILD_DIR}，请先 npm run build:mp-weixin`)

const app = JSON.parse(fs.readFileSync(path.join(BUILD_DIR, 'app.json'), 'utf8'))
const subRoots = (app.subPackages || []).map(entry => entry.root)

const files = []
;(function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const item = path.join(dir, entry.name)
    if (entry.isDirectory()) walk(item)
    else if (entry.name.endsWith('.js')) files.push(path.relative(BUILD_DIR, item).split(path.sep).join('/'))
  }
})(BUILD_DIR)
const known = new Set(files)

const referrers = new Map()
for (const file of files) {
  const content = fs.readFileSync(path.join(BUILD_DIR, file), 'utf8')
  for (const match of content.matchAll(/require\("(\.[^"]+)"\)/g)) {
    const target = path.normalize(path.join(path.dirname(file), match[1])).split(path.sep).join('/')
    assert(known.has(target), `${file} 的 require("${match[1]}") 解析不到文件：${target}`)
    if (!referrers.has(target)) referrers.set(target, new Set())
    referrers.get(target).add(file)
  }
}

const inSubpackage = file => subRoots.some(root => file.startsWith(`${root}/`))
for (const [target, set] of referrers) {
  if (inSubpackage(target)) continue
  const owners = new Set([...set].map(file => subRoots.find(root => file.startsWith(`${root}/`))))
  if (owners.size !== 1 || owners.has(undefined)) continue
  assert(
    false,
    `主包残留未使用 JS：${target} 只被分包 ${[...owners][0]}/ 引用，`
      + `请加进 scripts/post-build-move-assets.js 的 MOVES`,
  )
}

console.log(`mp subpackage layout checks passed (${files.length} js, subpackages: ${subRoots.join(', ')})`)
