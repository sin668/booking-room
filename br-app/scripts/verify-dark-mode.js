const fs = require('fs')
const path = require('path')

const root = path.resolve(__dirname, '..')
const read = (p) => fs.readFileSync(path.resolve(root, p), 'utf8')
const failures = []

const tokens = [
  '--primary', '--primary-light', '--primary-soft', '--orange-light',
  '--bg-color', '--bg-warm', '--bg-hero',
  '--surface', '--surface-soft', '--surface-muted',
  '--text-primary', '--text-secondary', '--text-muted',
  '--border-color', '--border-soft',
  '--success', '--danger',
]

const uniScss = read('src/uni.scss')
tokens.forEach((token) => {
  if (!uniScss.includes(`var(${token})`)) failures.push(`uni.scss 未通过 ${token} 引用 CSS 变量`)
})
if (/\$white:\s*var\(/.test(uniScss)) failures.push('$white 必须是字面量，不能改为 var()')

const appVue = read('src/App.vue')
if (!/\.theme-dark\s*\{[\s\S]*--bg-color/.test(appVue)) failures.push('App.vue 缺少 .theme-dark 深色变量')
tokens.forEach((token) => {
  if (!new RegExp(`${token}\\s*:`).test(appVue)) failures.push(`App.vue 未定义 ${token}`)
})
if (!/themeStore\.init\(\)/.test(appVue)) failures.push('App.vue 未初始化主题')

const mainJs = read('src/main.js')
if (!/mixin\(themeMixin\)/.test(mainJs)) failures.push('main.js 未注册 theme mixin')

const themeMixin = read('src/utils/theme.js')
if (!/onMounted\(\)[\s\S]*init\(\)/.test(themeMixin)) failures.push('theme mixin 未在页面 onMounted 重新应用原生配色')

const themeStore = read('src/store/modules/theme.js')
;['setNavigationBarColor', 'setTabBarStyle', 'theme_mode'].forEach((needle) => {
  if (!themeStore.includes(needle)) failures.push(`theme store 缺少 ${needle}`)
})

const pages = []
const walk = (dir) => {
  fs.readdirSync(path.resolve(root, dir), { withFileTypes: true }).forEach((entry) => {
    const rel = `${dir}/${entry.name}`
    if (entry.isDirectory()) {
      if (entry.name === 'TUIKit') return
      walk(rel)
    } else if (entry.name.endsWith('.vue')) {
      pages.push(rel)
    }
  })
}
walk('src/pages')
walk('src/pages-sub')

pages.forEach((page) => {
  if (!/<view class="page" :class="themeClass">/.test(read(page))) {
    failures.push(`${page} 根节点缺少 :class="themeClass"`)
  }
})

if (failures.length) {
  throw new Error(`深色模式验证失败:\n- ${failures.join('\n- ')}`)
}

console.log(`深色模式验证通过（${tokens.length} 个 token，${pages.length} 个页面）`)
