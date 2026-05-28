export const NOTIFICATION_TYPE_CONFIGS = [
  {
    key: 'booking',
    label: '预约提醒',
    settingLabel: '预约提醒',
    settingDescription: '预约开始前15分钟推送提醒',
    iconText: '铃',
    colorClass: 'blue-soft',
    color: '#3b82f6',
    defaultTarget: '/pages/orders/index',
  },
  {
    key: 'activity',
    label: '活动通知',
    settingLabel: '活动通知',
    settingDescription: '接收优惠活动和限时促销',
    iconText: '告',
    colorClass: 'purple-soft',
    color: '#8b5cf6',
    defaultTarget: '/pages/index/index',
  },
  {
    key: 'report',
    label: '学习报告',
    settingLabel: '学习周报',
    settingDescription: '每周一推送上周学习总结',
    iconText: '报',
    colorClass: 'green-soft',
    color: '#22c55e',
    defaultTarget: '/pages/study-record/index',
  },
  {
    key: 'arrival',
    label: '到店提醒',
    settingLabel: '到店打卡提醒',
    settingDescription: '到达门店附近时自动提醒',
    iconText: '到',
    colorClass: 'yellow-soft',
    color: '#eab308',
    defaultTarget: '/pages/qrcode/index',
  },
]

export const NOTIFICATION_TYPES = NOTIFICATION_TYPE_CONFIGS.map((item) => item.key)

export const NOTIFICATION_TYPE_MAP = NOTIFICATION_TYPE_CONFIGS.reduce((result, item) => {
  result[item.key] = item
  return result
}, {})

export function getNotificationPreferenceField(type) {
  return `${type}_enabled`
}
