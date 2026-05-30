import type { ProxyOptions } from 'vite';

export function createProxy(proxyList: [string, string][] = []) {
  return proxyList.reduce<Record<string, string | ProxyOptions>>((proxy, [prefix, target]) => {
    proxy[prefix] = {
      target,
      changeOrigin: true,
      rewrite: (path) => path.replace(new RegExp(`^${prefix}`), ''),
    };
    return proxy;
  }, {});
}
