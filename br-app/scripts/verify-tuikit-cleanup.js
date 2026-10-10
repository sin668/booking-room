const assert = require('assert')
const fs = require('fs')
const path = require('path')

const cwd = path.resolve(__dirname, '..')
const r = (rel) => fs.existsSync(path.resolve(cwd, rel))
const read = (rel) => fs.readFileSync(path.resolve(cwd, rel), 'utf8')

assert.ok(!r('src/TUIKit/debug'), 'debug/ 目录未删除')
assert.ok(!r('src/TUIKit/index.vue'), 'index.vue 未删除')
assert.ok(!r('src/TUIKit/vue.config.js'), 'vue.config.js 未删除')

const idx = read('src/TUIKit/index.ts')
assert.ok(!/genTestUserSig/.test(idx), 'index.ts 仍引用 genTestUserSig')
assert.ok(!/index\.vue/.test(idx), 'index.ts 仍引用 index.vue')
assert.ok(!/hideTUIChatFeatures/.test(idx), 'index.ts 仍引用 hideTUIChatFeatures')
assert.ok(!/TUIComponents/.test(idx), 'index.ts 仍引用 TUIComponents')
assert.ok(/export\s*\{\s*TUIChatKit\s*\}/.test(idx), 'index.ts 应只导出 TUIChatKit')
assert.ok(/import Server from/.test(idx), 'index.ts 缺少 Server 导入')

console.log('TUIKit 瘦身验证通过')
