export const BOOKING_TABS = [
  { label: '全部', value: 'all' },
  { label: '待开始', value: 'pending_start' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
]

export const BOOKING_STATUS_LABELS = {
  pending: '待支付',
  pending_start: '待开始',
  confirmed: '已预约',
  in_progress: '进行中',
  completed: '已完成',
  cancelled: '已取消',
}

export const SEAT_ZONE_LABELS = {
  quiet: '静音区',
  keyboard: '键盘区',
  vip: 'VIP区',
}
