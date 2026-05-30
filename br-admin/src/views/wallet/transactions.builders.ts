import { h } from 'vue';
import { NTag } from 'naive-ui';
import type { BasicColumn } from '../../components/Table';
import type { WalletStatistics, WalletTransactionItem } from '../../api/wallet';
import {
  formatAdminDateTime,
  formatAdminMoney,
  formatPaymentMethod,
  getTagConfig,
} from '../business/shared/formatters';
import { WALLET_STATUS_TAGS, WALLET_TRANSACTION_TYPE_TAGS } from '../business/shared/options';

export function buildWalletFilterOptions() {
  return {
    typeOptions: [
      { label: '全部', value: null },
      { label: '钱包充值', value: 'recharge' },
      { label: '预约消费', value: 'consume' },
      { label: '预约退款', value: 'booking_refund' },
      { label: '钱包退款', value: 'refund' },
    ],
    statusOptions: [
      { label: '全部', value: null },
      { label: '已完成', value: 'completed' },
      { label: '失败', value: 'failed' },
      { label: '已取消', value: 'cancelled' },
    ],
  };
}

export function buildWalletStatCards(statistics: WalletStatistics) {
  return [
    {
      key: 'total_recharge',
      label: '钱包充值',
      value: statistics.total_recharge,
      className: 'text-green',
    },
    {
      key: 'total_consume',
      label: '预约消费',
      value: statistics.total_consume,
      className: 'text-orange',
    },
    {
      key: 'total_refund',
      label: '预约退款',
      value: statistics.total_refund,
      className: 'text-red',
    },
    {
      key: 'net_income',
      label: '净收入',
      value: statistics.net_income,
      className: 'text-blue',
    },
  ];
}

export function buildWalletTransactionColumns(): BasicColumn<WalletTransactionItem>[] {
  return [
    {
      title: '交易时间',
      key: 'created_at',
      width: 170,
      render(record) {
        return formatAdminDateTime(record.created_at);
      },
    },
    {
      title: '用户',
      key: 'user',
      width: 180,
      render(record) {
        return h('div', { class: 'user-cell' }, [
          h('div', { class: 'user-name' }, record.user_nickname || '未设置昵称'),
          h('div', { class: 'user-phone' }, record.user_phone || '-'),
        ]);
      },
    },
    {
      title: '交易类型',
      key: 'type',
      width: 110,
      render(record) {
        const config = getTagConfig(WALLET_TRANSACTION_TYPE_TAGS, record.type);
        return h(NTag, { type: config.type, size: 'small' }, { default: () => config.label });
      },
    },
    {
      title: '金额',
      key: 'amount',
      width: 130,
      render(record) {
        const isIncome = ['recharge', 'refund', 'booking_refund', 'wallet_refund'].includes(
          record.type
        );
        return h(
          'span',
          { class: isIncome ? 'amount-positive' : 'amount-negative' },
          `${isIncome ? '+' : '-'}${formatAdminMoney(record.amount)}`
        );
      },
    },
    {
      title: '余额',
      key: 'balance_after',
      width: 120,
      render(record) {
        return formatAdminMoney(record.balance_after);
      },
    },
    {
      title: '状态',
      key: 'status',
      width: 110,
      render(record) {
        const config = getTagConfig(WALLET_STATUS_TAGS, record.status);
        return h(NTag, { type: config.type, size: 'small' }, { default: () => config.label });
      },
    },
    {
      title: '支付方式',
      key: 'payment_method',
      width: 130,
      render(record) {
        return formatPaymentMethod(record.payment_method);
      },
    },
  ];
}
