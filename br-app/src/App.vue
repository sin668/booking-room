<script>
import { getRefreshToken, getToken } from '@/utils/request'
import { useUserStore } from '@/store/modules/user'
import { useCityStore } from '@/store/modules/city'
import { useThemeStore } from '@/store/modules/theme'
import { ensureIM } from '@/utils/im'

export default {
  onLaunch() {
    const cityStore = useCityStore()
    cityStore.initCity()

    const themeStore = useThemeStore()
    themeStore.init()

    const token = getToken()
    const refreshToken = getRefreshToken()
    if (token || refreshToken) {
      const userStore = useUserStore()
      userStore.autoLogin().then((ok) => {
        if (ok) ensureIM()
      })
    }
  },
  onShow() {
    useThemeStore().init()
  },
  onHide() {},
}
</script>

<style lang="scss">
@import '@/static/icons/iconfont.css';

page {
  --primary: #4f6ef7;
  --primary-light: #e8edff;
  --primary-soft: #f2f5ff;
  --orange-light: #fff3e0;
  --bg-color: #f5f6fa;
  --bg-warm: #f8faff;
  --bg-hero: #eef1fb;
  --surface: #ffffff;
  --surface-soft: #fafbff;
  --surface-muted: #f7f8fb;
  --text-primary: #2d3436;
  --text-secondary: #636e72;
  --text-muted: #b2bec3;
  --border-color: #e5e7eb;
  --border-soft: rgba(79, 110, 247, 0.08);
  --success: #07c160;
  --danger: #ff6b6b;

  background: linear-gradient(180deg, $bg-warm 0%, $bg-color 220rpx);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  color: $text-primary;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

/* 深色模式：主题类挂在各页面根节点，token 在页面子树内覆盖 */
.theme-dark {
  --primary: #7c93ff;
  --primary-light: rgba(79, 110, 247, 0.18);
  --primary-soft: rgba(79, 110, 247, 0.1);
  --orange-light: rgba(255, 140, 0, 0.14);
  --bg-color: #0f1115;
  --bg-warm: #12151b;
  --bg-hero: #161a23;
  --surface: #1a1d24;
  --surface-soft: #20242c;
  --surface-muted: #232830;
  --text-primary: #eceff4;
  --text-secondary: #a8b0bd;
  --text-muted: #6b7484;
  --border-color: #2a2f3a;
  --border-soft: rgba(124, 147, 255, 0.22);
  --success: #22c55e;
  --danger: #ff7b7b;

  background-color: var(--bg-color);
  color: var(--text-primary);
}

/* 底部导航文字加粗 */
.uni-tabbar__label {
  font-weight: 600 !important;
}
</style>
