import { Alova } from '@/utils/http/alova/index';

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

const nativeMeta = {
  isReturnNativeResponse: true,
};

/**
 * @description: 获取用户信息
 */
export function getUserInfo() {
  return Alova.Get<AdminUserInfo>('/v1/admin/auth/me', {
    meta: nativeMeta,
  });
}

/**
 * @description: 用户登录
 */
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

/**
 * @description: 用户修改密码
 */
export function changePassword(params: AdminPasswordParams) {
  return updatePassword(params);
}

/**
 * @description: 用户登出
 */
export function logout(params) {
  return Alova.Post('/login/logout', {
    params,
  });
}
