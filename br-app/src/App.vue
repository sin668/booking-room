<script>
import { getRefreshToken, getToken } from '@/utils/request'
import { useUserStore } from '@/store/modules/user'
import { useCityStore } from '@/store/modules/city'

// 不需要登录的页面白名单
const WHITE_LIST = ['/pages/login/login']

export default {
  onLaunch() {
    const cityStore = useCityStore()
    cityStore.initCity()

    // 自动登录：检查本地 Token 并恢复用户状态
    const token = getToken()
    const refreshToken = getRefreshToken()
    if (token || refreshToken) {
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
