import { useThemeStore } from '@/store/modules/theme'

export default {
  computed: {
    themeClass() {
      return useThemeStore().themeClass
    },
  },
  onMounted() {
    // setNavigationBarColor 只作用于当前页面，新开页面需重新应用
    useThemeStore().init()
  },
}
