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
  { label: '已上架', value: 'open' },
  { label: '已下架', value: 'closed' },
];

export const ROOM_TYPE_OPTIONS: BusinessOption[] = [
  { label: '全部', value: '' },
  { label: '学习室', value: 'study' },
  { label: '培训室', value: 'training' },
  { label: '综合室', value: 'comprehensive' },
];

export const ROOM_TYPE_LABELS: Record<string, string> = {
  study: '学习室',
  training: '培训室',
  comprehensive: '综合室',
};

export const ACTIVITY_STATUS_OPTIONS: BusinessOption[] = [
  { label: '全部', value: '' },
  { label: '已上架', value: 'true' },
  { label: '已下架', value: 'false' },
];

export const BOOKING_STATUS_OPTIONS: BusinessOption[] = [
  { label: '全部', value: '' },
  { label: '待确认', value: 'pending_confirm' },
  { label: '待开始', value: 'pending' },
  { label: '进行中', value: 'confirmed' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
];

export const SEAT_ZONE_OPTIONS: BusinessOption[] = [
  { label: '静音区', value: 'quiet' },
  { label: '键盘区', value: 'keyboard' },
  { label: 'VIP区', value: 'vip' },
];

export const BOOKING_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  pending_confirm: { label: '待确认', type: 'warning' },
  pending: { label: '待开始', type: 'default' },
  confirmed: { label: '进行中', type: 'success' },
  completed: { label: '已完成', type: 'info' },
  cancelled: { label: '已取消', type: 'error' },
};

export const ROOM_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  open: { label: '已上架', type: 'success' },
  closed: { label: '已下架', type: 'default' },
};

export const ROOM_TYPE_TAGS: Record<string, BusinessTagConfig> = {
  study: { label: '学习室', type: 'info' },
  training: { label: '培训室', type: 'warning' },
  comprehensive: { label: '综合室', type: 'success' },
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
