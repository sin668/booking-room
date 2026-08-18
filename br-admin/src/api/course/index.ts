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
  lessons?: LessonItem[];
}

export interface LessonItem {
  id: number;
  title: string;
  description?: string | null;
  duration_minutes?: number | null;
  sort_order: number;
  is_free_preview: boolean;
}

export interface LessonCreateParams {
  title: string;
  description?: string | null;
  duration_minutes?: number | null;
  sort_order?: number;
  is_free_preview?: boolean;
}

export interface LessonUpdateParams {
  title?: string;
  description?: string | null;
  duration_minutes?: number | null;
  sort_order?: number;
  is_free_preview?: boolean;
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
    // 强制绕过 Alova GET 默认内存缓存，保证增删改后列表数据最新
    force: true,
  });
}

export function getCourseById(id: number) {
  return Alova.Get<CourseDetail>(`/v1/admin/courses/${id}`, {
    meta: ADMIN_NATIVE_META,
    force: true,
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

// --- Lesson API Functions ---

export function getCourseLessons(courseId: number) {
  return Alova.Get<LessonItem[]>(`/v1/admin/courses/${courseId}/lessons`, {
    meta: ADMIN_NATIVE_META,
    force: true,
  });
}

export function createLesson(courseId: number, data: LessonCreateParams) {
  return Alova.Post<LessonItem>(`/v1/admin/courses/${courseId}/lessons`, data, {
    meta: ADMIN_NATIVE_META,
  });
}

export function updateLesson(courseId: number, lessonId: number, data: LessonUpdateParams) {
  return Alova.Put<LessonItem>(`/v1/admin/courses/${courseId}/lessons/${lessonId}`, data, {
    meta: ADMIN_NATIVE_META,
  });
}

export function deleteLesson(courseId: number, lessonId: number) {
  return Alova.Delete(`/v1/admin/courses/${courseId}/lessons/${lessonId}`, {
    meta: ADMIN_NATIVE_META,
  });
}

// --- Teacher API Functions ---

export interface TeacherItem {
  id: number;
  name: string;
  avatar?: string | null;
  title?: string | null;
}

export interface TeacherListResult {
  items: TeacherItem[];
  total: number;
}

export function getTeacherList(params?: { keyword?: string }) {
  return Alova.Get<TeacherListResult>('/v1/admin/teachers', {
    params,
    meta: ADMIN_NATIVE_META,
  });
}

// --- Schedule API Functions ---

export interface ScheduleRecord {
  id: number;
  course_id: number;
  teacher_id?: number | null;
  start_date?: string | null;
  time_slots?: string | null;
  price: number;
  custom_price: number;
  full_package_price?: number | null;
  full_custom_price?: number | null;
}

export interface ScheduleCreateParams {
  teacher_id?: number | null;
  start_date?: string | null;
  time_slots?: string | null;
  price?: number;
  custom_price?: number;
  full_package_price?: number | null;
  full_custom_price?: number | null;
}

export type ScheduleUpdateParams = ScheduleCreateParams;

export function getCourseSchedules(courseId: number) {
  return Alova.Get<ScheduleRecord[]>(`/v1/admin/courses/${courseId}/schedules`, {
    meta: ADMIN_NATIVE_META,
    // 强制绕过 Alova GET 默认内存缓存，保证增删改后列表数据最新
    force: true,
  });
}

export function createCourseSchedule(courseId: number, data: ScheduleCreateParams) {
  return Alova.Post<ScheduleRecord>(`/v1/admin/courses/${courseId}/schedules`, data, {
    meta: ADMIN_NATIVE_META,
  });
}

export function updateCourseSchedule(courseId: number, scheduleId: number, data: ScheduleUpdateParams) {
  return Alova.Put<ScheduleRecord>(`/v1/admin/courses/${courseId}/schedules/${scheduleId}`, data, {
    meta: ADMIN_NATIVE_META,
  });
}

export function deleteCourseSchedule(courseId: number, scheduleId: number) {
  return Alova.Delete(`/v1/admin/courses/${courseId}/schedules/${scheduleId}`, {
    meta: ADMIN_NATIVE_META,
  });
}
