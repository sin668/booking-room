import { Alova } from '@/utils/http/alova/index';

// --- Types ---
export interface SeatItem {
  id: number;
  room_id: number;
  seat_number: string;
  zone: 'quiet' | 'keyboard' | 'vip';
  position: string | null;
  floor: number;
  price_per_hour: number;
  status: 'available' | 'maintenance';
  row: number;
  col: number;
  created_at: string;
  updated_at: string;
  room_name: string;
}

export interface SeatFormParams {
  seat_number: string;
  zone: 'quiet' | 'keyboard' | 'vip';
  position?: string | null;
  floor?: number;
  price_per_hour: number;
  row: number;
  col: number;
}

export interface SeatBulkZoneConfig {
  zone: 'quiet' | 'keyboard' | 'vip';
  rows: number;
  cols: number;
  prefix: string;
  start_number?: number;
  price_per_hour: number;
  floor?: number;
}

export interface SeatBulkParams {
  seats: SeatBulkZoneConfig[];
}

export interface SeatBulkResult {
  created: number;
}

export interface SeatUpdateParams {
  seat_number?: string;
  zone?: 'quiet' | 'keyboard' | 'vip';
  position?: string | null;
  floor?: number;
  price_per_hour?: number;
  row?: number;
  col?: number;
}

export interface SeatStatusParams {
  status: 'available' | 'maintenance';
}

export interface SeatListParams {
  zone?: 'quiet' | 'keyboard' | 'vip';
  status?: 'available' | 'maintenance';
}

// --- Common meta for admin API calls ---
const adminMeta = {
  ignoreToken: true,
  isReturnNativeResponse: true,
};

/** Read admin token from env (never hardcode) */
function getAdminHeaders(): Record<string, string> {
  const token = import.meta.env.VITE_ADMIN_TOKEN;
  return token ? { 'X-Admin-Token': token } : {};
}

// --- API Functions ---
export function createSeat(roomId: number, data: SeatFormParams) {
  return Alova.Post<SeatItem>(`/v1/admin/rooms/${roomId}/seats`, data, { meta: adminMeta, headers: getAdminHeaders() });
}
export function bulkCreateSeats(roomId: number, data: SeatBulkParams) {
  return Alova.Post<SeatBulkResult>(`/v1/admin/rooms/${roomId}/seats/bulk`, data, { meta: adminMeta, headers: getAdminHeaders() });
}
export function getSeatList(roomId: number, params?: SeatListParams) {
  return Alova.Get<SeatItem[]>(`/v1/admin/rooms/${roomId}/seats`, { params, meta: adminMeta, headers: getAdminHeaders() });
}
export function getSeatById(seatId: number) {
  return Alova.Get<SeatItem>(`/v1/admin/seats/${seatId}`, { meta: adminMeta, headers: getAdminHeaders() });
}
export function updateSeat(seatId: number, data: SeatUpdateParams) {
  return Alova.Put<SeatItem>(`/v1/admin/seats/${seatId}`, data, { meta: adminMeta, headers: getAdminHeaders() });
}
export function deleteSeat(seatId: number) {
  return Alova.Delete(`/v1/admin/seats/${seatId}`, { meta: adminMeta, headers: getAdminHeaders() });
}
export function toggleSeatStatus(seatId: number, status: 'available' | 'maintenance') {
  return Alova.Patch<SeatItem>(`/v1/admin/seats/${seatId}/status`, { status }, { meta: adminMeta, headers: getAdminHeaders() });
}
