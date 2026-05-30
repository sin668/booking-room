export interface ViteEnv {
  VITE_PUBLIC_PATH: string;
  VITE_PORT: number;
  VITE_PROXY: [string, string][];
  [key: string]: string | number | boolean | [string, string][];
}

function parseProxy(value: string | undefined): [string, string][] {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value.replace(/'/g, '"'));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function parseValue(value: string): string | number | boolean {
  if (value === 'true') return true;
  if (value === 'false') return false;
  if (/^\d+$/.test(value)) return Number(value);
  return value;
}

export function wrapperEnv(envConf: Record<string, string>): ViteEnv {
  const env = Object.entries(envConf).reduce<Record<string, string | number | boolean>>(
    (result, [key, value]) => {
      result[key] = parseValue(value);
      return result;
    },
    {}
  );

  return {
    ...env,
    VITE_PUBLIC_PATH: String(env.VITE_PUBLIC_PATH || '/'),
    VITE_PORT: Number(env.VITE_PORT || 3100),
    VITE_PROXY: parseProxy(envConf.VITE_PROXY),
  };
}
