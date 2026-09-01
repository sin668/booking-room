import type { BasicColumn } from '../../../components/Table';
import type { BusinessOption } from '../../business/shared/options';
import { BOOKING_STATUS_OPTIONS, BOOKING_STATUS_TAGS } from '../../business/shared/options';
import {
  createDateRangeSchema,
  createRoomSelectSchema,
  createStatusSchema,
} from '../../business/shared/formSchemaBuilders';
import {
  createDateTimeColumn,
  createMoneyColumn,
  createTagColumn,
} from '../../business/shared/tableBuilders';
import type { BookingItem } from '../../../api/booking';

export function buildBookingSearchSchemas(roomOptions: BusinessOption<number>[]) {
  return [
    createStatusSchema('status', BOOKING_STATUS_OPTIONS),
    createRoomSelectSchema([{ label: '全部', value: 0 }, ...roomOptions]),
    createDateRangeSchema('dateRange', '预约日期'),
  ];
}

const WEEKDAY_NAMES = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

export function formatBookingType(record: BookingItem): string {
  return record.booking_type === 'course' ? '课程' : '自习室';
}

/**
 * 格式化课程预约的 time_slots，输出如"周三 10:00-12:00、周六 12:00-14:00"。
 * 兼容三种历史格式：
 * - [{"weekday": N, "time_slot": "HH:MM-HH:MM"}]
 * - ["HH:MM-HH:MM"]（旧数据，缺省周几）
 * - {"weekday": N, "start": "HH:MM", "end": "HH:MM"}
 * 解析失败返回 null，由调用方回退展示。
 */
export function formatTimeSlots(raw: string | null | undefined): string | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    const items = Array.isArray(parsed) ? parsed : [parsed];
    const parts: string[] = [];
    for (const item of items) {
      if (typeof item === 'string') {
        parts.push(item);
        continue;
      }
      if (!item || typeof item !== 'object') continue;
      const weekday = Number(item.weekday);
      const weekdayName =
        Number.isInteger(weekday) && weekday >= 1 && weekday <= 7
          ? WEEKDAY_NAMES[weekday - 1]
          : null;
      const slot =
        typeof item.time_slot === 'string'
          ? item.time_slot
          : item.start && item.end
            ? `${item.start}-${item.end}`
            : null;
      if (!slot) continue;
      parts.push(weekdayName ? `${weekdayName} ${slot}` : slot);
    }
    return parts.length > 0 ? parts.join('、') : null;
  } catch {
    return null;
  }
}

export function formatBookingTimeRange(record: BookingItem): string {
  if (record.booking_type === 'course') {
    const formatted = formatTimeSlots(record.time_slots);
    if (formatted) return formatted;
  }
  return `${record.start_time}~${record.end_time}`;
}

export function buildBookingTableColumns(): BasicColumn<BookingItem>[] {
  return [
    { title: 'ID', key: 'id', width: 60 },
    {
      title: '预约类型',
      key: 'booking_type',
      width: 90,
      render(record) {
        return formatBookingType(record);
      },
    },
    {
      title: '用户昵称',
      key: 'user_nickname',
      width: 120,
      ellipsis: { tooltip: true },
      render(record) {
        return record.user_nickname || record.user_id.slice(0, 8) + '...';
      },
    },
    {
      title: '自习室名称',
      key: 'room_name',
      width: 140,
      render(record) {
        return record.room?.name || '-';
      },
    },
    {
      title: '座位编号',
      key: 'seat_number',
      width: 100,
      render(record) {
        return record.seat?.seat_number || '-';
      },
    },
    { title: '预约日期', key: 'date', width: 110 },
    {
      title: '时段',
      key: 'time_range',
      width: 200,
      ellipsis: { tooltip: true },
      render(record) {
        return formatBookingTimeRange(record);
      },
    },
    createMoneyColumn<BookingItem>('金额', 'total_price', 90),
    createTagColumn<BookingItem>('状态', 'status', BOOKING_STATUS_TAGS, 90),
    createDateTimeColumn<BookingItem>('创建时间', 'created_at'),
  ];
}
