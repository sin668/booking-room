import { RouteRecordRaw } from 'vue-router';
import { Layout } from '@/router/constant';
import { OptionsSharp } from '@vicons/ionicons5';
import { renderIcon } from '@/utils/index';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/system',
    name: 'System',
    redirect: '/system/menu',
    component: Layout,
    meta: {
      title: '系统设置',
      icon: renderIcon(OptionsSharp),
      sort: 1,
    },
    children: [
      {
        path: 'menu',
        name: 'system_menu',
        meta: {
          title: '菜单权限',
        },
        component: () => import('@/views/system/menu/menu.vue'),
      },
      {
        path: 'role',
        name: 'system_role',
        meta: {
          title: '角色权限',
        },
        component: () => import('@/views/system/role/role.vue'),
      },
      {
        path: 'role/edit/:id?',
        name: 'system_role_edit',
        meta: {
          title: '编辑角色',
          hideInMenu: true,
          activeMenu: 'system_role',
        },
        component: () => import('@/views/system/role/edit.vue'),
      },
      {
        path: 'user',
        name: 'system_user',
        meta: {
          title: '用户管理',
        },
        component: () => import('@/views/system/user/index.vue'),
      },
      {
        path: 'user/edit/:id?',
        name: 'system_user_edit',
        meta: {
          title: '编辑用户',
          hideInMenu: true,
          activeMenu: 'system_user',
        },
        component: () => import('@/views/system/user/edit.vue'),
      },
    ],
  },
];

export default routes;
