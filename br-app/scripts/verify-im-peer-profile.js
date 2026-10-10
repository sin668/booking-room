const assert = require('assert')
const fs = require('fs')
const path = require('path')

const read = (rel) => fs.readFileSync(path.resolve(__dirname, '..', rel), 'utf8')

const im = read('src/utils/im.js')
const store = read('src/store/modules/user.js')
const page = read('src/pages/notifications/index.vue')

// 画像写入：复用已安装 SDK 的 updateMyProfile，且只携带非空字段
assert.ok(
  /import TUIChatEngine, \{ TUIUserService \} from '@tencentcloud\/chat-uikit-engine-lite'/.test(im),
  'im.js 未引入 TUIUserService',
)
assert.ok(/export function setIMProfile/.test(im), 'im.js 未导出 setIMProfile')
assert.ok(/TUIUserService\.updateMyProfile\(payload\)/.test(im), '未调用 SDK updateMyProfile 写入 IM 用户画像')
assert.ok(
  im.includes('if (imProfile.nick) payload.nick = imProfile.nick')
    && im.includes('if (imProfile.avatar) payload.avatar = imProfile.avatar'),
  'updateMyProfile payload 未过滤空字段，可能清空对方可见的昵称/头像',
)

// 两个方向的时序都要覆盖：IM 先就绪由 store 触发推送，IM 后就绪由 ensureIM 补推
const ensureBody = im.match(/initPromise = \(async \(\) => \{([\s\S]*?)\}\)\(\)/)
assert.ok(ensureBody, '未找到 ensureIM 的初始化体')
assert.ok(
  /imInitialized = true\s*\n\s*pushIMProfile\(\)/.test(ensureBody[1]),
  'ensureIM 登录成功后未补推已缓存的本系统资料',
)
assert.ok(!/from '@\/store/.test(im), 'im.js 反向 import store 会与 store/modules/user.js 形成循环依赖')

for (const action of ['fetchUserInfo', 'updateProfile']) {
  const body = store.match(new RegExp(`async ${action}\\([^)]*\\) \\{([\\s\\S]*?)\\n {4}\\}`))
  assert.ok(body, `未找到 store action ${action}`)
  assert.ok(
    /setIMProfile\(\{ nick: user\.nickname, avatar: user\.avatar \}\)/.test(body[1]),
    `${action} 未把本系统昵称/头像同步给 IM`,
  )
}
assert.ok(
  /import \{ ensureIM, setIMProfile, resetIM \} from '@\/utils\/im'/.test(store),
  'store 未引入 setIMProfile / resetIM',
)

// 会话行渲染口径不变：头像来自 IM 画像，缺失时保留首字母占位
assert.ok(/avatar: conversation\.getAvatar\(\)/.test(page), '会话行未从会话画像读取对方头像')
assert.ok(/v-if="item\.avatar"/.test(page), '会话行缺少头像分支')
assert.ok(/conv-avatar-fallback/.test(page), '头像为空时应保留首字母占位回退')

// 未读红点及时性：订阅会话列表 + 回到页面重新拉取
assert.ok(
  /TUIStore\.watch\(StoreName\.CONV, \{ conversationList: onConversationListUpdated \}\)/.test(page),
  '未订阅会话列表变化，对方回复后无法及时刷新未读红点',
)
const showBody = page.match(/onShow\(\(\) => \{([\s\S]*?)\n\}\)/)
assert.ok(showBody, '未找到 onShow 钩子')
assert.ok(/loadConversations\(\)/.test(showBody[1]), 'onShow 未重新拉取会话列表以覆盖小程序退后台断连')

// 离开聊天页必须释放 IM 当前会话：否则引擎会把该会话的新消息自动置已读，unreadCount 恒为 0
const chatPage = read('src/TUIKit/components/TUIChat/index.vue')
const unloadBody = chatPage.match(/onUnload\(\(\) => \{([\s\S]*?)\n\}\)/)
assert.ok(unloadBody, '未找到 TUIChat 的 onUnload')
assert.ok(/\breset\(\);/.test(unloadBody[1]), 'TUIChat onUnload 未清除当前会话，对方新消息会被自动置已读')
const unmountedBody = chatPage.match(/onUnmounted\(\(\) => \{([\s\S]*?)\n\}\)/)
assert.ok(unmountedBody && /\breset\(\);/.test(unmountedBody[1]), 'TUIChat onUnmounted 应继续清除当前会话（H5 场景）')
assert.ok(
  /const reset = \(\) => \{\s*\n\s*TUIConversationService\.switchConversation\(''\)/.test(chatPage),
  'reset 未调用 switchConversation("") 清除当前会话',
)

// 退出系统登录必须同步登出 IM 并重置模块状态：否则 imInitialized 短路会让下一个用户复用上一个账号的会话
assert.ok(/export async function resetIM/.test(im), 'im.js 未导出 resetIM')
const resetBody = im.match(/export async function resetIM\(\) \{([\s\S]*?)\n\}/)
assert.ok(resetBody, '未找到 resetIM 函数体')
assert.ok(/await TUILogin\.logout\(\)/.test(resetBody[1]), 'resetIM 未调用 TUILogin.logout 登出 IM')
assert.ok(
  /imInitialized = false\s*\n\s*initPromise = null\s*\n\s*imProfile = null/.test(resetBody[1]),
  'resetIM 未重置 imInitialized/initPromise/imProfile，ensureIM 会短路复用旧账号',
)
const clearBody = store.match(/clearLocalSession\(\) \{([\s\S]*?)\n {4}\}/)
assert.ok(clearBody, '未找到 store clearLocalSession')
assert.ok(/resetIM\(\)/.test(clearBody[1]), 'clearLocalSession 未在退出登录时调用 resetIM')

console.log('IM 会话对方头像/昵称同步 + 未读会话释放 + 退出登出 IM 验证通过')
