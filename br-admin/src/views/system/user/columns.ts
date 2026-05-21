import { h } from 'vue';
import { NTag } from 'naive-ui';
import type { AdminRoleSummary } from '@/api/system/user';

export const columns = [
  {
    title: 'ID',
    key: 'id',
  },
  {
    title: '手机号',
    key: 'phone',
  },
  {
    title: '昵称',
    key: 'nickname',
    render(row) {
      return row.nickname || '-';
    },
  },
  {
    title: '用户类型',
    key: 'user_type',
    render(row) {
      return h(
        NTag,
        {
          type: row.user_type === 'admin' ? 'success' : 'primary',
          size: 'small',
        },
        {
          default: () => (row.user_type === 'admin' ? '管理员' : 'App用户'),
        }
      );
    },
  },
  {
    title: '余额',
    key: 'balance',
  },
  {
    title: '状态',
    key: 'status',
    render(row) {
      const map: Record<string, { type: 'success' | 'error' | 'warning'; label: string }> = {
        active: { type: 'success', label: '正常' },
        banned: { type: 'error', label: '封禁' },
        disabled: { type: 'warning', label: '禁用' },
      };
      const cfg = map[row.status] || { type: 'warning', label: row.status };
      return h(NTag, { type: cfg.type, size: 'small' }, { default: () => cfg.label });
    },
  },
  {
    title: '角色',
    key: 'roles',
    render(row) {
      const roles: AdminRoleSummary[] = row.roles || [];
      if (!roles.length) return '-';
      return h('span', {}, roles.map((r: AdminRoleSummary) => h(NTag, { type: 'info', size: 'small', class: 'mr-1' }, { default: () => r.name })));
    },
  },
  {
    title: '预约数',
    key: 'booking_count',
    width: 80,
  },
  {
    title: '卡券数',
    key: 'coupon_count',
    width: 80,
  },
  {
    title: '注册时间',
    key: 'created_at',
  },
];
