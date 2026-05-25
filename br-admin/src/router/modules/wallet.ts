import { RouteRecordRaw } from 'vue-router';
import { Layout } from '@/router/constant';
import { WalletOutlined } from '@vicons/antd';
import { renderIcon } from '@/utils/index';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/wallet',
    name: 'Wallet',
    redirect: '/wallet/transactions',
    component: Layout,
    meta: {
      title: '钱包管理',
      icon: renderIcon(WalletOutlined),
      sort: 5,
    },
    children: [
      {
        path: 'transactions',
        name: 'wallet_transactions',
        meta: { title: '钱包流水' },
        component: () => import('@/views/wallet/transactions.vue'),
      },
    ],
  },
];

export default routes;
