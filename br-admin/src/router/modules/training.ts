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
      {
        path: 'courses/edit/:id?',
        name: 'training_course_edit',
        meta: {
          title: '编辑课程',
          hidden: true,
          activeMenu: 'training_courses',
        },
        component: () => import('@/views/training/courses/edit.vue'),
      },
    ],
  },
];

export default routes;
