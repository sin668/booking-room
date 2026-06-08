import { RouteRecordRaw } from 'vue-router';
import { GiftOutline } from '@vicons/ionicons5';
import { Layout } from '@/router/constant';
import { renderIcon } from '@/utils/index';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/coupon',
    name: 'Coupon',
    redirect: '/coupon/list',
    component: Layout,
    meta: {
      title: '卡券管理',
      icon: renderIcon(GiftOutline),
      sort: 3,
    },
    children: [
      {
        path: 'list',
        name: 'coupon_list',
        meta: {
          title: '卡券列表',
        },
        component: () => import('@/views/coupon/list/index.vue'),
      },
    ],
  },
];

export default routes;
