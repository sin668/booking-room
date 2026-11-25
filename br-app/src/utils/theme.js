import { useThemeStore } from '@/store/modules/theme'

export default {
  computed: {
    themeClass() {
      return useThemeStore().themeClass
    },
  },
}
