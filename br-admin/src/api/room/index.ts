import { Alova } from '@/utils/http/alova/index';

// --- Types ---
export interface RoomItem {
  id: number;
  name: string;
  description: string | null;
  cover_image: string | null;
  address: string;
  business_hours: string | null;
  status: 'open' | 'closed';
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
  business_hours?: string | null;
  min_price?: number;
}

export interface RoomUpdateParams {
  name?: string;
  address?: string;
  description?: string | null;
  cover_image?: string | null;
  business_hours?: string | null;
  min_price?: number;
}

export interface RoomStatusParams {
  status: 'open' | 'closed';
}

export interface RoomListParams {
  page?: number;
  page_size?: number;
  status?: 'open' | 'closed';
}

// --- Common meta for admin API calls ---
const adminMeta = {
  isReturnNativeResponse: true,
};

// --- API Functions ---
export function getRoomList(params?: RoomListParams) {
  return Alova.Get<RoomListResult>('/v1/admin/rooms', { params, meta: adminMeta });
}
export function createRoom(data: RoomFormParams) {
  return Alova.Post<RoomItem>('/v1/admin/rooms', data, { meta: adminMeta });
}
export function getRoomById(id: number) {
  return Alova.Get<RoomItem>(`/v1/admin/rooms/${id}`, { meta: adminMeta });
}
export function updateRoom(id: number, data: RoomUpdateParams) {
  return Alova.Put<RoomItem>(`/v1/admin/rooms/${id}`, data, { meta: adminMeta });
}
export function deleteRoom(id: number) {
  return Alova.Delete(`/v1/admin/rooms/${id}`, { meta: adminMeta });
}
export function toggleRoomStatus(id: number, status: 'open' | 'closed') {
  return Alova.Patch<RoomItem>(`/v1/admin/rooms/${id}/status`, { status }, { meta: adminMeta });
}
