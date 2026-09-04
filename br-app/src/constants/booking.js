export const BOOKING_TABS = [
  { label: '全部', value: 'all' },
  { label: '待开始', value: 'pending_start' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
]

export const BOOKING_STATUS_LABELS = {
  pending_confirm: '待确认',
  pending_start: '待开始',
  in_progress: '进行中',
  completed: '已完成',
  cancelled: '已取消',
}

// 支付域状态文案（Q13/F23）：从 BOOKING_STATUS_LABELS 剥离，消除 pending 键「待支付/待开始」同键双义
export const PAYMENT_STATUS_LABELS = {
  pending: '待支付',
}

export const SEAT_ZONE_LABELS = {
  quiet: '静音区',
  keyboard: '键盘区',
  vip: 'VIP区',
}
