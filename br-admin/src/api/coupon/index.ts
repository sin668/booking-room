import { Alova } from '@/utils/http/alova/index';
import { ADMIN_NATIVE_META, normalizePageParams } from '@/api/contracts/admin';

export interface AdminCouponItem {
  id: number;
  name: string;
  description: string | null;
  type: string;
  discount_amount: string | number | null;
  discount_percent: number | null;
  min_order_amount: string | number;
  scope: string;
  seat_zone: string | null;
  valid_from: string;
  expires_at: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminCouponListResult {
  total: number;
  page: number;
  page_size: number;
  items: AdminCouponItem[];
}

export interface AdminCouponCreateParams {
  name: string;
  description?: string | null;
  type: string;
  discount_amount?: number | null;
  discount_percent?: number | null;
  min_order_amount?: number;
  scope?: string;
  seat_zone?: string | null;
  valid_from: string;
  expires_at: string;
  is_active?: boolean;
}

export type AdminCouponUpdateParams = Partial<AdminCouponCreateParams>;

export interface AdminCouponListParams {
  page?: number;
  pageSize?: number;
  page_size?: number;
  keyword?: string;
  type?: string;
  scope?: string;
  is_active?: boolean;
  valid_now?: boolean;
}

export function getCouponList(params?: AdminCouponListParams) {
  return Alova.Get<AdminCouponListResult>('/v1/admin/coupons', {
    params: normalizePageParams(params || {}),
    meta: ADMIN_NATIVE_META,
  });
}

export function getCouponById(id: number) {
  return Alova.Get<AdminCouponItem>(`/v1/admin/coupons/${id}`, { meta: ADMIN_NATIVE_META });
}

export function createCoupon(data: AdminCouponCreateParams) {
  return Alova.Post<AdminCouponItem>('/v1/admin/coupons', data, { meta: ADMIN_NATIVE_META });
}

export function updateCoupon(id: number, data: AdminCouponUpdateParams) {
  return Alova.Put<AdminCouponItem>(`/v1/admin/coupons/${id}`, data, { meta: ADMIN_NATIVE_META });
}

export function toggleCouponStatus(id: number, is_active: boolean) {
  return Alova.Patch<AdminCouponItem>(
    `/v1/admin/coupons/${id}/status`,
    { is_active },
    { meta: ADMIN_NATIVE_META }
  );
}

export function deleteCoupon(id: number) {
  return Alova.Delete(`/v1/admin/coupons/${id}`, { meta: ADMIN_NATIVE_META });
}
