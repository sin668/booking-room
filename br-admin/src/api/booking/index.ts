import { Alova } from '@/utils/http/alova/index';
import { ADMIN_NATIVE_META } from '@/api/contracts/admin';

// --- Types ---

export interface BookingItem {
  id: number;
  user_id: string;
  user_nickname: string | null;
  room_id: number;
  seat_id: number | null;
  date: string;
  start_time: string;
  end_time: string;
  status: string;
  total_price: number;
  created_at: string;
  updated_at: string;
  booking_type?: string;
  schedule_type?: string | null;
  time_slots?: string | null;
  seat: {
    id: number;
    seat_number: string;
    zone: string;
    position: string | null;
    price_per_hour: number;
  };
  room: {
    id: number;
    name: string;
    address: string;
  };
}

// --- 详情聚合类型（对应后端 BookingAdminDetailResponse）---

export interface BookingDetailUser {
  id: string;
  nickname: string | null;
  phone: string | null;
  avatar: string | null;
}

export interface BookingDetailCourse {
  id: number;
  name: string;
  category: string;
}

export interface BookingDetailTeacher {
  id: number;
  name: string;
  avatar: string | null;
}

export interface BookingDetailSchedule {
  id: number;
  start_date: string | null;
  end_date: string | null;
  schedule_type: string;
  schedule_status: string;
  time_slots: string | null;
}

export interface BookingDetailLessonSchedule {
  id: number;
  lesson_id: number;
  lesson_title: string | null;
  lesson_date: string | null;
  lesson_time_slot: string;
  sort_order: number;
}

export interface BookingDetailCoupon {
  user_coupon_id: number;
  coupon_id: number;
  name: string | null;
  type: string | null;
  discount_amount: number | null;
  discount_percent: number | null;
}

export interface BookingDetailRefundTransaction {
  id: string;
  amount: number;
  balance_after: number | null;
  payment_method: string | null;
  created_at: string | null;
}

export interface BookingDetail extends BookingItem {
  original_price?: number;
  discount_amount?: number;
  coupon_id?: number | null;
  payment_method?: string;
  payment_status?: string;
  payment_provider?: string | null;
  paid_at?: string | null;
  cancelled_at?: string | null;
  penalty_amount?: number;
  refund_amount?: number;
  cancel_policy?: string | null;
  lesson_ids?: number[] | null;
  highlighted_lesson_id?: number | null;
  schedule_id?: number | null;
  teacher_id?: number | null;
  prepay_id?: string | null;
  transaction_id?: string | null;
  payment_check_count?: number;
  user?: BookingDetailUser | null;
  course?: BookingDetailCourse | null;
  teacher?: BookingDetailTeacher | null;
  schedule?: BookingDetailSchedule | null;
  lesson_schedules?: BookingDetailLessonSchedule[];
  coupon?: BookingDetailCoupon | null;
  refund_transaction?: BookingDetailRefundTransaction | null;
}

export interface BookingListResult {
  total: number;
  page: number;
  page_size: number;
  items: BookingItem[];
}

export interface BookingListParams {
  page?: number;
  page_size?: number;
  status?: string;
  room_id?: number;
  date_start?: string;
  date_end?: string;
}

// --- Common meta for admin API calls ---

// --- API Functions ---

export function getBookingList(params?: BookingListParams) {
  return Alova.Get<BookingListResult>('/v1/admin/bookings', {
    params,
    meta: ADMIN_NATIVE_META,
  });
}

export function getBookingDetail(id: number) {
  return Alova.Get<BookingDetail>(`/v1/admin/bookings/${id}`, {
    meta: ADMIN_NATIVE_META,
  });
}

export function cancelBooking(id: number) {
  return Alova.Post<BookingDetail>(`/v1/admin/bookings/${id}/cancel`, undefined, {
    meta: ADMIN_NATIVE_META,
  });
}

export function confirmBooking(id: number) {
  return Alova.Post<BookingItem>(`/v1/admin/bookings/${id}/confirm`, undefined, {
    meta: ADMIN_NATIVE_META,
  });
}
