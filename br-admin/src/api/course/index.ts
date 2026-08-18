import { Alova } from '@/utils/http/alova/index';
import { ADMIN_NATIVE_META } from '@/api/contracts/admin';

// --- Types ---

export interface CourseScheduleItem {
  id?: number | null;
  teacher_id?: number | null;
  start_date?: string | null;
  time_slots?: string | null;
  price: number;
  custom_price?: number;
  full_package_price?: number | null;
  full_custom_price?: number | null;
}

export interface CourseItem {
  id: number;
  name: string;
  cover_image: string | null;
  category: string;
  rating: number;
  enrollment_count: number;
  tags: string[];
  status: string;
  is_hot: boolean;
  sort_order: number;
  room_id: number;
  room_name?: string | null;
  schedules: CourseScheduleItem[];
  created_at: string;
  updated_at: string;
}

export interface CourseListResult {
  total: number;
  page: number;
  page_size: number;
  items: CourseItem[];
}

export interface CourseCreateParams {
  name: string;
  cover_image?: string | null;
  category: string;
  room_id: number;
  tags?: string | null;
  description?: string | null;
  is_hot?: boolean;
  sort_order?: number;
  status?: string;
  schedules?: CourseScheduleItem[];
}

export interface CourseUpdateParams {
  name?: string;
  cover_image?: string | null;
  category?: string;
  room_id?: number;
  tags?: string | null;
  description?: string | null;
  is_hot?: boolean;
  sort_order?: number;
  status?: string;
  schedules?: CourseScheduleItem[];
}

export interface TeacherBrief {
  id: number;
  name: string;
  avatar?: string | null;
  title?: string | null;
}

export interface CourseDetail extends CourseItem {
  teacher?: TeacherBrief | null;
  description?: string | null;
}

// --- API Functions ---

export function getCourseList(params?: {
  page?: number;
  page_size?: number;
  category?: string;
  status?: string;
  keyword?: string;
  teacher_id?: number;
}) {
  return Alova.Get<CourseListResult>('/v1/admin/courses', {
    params,
    meta: ADMIN_NATIVE_META,
  });
}

export function getCourseById(id: number) {
  return Alova.Get<CourseDetail>(`/v1/admin/courses/${id}`, {
    meta: ADMIN_NATIVE_META,
  });
}

export function createCourse(data: CourseCreateParams) {
  return Alova.Post<CourseDetail>('/v1/admin/courses', data, {
    meta: ADMIN_NATIVE_META,
  });
}

export function updateCourse(id: number, data: CourseUpdateParams) {
  return Alova.Put<CourseDetail>(`/v1/admin/courses/${id}`, data, {
    meta: ADMIN_NATIVE_META,
  });
}

export function deleteCourse(id: number) {
  return Alova.Delete(`/v1/admin/courses/${id}`, {
    meta: ADMIN_NATIVE_META,
  });
}

export function toggleCourseStatus(id: number, status: string) {
  return Alova.Patch<CourseDetail>(
    `/v1/admin/courses/${id}/status`,
    { status },
    {
      meta: ADMIN_NATIVE_META,
    }
  );
}
