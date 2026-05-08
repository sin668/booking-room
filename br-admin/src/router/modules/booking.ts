import { RouteRecordRaw } from 'vue-router';
import { Layout } from '@/router/constant';
import { FileTextOutlined } from '@vicons/antd';
import { renderIcon } from '@/utils/index';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/booking',
    name: 'Booking',
    redirect: '/booking/list',
    component: Layout,
    meta: {
      title: '订单管理',
      icon: renderIcon(FileTextOutlined),
      sort: 4,
    },
    children: [
      {
        path: 'list',
        name: 'booking_list',
        meta: { title: '订单列表' },
        component: () => import('@/views/booking/list/index.vue'),
      },
    ],
  },
];

export default routes;