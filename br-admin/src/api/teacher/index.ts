import { Alova } from '@/utils/http/alova/index';
import { ADMIN_NATIVE_META } from '@/api/contracts/admin';

// --- Types ---

export interface QualificationItem {
  name: string;
  sub?: string | null;
}

export interface TeacherRoomBrief {
  id: number;
  name: string;
  room_type: string;
}

export interface AdminTeacherItem {
  id: number;
  name: string;
  avatar?: string | null;
  title?: string | null;
  specialty?: string | null;
  teaching_years: number;
  education?: string | null;
  school?: string | null;
  rating: number;
  student_count: number;
  course_count: number;
  status: string;
  created_at: string;
}

export interface AdminTeacherListResult {
  items: AdminTeacherItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AdminTeacherDetail extends AdminTeacherItem {
  bio?: string | null;
  teaching_tags: string[];
  qualifications: QualificationItem[];
  room_ids: number[];
  rooms: TeacherRoomBrief[];
  updated_at: string;
}

export interface AdminTeacherCreateParams {
  name: string;
  avatar?: string | null;
  title?: string | null;
  specialty?: string | null;
  teaching_years?: number;
  education?: string | null;
  school?: string | null;
  bio?: string | null;
  teaching_tags?: string[];
  qualifications?: QualificationItem[];
  room_ids?: number[];
  status?: 'active' | 'inactive';
}

export type AdminTeacherUpdateParams = Partial<AdminTeacherCreateParams>;

// --- API Functions ---

export function getAdminTeacherList(params?: {
  page?: number;
  page_size?: number;
  keyword?: string;
  status?: string;
}) {
  return Alova.Get<AdminTeacherListResult>('/v1/admin/teachers', {
    params,
    meta: ADMIN_NATIVE_META,
    // 强制绕过 Alova GET 默认内存缓存，保证增删改后列表数据最新
    force: true,
  });
}

export function getAdminTeacherById(id: number) {
  return Alova.Get<AdminTeacherDetail>(`/v1/admin/teachers/${id}`, {
    meta: ADMIN_NATIVE_META,
    force: true,
  });
}

export function createAdminTeacher(data: AdminTeacherCreateParams) {
  return Alova.Post<AdminTeacherDetail>('/v1/admin/teachers', data, {
    meta: ADMIN_NATIVE_META,
  });
}

export function updateAdminTeacher(id: number, data: AdminTeacherUpdateParams) {
  return Alova.Put<AdminTeacherDetail>(`/v1/admin/teachers/${id}`, data, {
    meta: ADMIN_NATIVE_META,
  });
}

export function deleteAdminTeacher(id: number) {
  return Alova.Delete(`/v1/admin/teachers/${id}`, {
    meta: ADMIN_NATIVE_META,
  });
}

export function toggleAdminTeacherStatus(id: number, status: string) {
  return Alova.Patch<AdminTeacherDetail>(
    `/v1/admin/teachers/${id}/status`,
    { status },
    {
      meta: ADMIN_NATIVE_META,
    }
  );
}

export function getTeacherAvailableTimeSlots(teacherId: number) {
  return Alova.Get<{ available_time_slots: any[] }>(
    `/v1/admin/teachers/${teacherId}/available-time-slots`,
    {
      meta: ADMIN_NATIVE_META,
      force: true,
    }
  );
}

export function updateTeacherAvailableTimeSlots(teacherId: number, data: { available_time_slots: any[] | null }) {
  return Alova.Put(
    `/v1/admin/teachers/${teacherId}/available-time-slots`,
    data,
    {
      meta: ADMIN_NATIVE_META,
    }
  );
}
