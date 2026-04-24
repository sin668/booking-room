import { Alova } from '@/utils/http/alova/index';

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

export interface UploadResult {
  url: string;
}

// --- Common meta for admin API calls ---

const adminMeta = {
  ignoreToken: true,
  isReturnNativeResponse: true,
};

/** Read admin token from env (never hardcode - BUG-5) */
function getAdminHeaders(): Record<string, string> {
  const token = import.meta.env.VITE_ADMIN_TOKEN;
  return token ? { 'X-Admin-Token': token } : {};
}

// --- API Functions ---

export function getActivityList(params?: ActivityListParams) {
  return Alova.Get<ActivityListResult>('/v1/admin/activities', {
    params,
    meta: adminMeta,
    headers: getAdminHeaders(),
  });
}

export function createActivity(data: ActivityFormParams) {
  return Alova.Post<ActivityItem>('/v1/admin/activities', data, {
    meta: adminMeta,
    headers: getAdminHeaders(),
  });
}

export function getActivityById(id: number) {
  return Alova.Get<ActivityItem>(`/v1/admin/activities/${id}`, {
    meta: adminMeta,
    headers: getAdminHeaders(),
  });
}

export function updateActivity(id: number, data: ActivityUpdateParams) {
  return Alova.Put<ActivityItem>(`/v1/admin/activities/${id}`, data, {
    meta: adminMeta,
    headers: getAdminHeaders(),
  });
}

export function deleteActivity(id: number) {
  return Alova.Delete(`/v1/admin/activities/${id}`, {
    meta: adminMeta,
    headers: getAdminHeaders(),
  });
}

export function toggleActivityStatus(id: number, is_active: boolean) {
  return Alova.Patch<ActivityItem>(`/v1/admin/activities/${id}/status`, { is_active }, {
    meta: adminMeta,
    headers: getAdminHeaders(),
  });
}

export function uploadFile(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return Alova.Post<UploadResult>('/v1/admin/upload', formData, {
    meta: adminMeta,
    headers: getAdminHeaders(),
  });
}
