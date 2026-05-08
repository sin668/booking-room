import { Alova } from '@/utils/http/alova/index';

// --- Types ---

export interface BookingItem {
  id: number;
  user_id: string;
  room_id: number;
  seat_id: number;
  date: string;
  start_time: string;
  end_time: string;
  status: string;
  total_price: number;
  created_at: string;
  updated_at: string;
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

const adminMeta = {
  ignoreToken: true,
  isReturnNativeResponse: true,
};

function getAdminHeaders(): Record<string, string> {
  const token = import.meta.env.VITE_ADMIN_TOKEN;
  return token ? { 'X-Admin-Token': token } : {};
}

// --- API Functions ---

export function getBookingList(params?: BookingListParams) {
  return Alova.Get<BookingListResult>('/v1/admin/bookings', {
    params,
    meta: adminMeta,
    headers: getAdminHeaders(),
  });
}

export function getBookingDetail(id: number) {
  return Alova.Get<BookingItem>(`/v1/admin/bookings/${id}`, {
    meta: adminMeta,
    headers: getAdminHeaders(),
  });
}

export function cancelBooking(id: number) {
  return Alova.Post<BookingItem>(`/v1/admin/bookings/${id}/cancel`, undefined, {
    meta: adminMeta,
    headers: getAdminHeaders(),
  });
}
