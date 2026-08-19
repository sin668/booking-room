import { RouteRecordRaw } from 'vue-router';
import { Layout } from '@/router/constant';
import { CalendarOutline } from '@vicons/ionicons5';
import { renderIcon } from '@/utils/index';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/activity',
    name: 'Activity',
    redirect: '/activity/list',
    component: Layout,
    meta: {
      title: '活动管理',
      icon: renderIcon(CalendarOutline),
      sort: 2,
    },
    children: [
      {
        path: 'list',
        name: 'activity_list',
        meta: {
          title: '活动列表',
        },
        component: () => import('@/views/activity/list/index.vue'),
      },
      {
        path: 'list/edit/:id?',
        name: 'activity_edit',
        meta: {
          title: '编辑活动',
          hideInMenu: true,
          activeMenu: 'activity_list',
        },
        component: () => import('@/views/activity/list/edit.vue'),
      },
    ],
  },
];

export default routes;
