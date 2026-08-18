import { h } from 'vue';
import { NTag } from 'naive-ui';
import type { BasicColumn } from '@/components/Table';
import type { AdminCouponItem } from '@/api/coupon';
import { createDateTimeColumn, createTextColumn } from '@/views/business/shared/tableBuilders';
import { formatAdminDateTime, formatAdminMoney } from '@/views/business/shared/formatters';

export const couponTypeLabels: Record<string, string> = {
  threshold_amount_off: '满减券',
  amount_off: '立减券',
  percentage_off: '折扣券',
};

export const couponScopeLabels: Record<string, string> = {
  all: '全场通用',
  first_booking: '首次预约',
  vip_only: 'VIP专享',
  seat_zone: '指定区域',
};

const typeTagMap: Record<string, 'default' | 'error' | 'primary' | 'info' | 'success' | 'warning'> =
  {
    threshold_amount_off: 'success',
    amount_off: 'info',
    percentage_off: 'warning',
  };

export function formatCouponRule(record: AdminCouponItem) {
  if (record.type === 'percentage_off' && record.discount_percent) {
    return `${Number(record.discount_percent) / 10}折`;
  }
  if (record.type === 'threshold_amount_off') {
    return `满${formatAdminMoney(record.min_order_amount)}减${formatAdminMoney(
      record.discount_amount || 0
    )}`;
  }
  if (record.type === 'amount_off') {
    return `立减${formatAdminMoney(record.discount_amount || 0)}`;
  }
  return '-';
}

export function formatCouponScope(record: Pick<AdminCouponItem, 'scope' | 'seat_zone'>) {
  if (record.scope === 'seat_zone' && record.seat_zone) {
    return `区域：${record.seat_zone}`;
  }
  return couponScopeLabels[record.scope] || record.scope;
}

export function isCouponExpired(record: Pick<AdminCouponItem, 'expires_at'>): boolean {
  return new Date(record.expires_at) < new Date();
}

export function buildCouponTableColumns(): BasicColumn<AdminCouponItem>[] {
  return [
    { title: 'ID', key: 'id', width: 70 },
    createTextColumn<AdminCouponItem>('名称', 'name', 180),
    {
      title: '类型',
      key: 'type',
      width: 100,
      render(record) {
        return h(
          NTag,
          { type: typeTagMap[record.type] || 'default', size: 'small' },
          { default: () => couponTypeLabels[record.type] || record.type }
        );
      },
    },
    {
      title: '优惠规则',
      key: 'discount_rule',
      width: 160,
      render: formatCouponRule,
    },
    {
      title: '适用范围',
      key: 'scope',
      width: 120,
      render: formatCouponScope,
    },
    {
      title: '有效期',
      key: 'validity',
      width: 280,
      render(record) {
        return `${formatAdminDateTime(record.valid_from)} 至 ${formatAdminDateTime(
          record.expires_at
        )}`;
      },
    },
    {
      title: '状态',
      key: 'is_active',
      width: 90,
      render(record) {
        const expired = isCouponExpired(record);
        if (expired) {
          return h(NTag, { type: 'error', size: 'small' }, { default: () => '过期' });
        }
        return h(
          NTag,
          { type: record.is_active ? 'success' : 'default', size: 'small' },
          { default: () => (record.is_active ? '启用' : '停用') }
        );
      },
    },
    createDateTimeColumn<AdminCouponItem>('创建时间', 'created_at'),
  ];
}
