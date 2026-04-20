<script>
import { getToken } from '@/utils/request'
import { useUserStore } from '@/store/modules/user'

// 不需要登录的页面白名单
const WHITE_LIST = ['/pages/login/login']

export default {
  onLaunch() {
    // 自动登录：检查本地 Token 并恢复用户状态
    const token = getToken()
    if (token) {
      const userStore = useUserStore()
      userStore.autoLogin()
    }
  },

  onShow() {},

  onHide() {},
}
</script>

<style lang="scss">
@import '@/static/icons/iconfont.css';

page {
  background-color: $bg-color;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  color: $text-primary;
  -webkit-font-smoothing: antialiased;
}
</style>
