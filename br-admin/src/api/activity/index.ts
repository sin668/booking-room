import { Alova } from '@/utils/http/alova/index';
import { uploadImage, type UploadResult } from '@/api/upload';
import { ADMIN_NATIVE_META } from '@/api/contracts/admin';

// --- Types ---

export interface ActivityItem {
  id: number;
  title: string;
  description: string | null;
  content_html?: string | null;
  cover_image: string | null;
  participant_count: number;
  sort_order: number;
  is_active: boolean;
  activity_coupon_count?: number;
  activity_coupon_claimed_count?: number;
  activity_coupons?: ActivityCouponItem[];
  created_at: string;
  updated_at: string;
}

export interface ActivityListResult {
  total: number;
  page: number;
  page_size: number;
  items: ActivityItem[];
}

export interface ActivityFormParams {
  title: string;
  description?: string | null;
  content_html?: string | null;
  cover_image?: string | null;
  participant_count?: number;
  sort_order?: number;
  is_active?: boolean;
  activity_coupons?: ActivityCouponFormItem[];
}

export interface ActivityUpdateParams {
  title?: string;
  description?: string | null;
  content_html?: string | null;
  cover_image?: string | null;
  participant_count?: number;
  sort_order?: number;
  is_active?: boolean;
  activity_coupons?: ActivityCouponFormItem[];
}

export interface ActivityListParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  is_active?: boolean;
}

export interface ActivityCouponBase {
  coupon_id: number | null;
  total_quantity: number;
  claimed_quantity?: number;
  per_user_limit: number;
  claim_starts_at?: string | null;
  claim_ends_at?: string | null;
  is_active: boolean;
  sort_order: number;
  display_title?: string | null;
  display_description?: string | null;
}

export interface ActivityCouponTemplate {
  id: number;
  name: string;
  description?: string | null;
  type: string;
  discount_amount?: string | number | null;
  discount_percent?: number | null;
  min_order_amount?: string | number | null;
  scope?: string;
  seat_zone?: string | null;
  valid_from?: string | null;
  expires_at?: string | null;
  is_active?: boolean;
}

export interface ActivityCouponItem extends ActivityCouponBase {
  id: number;
  coupon?: ActivityCouponTemplate | null;
  remaining_quantity?: number;
  coupon_title?: string | null;
  coupon_type?: string | null;
  discount_rule?: string | null;
  valid_from?: string | null;
  expires_at?: string | null;
}

export interface ActivityCouponFormItem extends ActivityCouponBase {
  id?: number;
  coupon?: ActivityCouponTemplate | null;
  coupon_title?: string | null;
  coupon_type?: string | null;
  discount_rule?: string | null;
  valid_from?: string | null;
  expires_at?: string | null;
  _destroy?: boolean;
}

// --- Common meta for admin API calls ---

// --- API Functions ---

export function getActivityList(params?: ActivityListParams) {
  return Alova.Get<ActivityListResult>('/v1/admin/activities', {
    params,
    meta: ADMIN_NATIVE_META,
  });
}

export function createActivity(data: ActivityFormParams) {
  return Alova.Post<ActivityItem>('/v1/admin/activities', data, {
    meta: ADMIN_NATIVE_META,
  });
}

export function getActivityById(id: number) {
  return Alova.Get<ActivityItem>(`/v1/admin/activities/${id}`, {
    meta: ADMIN_NATIVE_META,
  });
}

export function updateActivity(id: number, data: ActivityUpdateParams) {
  return Alova.Put<ActivityItem>(`/v1/admin/activities/${id}`, data, {
    meta: ADMIN_NATIVE_META,
  });
}

export function deleteActivity(id: number) {
  return Alova.Delete(`/v1/admin/activities/${id}`, {
    meta: ADMIN_NATIVE_META,
  });
}

export function toggleActivityStatus(id: number, is_active: boolean) {
  return Alova.Patch<ActivityItem>(
    `/v1/admin/activities/${id}/status`,
    { is_active },
    {
      meta: ADMIN_NATIVE_META,
    }
  );
}

export function uploadFile(file: File) {
  return uploadImage(file, 'common');
}

export type { UploadResult };
