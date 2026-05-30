import { Alova } from '@/utils/http/alova/index';
import { uploadImage, type UploadResult } from '@/api/upload';
import { ADMIN_NATIVE_META } from '@/api/contracts/admin';

// --- Types ---

export interface ActivityItem {
  id: number;
  title: string;
  description: string | null;
  cover_image: string | null;
  participant_count: number;
  sort_order: number;
  is_active: boolean;
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
  cover_image?: string | null;
  participant_count?: number;
  sort_order?: number;
  is_active?: boolean;
}

export interface ActivityUpdateParams {
  title?: string;
  description?: string | null;
  cover_image?: string | null;
  participant_count?: number;
  sort_order?: number;
  is_active?: boolean;
}

export interface ActivityListParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  is_active?: boolean;
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
  return Alova.Patch<ActivityItem>(`/v1/admin/activities/${id}/status`, { is_active }, {
    meta: ADMIN_NATIVE_META,
  });
}

export function uploadFile(file: File) {
  return uploadImage(file, 'common');
}

export type { UploadResult };
