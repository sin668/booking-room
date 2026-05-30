export function getConfigFileName(env: Record<string, unknown>) {
  return `__PRODUCTION__${env.VITE_GLOB_APP_SHORT_NAME || 'APP'}__CONF__`;
}
