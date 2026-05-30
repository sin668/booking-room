import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import type { PluginOption } from 'vite';
import type { ViteEnv } from '../../utils';

export function createVitePlugins(_viteEnv: ViteEnv, _isBuild: boolean): PluginOption[] {
  return [vue(), vueJsx()];
}
