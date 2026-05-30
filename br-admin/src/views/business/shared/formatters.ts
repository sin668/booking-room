import type { BusinessTagConfig } from './options';

export function formatAdminMoney(value: number | string | null | undefined) {
  const amount = Number(value || 0);
  return `¥${amount.toFixed(2)}`;
}

export function formatAdminDate(value: number | string | null | undefined) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

export function formatAdminDateTime(value: string | null | undefined) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${formatAdminDate(date.getTime())} ${hours}:${minutes}`;
}

export function formatPaymentMethod(value: string | null | undefined) {
  if (!value) return '-';
  const map: Record<string, string> = {
    wechat: '微信',
    alipay: '支付宝',
    balance: '钱包余额',
  };
  return map[value] || value;
}

export function getTagConfig(
  configMap: Record<string, BusinessTagConfig>,
  value: string | number | boolean | null | undefined
): BusinessTagConfig {
  const key = String(value);
  return configMap[key] || { label: key, type: 'default' };
}
