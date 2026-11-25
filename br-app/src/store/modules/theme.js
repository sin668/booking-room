import { defineStore } from 'pinia'

const THEME_STORAGE_KEY = 'theme_mode'

function readStoredTheme() {
  try {
    return uni.getStorageSync(THEME_STORAGE_KEY) === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

function applyNativeTheme(isDark) {
  const front = isDark ? '#ffffff' : '#000000'
  const background = isDark ? '#0F1115' : '#F5F6FA'
  try {
    uni.setNavigationBarColor({ frontColor: front, backgroundColor: background })
  } catch {
    // 部分页面使用自定义导航栏，原生接口失败不影响主题
  }
  try {
    uni.setBackgroundColor?.({
      backgroundColor: background,
      backgroundColorTop: background,
      backgroundColorBottom: background,
    })
  } catch {
    // H5 不支持窗口背景色
  }
  try {
    uni.setTabBarStyle?.({
      color: isDark ? '#8A93A3' : '#B2BEC3',
      selectedColor: isDark ? '#8FA6FF' : '#4F6EF7',
      backgroundColor: isDark ? '#1A1D24' : '#ffffff',
      borderStyle: isDark ? 'black' : 'white',
    })
  } catch {
    // 非 tabBar 页面或平台不支持时忽略
  }
}

export const useThemeStore = defineStore('theme', {
  state: () => ({
    mode: readStoredTheme(),
  }),

  getters: {
    isDark: (state) => state.mode === 'dark',
    themeClass: (state) => (state.mode === 'dark' ? 'theme-dark' : ''),
  },

  actions: {
    setMode(mode) {
      this.mode = mode === 'dark' ? 'dark' : 'light'
      try {
        uni.setStorageSync(THEME_STORAGE_KEY, this.mode)
      } catch {
        // 存储失败时本次会话内仍然生效
      }
      applyNativeTheme(this.isDark)
    },
    toggle() {
      this.setMode(this.isDark ? 'light' : 'dark')
    },
    init() {
      applyNativeTheme(this.isDark)
    },
  },
})
