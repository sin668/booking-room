import { RouteRecordRaw } from 'vue-router';
import { Layout } from '@/router/constant';
import { HomeOutline } from '@vicons/ionicons5';
import { renderIcon } from '@/utils/index';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/room',
    name: 'Room',
    redirect: '/room/list',
    component: Layout,
    meta: {
      title: '门店管理',
      icon: renderIcon(HomeOutline),
      sort: 3,
    },
    children: [
      {
        path: 'list',
        name: 'room_list',
        meta: {
          title: '门店列表',
        },
        component: () => import('@/views/room/list/index.vue'),
      },
      {
        path: 'list/:id/seats',
        name: 'room_seats',
        meta: {
          title: '座位管理',
          hideInMenu: true,
        },
        component: () => import('@/views/room/seats/index.vue'),
      },
    ],
  },
];

export default routes;
