export type BusinessTagType = 'success' | 'warning' | 'error' | 'info' | 'default';

export interface BusinessOption<T = string | number | boolean | null> {
  label: string;
  value: T;
}

export interface BusinessTagConfig {
  label: string;
  type: BusinessTagType;
}

export const ROOM_STATUS_OPTIONS: BusinessOption[] = [
  { label: '全部', value: '' },
  { label: '营业中', value: 'open' },
  { label: '已关闭', value: 'closed' },
];

export const ACTIVITY_STATUS_OPTIONS: BusinessOption[] = [
  { label: '全部', value: '' },
  { label: '已上架', value: 'true' },
  { label: '已下架', value: 'false' },
];

export const BOOKING_STATUS_OPTIONS: BusinessOption[] = [
  { label: '全部', value: '' },
  { label: '已确认', value: 'confirmed' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
];

export const SEAT_ZONE_OPTIONS: BusinessOption[] = [
  { label: '静音区', value: 'quiet' },
  { label: '键盘区', value: 'keyboard' },
  { label: 'VIP区', value: 'vip' },
];

export const BOOKING_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  confirmed: { label: '已确认', type: 'success' },
  completed: { label: '已完成', type: 'info' },
  cancelled: { label: '已取消', type: 'error' },
};

export const ROOM_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  open: { label: '营业中', type: 'success' },
  closed: { label: '已关闭', type: 'error' },
};

export const ACTIVITY_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  true: { label: '已上架', type: 'success' },
  false: { label: '已下架', type: 'default' },
};

export const WALLET_TRANSACTION_TYPE_TAGS: Record<string, BusinessTagConfig> = {
  recharge: { label: '钱包充值', type: 'success' },
  consume: { label: '预约消费', type: 'warning' },
  booking_refund: { label: '预约退款', type: 'success' },
  refund: { label: '钱包退款', type: 'error' },
  wallet_refund: { label: '钱包退款', type: 'error' },
};

export const WALLET_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  pending: { label: '待处理', type: 'warning' },
  completed: { label: '已完成', type: 'success' },
  failed: { label: '失败', type: 'error' },
  cancelled: { label: '已取消', type: 'default' },
};
