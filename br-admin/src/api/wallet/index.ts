import { Alova } from '@/utils/http/alova/index';
import { useGlobSetting } from '@/hooks/setting';
import { ACCESS_TOKEN } from '@/store/mutation-types';
import { storage } from '@/utils/Storage';
import {
  ADMIN_NATIVE_META,
  normalizePageParams,
  toBasicTableResult,
  type AdminPageResponse,
} from '@/api/contracts/admin';

// ── 类型定义 ─────────────────────────────────────────────────────────────

/** 钱包交易流水项 */
export interface WalletTransactionItem {
  id: string | number;
  user_id: string | number;
  user_nickname: string | null;
  user_phone: string | null;
  type: string;
  amount: number;
  balance_after: number;
  status: string;
  payment_method: string | null;
  created_at: string;
  bonus_amount?: number;
  direction?: string;
  title?: string;
  order_id?: string | number | null;
  completed_at?: string | null;
}

/** 钱包统计数据 */
export interface WalletStatistics {
  total_recharge: number;
  total_consume: number;
  total_refund: number;
  net_income: number;
  active_users: number;
  total_transactions: number;
}

/** 钱包列表查询参数 */
export interface WalletListParams {
  page?: number;
  pageSize?: number;
  page_size?: number;
  type?: string;
  status?: string;
  user_id?: string | number;
  date_start?: string;
  date_end?: string;
}

/** 钱包交易列表响应 */
export interface WalletTransactionListResponse extends AdminPageResponse<WalletTransactionItem> {
  has_more?: boolean;
}

/** 分页适配结果（适配 BasicTable） */
export interface WalletListResult {
  list: WalletTransactionItem[];
  itemCount: number;
  pageCount: number;
  page: number;
}

// ── 配置 ─────────────────────────────────────────────────────────────────

function normalizeParams(params: WalletListParams = {}) {
  return normalizePageParams(params);
}

function buildQuery(params: WalletListParams = {}) {
  const query = new URLSearchParams();
  Object.entries(normalizeParams(params)).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, String(value));
    }
  });
  return query.toString();
}

function buildAdminApiUrl(path: string, params?: WalletListParams) {
  const { apiUrl, urlPrefix } = useGlobSetting();
  const query = buildQuery(params);
  return `${apiUrl || ''}${urlPrefix || ''}${path}${query ? `?${query}` : ''}`;
}

function normalizeExportParams(params: WalletListParams = {}) {
  const { page, pageSize, page_size, ...exportParams } = params;
  void page;
  void pageSize;
  void page_size;
  return exportParams;
}

function getExportFileName(response: Response) {
  const disposition = response.headers.get('Content-Disposition') || '';
  const filenameStar = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
  const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1];
  const rawName = filenameStar || filename;

  if (!rawName) {
    return `wallet_transactions_${new Date().toISOString().slice(0, 10)}.csv`;
  }

  try {
    return decodeURIComponent(rawName);
  } catch {
    return rawName;
  }
}

// ── API 函数 ─────────────────────────────────────────────────────────────

/**
 * 获取钱包交易列表
 * 适配 BasicTable 分页结构
 */
export async function getWalletList(params: WalletListParams = {}): Promise<WalletListResult> {
  const result = await Alova.Get<WalletTransactionListResponse>('/v1/admin/wallet/transactions', {
    params: normalizeParams(params),
    meta: ADMIN_NATIVE_META,
  });

  return toBasicTableResult(result);
}

/**
 * 获取钱包统计数据
 */
export async function getWalletStatistics(params?: WalletListParams): Promise<WalletStatistics> {
  return Alova.Get<WalletStatistics>('/v1/admin/wallet/statistics', {
    params: normalizeParams(params),
    meta: ADMIN_NATIVE_META,
  });
}

/**
 * 导出钱包交易记录
 * 返回 blob 并触发浏览器下载
 */
export async function exportWalletTransactions(params: WalletListParams = {}): Promise<Blob> {
  const headers: Record<string, string> = {};
  const token = storage.get(ACCESS_TOKEN, '');
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  } else if (import.meta.env.VITE_ADMIN_TOKEN) {
    headers['X-Admin-Token'] = import.meta.env.VITE_ADMIN_TOKEN;
  }

  const response = await fetch(
    buildAdminApiUrl('/v1/admin/wallet/transactions/export', normalizeExportParams(params)),
    {
      method: 'GET',
      headers,
    }
  );

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || response.statusText || '导出失败');
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = getExportFileName(response);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);

  return blob;
}
