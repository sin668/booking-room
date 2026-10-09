<script>
import { getRefreshToken, getToken } from '@/utils/request'
import { useUserStore } from '@/store/modules/user'
import { useCityStore } from '@/store/modules/city'
import { ensureIM } from '@/utils/im'

export default {
  onLaunch() {
    const cityStore = useCityStore()
    cityStore.initCity()

    const token = getToken()
    const refreshToken = getRefreshToken()
    if (token || refreshToken) {
      const userStore = useUserStore()
      userStore.autoLogin().then((ok) => {
        if (ok) ensureIM()
      })
    }
  },
  onShow() {},
  onHide() {},
}
</script>

<style lang="scss">
@import '@/static/icons/iconfont.css';

page {
  background: linear-gradient(180deg, $bg-warm 0%, $bg-color 220rpx);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  color: $text-primary;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

/* 底部导航文字加粗 */
.uni-tabbar__label {
  font-weight: 600 !important;
}
</style>
