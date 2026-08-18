import { RouteRecordRaw } from 'vue-router';
import { Layout } from '@/router/constant';
import { SchoolOutline } from '@vicons/ionicons5';
import { renderIcon } from '@/utils/index';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/training',
    name: 'Training',
    redirect: '/training/courses',
    component: Layout,
    meta: {
      title: '培训管理',
      icon: renderIcon(SchoolOutline),
      sort: 3,
    },
    children: [
      {
        path: 'courses',
        name: 'training_courses',
        meta: {
          title: '培训课程',
        },
        component: () => import('@/views/training/courses/index.vue'),
      },
    ],
  },
];

export default routes;
