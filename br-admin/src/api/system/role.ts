import { Alova } from '@/utils/http/alova/index';
import { normalizeMenuTree, type MenuItem } from './menu';

export interface RoleItem {
  id: string | number;
  name: string;
  code: string;
  description?: string;
  status?: 'active' | 'disabled';
  is_default?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface RoleListParams {
  page?: number;
  pageSize?: number;
  page_size?: number;
  name?: string;
  code?: string;
}

export interface RoleListResponse {
  items: RoleItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface RoleSaveParams {
  name: string;
  code: string;
  description?: string;
  status?: 'active' | 'disabled';
}

export interface RoleMenusResponse {
  menus: MenuItem[];
  checked_menu_ids: Array<string | number>;
}

const nativeMeta = {
  isReturnNativeResponse: true,
};

/**
 * @description: 角色列表，适配 BasicTable 分页结构
 */
export async function getRoleList(params: RoleListParams = {}) {
  const page_size = params.page_size || params.pageSize;
  const keyword = params.name || params.code;
  const result = await Alova.Get<RoleListResponse>('/v1/admin/roles', {
    params: {
      ...params,
      keyword,
      name: undefined,
      code: undefined,
      page_size,
      pageSize: undefined,
    },
    meta: nativeMeta,
  });

  return {
    list: result.items,
    itemCount: result.total,
    pageCount: Math.ceil(result.total / result.page_size) || 1,
    page: result.page,
  };
}

export function createRole(data: RoleSaveParams) {
  return Alova.Post<RoleItem>('/v1/admin/roles', data, {
    meta: nativeMeta,
  });
}

export function updateRole(id: string | number, data: Partial<RoleSaveParams>) {
  return Alova.Put<RoleItem>(`/v1/admin/roles/${id}`, data, {
    meta: nativeMeta,
  });
}

export function deleteRole(id: string | number) {
  return Alova.Delete(`/v1/admin/roles/${id}`, {
    meta: nativeMeta,
  });
}

export async function getRoleMenus(id: string | number) {
  const result = await Alova.Get<RoleMenusResponse>(`/v1/admin/roles/${id}/menus`, {
    meta: nativeMeta,
  });
  return {
    tree: normalizeMenuTree(result.menus),
    checkedKeys: result.checked_menu_ids,
  };
}

export function updateRoleMenus(id: string | number, menu_ids: Array<string | number>) {
  return Alova.Put(
    `/v1/admin/roles/${id}/menus`,
    { menu_ids },
    {
      meta: nativeMeta,
    }
  );
}
