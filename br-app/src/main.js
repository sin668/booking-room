import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import shareMixin from './utils/share.js'

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  app.use(pinia)
  // 全局混入分享配置
  app.mixin(shareMixin)
  return { app }
}
