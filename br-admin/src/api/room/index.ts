import { Alova } from '@/utils/http/alova/index';
import { ADMIN_NATIVE_META } from '@/api/contracts/admin';

// --- Types ---
export type RoomType = 'study' | 'training' | 'comprehensive';

export interface RoomItem {
  id: number;
  name: string;
  description: string | null;
  cover_image: string | null;
  environment_images: string[] | null;
  address: string;
  city_id: number | null;
  city_name: string | null;
  business_hours: string | null;
  status: 'open' | 'closed';
  room_type: RoomType;
  min_price: number;
  created_at: string;
  updated_at: string;
  seat_count: number;
  available_seat_count: number;
}

export interface RoomListResult {
  total: number;
  page: number;
  page_size: number;
  items: RoomItem[];
}

export interface RoomFormParams {
  name: string;
  address: string;
  description?: string | null;
  cover_image?: string | null;
  environment_images?: string[];
  business_hours?: string | null;
  city_id?: number | null;
  room_type?: RoomType;
  min_price?: number;
  status?: 'open' | 'closed';
}

export interface RoomUpdateParams {
  name?: string;
  address?: string;
  description?: string | null;
  cover_image?: string | null;
  environment_images?: string[];
  business_hours?: string | null;
  city_id?: number | null;
  room_type?: RoomType;
  min_price?: number;
  status?: 'open' | 'closed';
}

export interface RoomStatusParams {
  status: 'open' | 'closed';
}

export interface RoomListParams {
  page?: number;
  page_size?: number;
  status?: 'open' | 'closed';
  room_type?: RoomType;
  city_id?: number;
}

export interface CityItem {
  id: number;
  name: string;
  province: string;
}

// --- Common meta for admin API calls ---
// --- API Functions ---
export function getRoomList(params?: RoomListParams) {
  return Alova.Get<RoomListResult>('/v1/admin/rooms', { params, meta: ADMIN_NATIVE_META });
}
export function createRoom(data: RoomFormParams) {
  return Alova.Post<RoomItem>('/v1/admin/rooms', data, { meta: ADMIN_NATIVE_META });
}
export function getRoomById(id: number) {
  return Alova.Get<RoomItem>(`/v1/admin/rooms/${id}`, { meta: ADMIN_NATIVE_META });
}
export function updateRoom(id: number, data: RoomUpdateParams) {
  return Alova.Put<RoomItem>(`/v1/admin/rooms/${id}`, data, { meta: ADMIN_NATIVE_META });
}
export function deleteRoom(id: number) {
  return Alova.Delete(`/v1/admin/rooms/${id}`, { meta: ADMIN_NATIVE_META });
}
export function toggleRoomStatus(id: number, status: 'open' | 'closed') {
  return Alova.Patch<RoomItem>(
    `/v1/admin/rooms/${id}/status`,
    { status },
    { meta: ADMIN_NATIVE_META }
  );
}
export function getCityList() {
  return Alova.Get<CityItem[]>('/v1/cities', { meta: ADMIN_NATIVE_META });
}
