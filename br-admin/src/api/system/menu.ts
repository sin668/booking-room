import { Alova } from '@/utils/http/alova/index';

export type MenuType = 'directory' | 'menu' | 'button';

export interface MenuMeta {
  title: string;
  icon?: string;
  permissions?: string[];
  hidden?: boolean;
  keepAlive?: boolean;
}

export interface MenuRoute {
  path: string;
  name?: string;
  component?: string;
  redirect?: string;
  meta: MenuMeta;
  children?: MenuRoute[];
}

export interface MenuItem {
  id: string | number;
  parent_id?: string | number | null;
  type: MenuType;
  title: string;
  permission_code?: string | null;
  path?: string | null;
  name?: string | null;
  component?: string | null;
  redirect?: string | null;
  icon?: string | null;
  sort?: number;
  hidden?: boolean;
  keep_alive?: boolean;
  enabled?: boolean;
  children?: MenuItem[];
}

export interface MenuTreeNode extends MenuItem {
  key: string | number;
  label: string;
  disabled?: boolean;
  children?: MenuTreeNode[];
}

export interface ComponentOption {
  label: string;
  value: string;
}

export type MenuSaveParams = Partial<Omit<MenuItem, 'id' | 'children'>> & {
  title: string;
  type: MenuType;
};

const nativeMeta = {
  isReturnNativeResponse: true,
};

export function normalizeMenuTree(items: MenuItem[] = []): MenuTreeNode[] {
  return items.map((item) => ({
    ...item,
    key: item.id,
    label: item.title,
    children: normalizeMenuTree(item.children || []),
  }));
}

/**
 * @description: 根据用户权限获取后端动态路由
 */
export function adminMenus() {
  return Alova.Get<MenuRoute[]>('/v1/admin/menus/routes', {
    meta: nativeMeta,
  });
}

/**
 * 获取完整菜单权限树
 */
export async function getMenuList(params?) {
  const list = await Alova.Get<MenuItem[]>('/v1/admin/menus', {
    params,
    meta: nativeMeta,
  });
  return {
    list: normalizeMenuTree(list),
    raw: list,
  };
}

export function createMenu(data: MenuSaveParams) {
  return Alova.Post<MenuItem>('/v1/admin/menus', data, {
    meta: nativeMeta,
  });
}

export function updateMenu(id: string | number, data: Partial<MenuSaveParams>) {
  return Alova.Put<MenuItem>(`/v1/admin/menus/${id}`, data, {
    meta: nativeMeta,
  });
}

export function deleteMenu(id: string | number) {
  return Alova.Delete(`/v1/admin/menus/${id}`, {
    meta: nativeMeta,
  });
}

export function getComponentOptions() {
  return Alova.Get<ComponentOption[]>('/v1/admin/menus/component-options', {
    meta: nativeMeta,
  });
}
