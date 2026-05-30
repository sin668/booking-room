import { Alova } from '@/utils/http/alova/index';
import {
  ADMIN_NATIVE_META,
  normalizePageParams,
  toBasicTableResult,
  type AdminPageResponse,
} from '@/api/contracts/admin';

export interface AdminLoginParams {
  username: string;
  password: string;
}

export interface AdminLoginResult {
  access_token: string;
  token_type?: string;
}

export interface AdminPermission {
  label: string;
  value: string;
}

export interface AdminRoleSummary {
  id: string | number;
  name: string;
  code: string;
}

export interface AdminUserInfo {
  id?: string | number;
  username: string;
  nickname?: string;
  email?: string;
  mobile?: string;
  avatar?: string;
  roles?: AdminRoleSummary[];
  permissions?: AdminPermission[];
}

export interface AdminProfileParams {
  nickname?: string;
  email?: string;
  mobile?: string;
  avatar?: string;
}

export interface AdminPasswordParams {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export interface UserListItem {
  id: string;
  phone: string;
  nickname: string | null;
  user_type: string;
  status: string;
  avatar: string | null;
  created_at: string;
  roles: AdminRoleSummary[];
  booking_count: number;
  coupon_count: number;
}

export interface UserDetail extends UserListItem {
  username: string | null;
  email: string | null;
  mobile: string | null;
  balance: number;
  is_super_admin: boolean;
  wechat_openid: string | null;
  invite_code: string | null;
  updated_at: string | null;
}

export interface UserListParams {
  user_type?: string;
  keyword?: string;
  status?: string;
  page?: number;
  pageSize?: number;
  page_size?: number;
}

export type UserListResponse = AdminPageResponse<UserListItem>;

export interface UserCreateParams {
  user_type: string;
  phone?: string;
  username?: string;
  password: string;
  nickname?: string;
}

export interface UserUpdateParams {
  nickname?: string;
  email?: string;
  mobile?: string;
  avatar?: string;
  balance?: number;
  role_ids?: number[];
}

const nativeMeta = ADMIN_NATIVE_META;

// ── Auth APIs (existing) ──────────────────────────────────────────────

/** @description: 获取用户信息 */
export function getUserInfo() {
  return Alova.Get<AdminUserInfo>('/v1/admin/auth/me', {
    meta: nativeMeta,
  });
}

/** @description: 用户登录 */
export function login(params: AdminLoginParams) {
  return Alova.Post<AdminLoginResult>('/v1/admin/auth/login', params, {
    meta: {
      ...nativeMeta,
      ignoreToken: true,
    },
  });
}

export function updateProfile(params: AdminProfileParams) {
  return Alova.Put<AdminUserInfo>('/v1/admin/auth/profile', params, {
    meta: nativeMeta,
  });
}

export function updatePassword(params: AdminPasswordParams) {
  return Alova.Put('/v1/admin/auth/password', params, {
    meta: nativeMeta,
  });
}

/** @description: 用户修改密码 */
export function changePassword(params: AdminPasswordParams) {
  return updatePassword(params);
}

/** @description: 用户登出 */
export function logout(params) {
  return Alova.Post('/login/logout', {
    params,
  });
}

// ── User Management APIs (new) ────────────────────────────────────────

/** @description: 用户列表，适配 BasicTable 分页结构 */
export async function getUserList(params: UserListParams = {}) {
  const result = await Alova.Get<UserListResponse>('/v1/admin/users', {
    params: normalizePageParams(params),
    meta: nativeMeta,
  });

  return toBasicTableResult(result);
}

/** @description: 用户详情 */
export function getUserDetail(id: string | number) {
  return Alova.Get<UserDetail>(`/v1/admin/users/${id}`, {
    meta: nativeMeta,
  });
}

/** @description: 创建用户 */
export function createUser(data: UserCreateParams) {
  return Alova.Post<UserListItem>('/v1/admin/users', data, {
    meta: nativeMeta,
  });
}

/** @description: 更新用户 */
export function updateUser(id: string | number, data: UserUpdateParams) {
  return Alova.Put<UserListItem>(`/v1/admin/users/${id}`, data, {
    meta: nativeMeta,
  });
}

/** @description: 删除用户 */
export function deleteUser(id: string | number) {
  return Alova.Delete(`/v1/admin/users/${id}`, {
    meta: nativeMeta,
  });
}

/** @description: 重置用户密码 */
export function resetUserPassword(id: string | number, new_password: string) {
  return Alova.Put(`/v1/admin/users/${id}/reset-password`, { new_password }, {
    meta: nativeMeta,
  });
}

/** @description: 切换用户状态 */
export function toggleUserStatus(id: string | number, target_status: string) {
  return Alova.Put(`/v1/admin/users/${id}/status`, { target_status }, {
    meta: nativeMeta,
  });
}
