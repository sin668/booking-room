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

export function buildBookingTableColumns(): BasicColumn<BookingItem>[] {
  return [
    { title: 'ID', key: 'id', width: 60 },
    {
      title: '用户ID',
      key: 'user_id',
      width: 120,
      ellipsis: { tooltip: true },
      render(record) {
        return record.user_id.slice(0, 8) + '...';
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
      width: 160,
      render(record) {
        return `${record.start_time}~${record.end_time}`;
      },
    },
    createMoneyColumn<BookingItem>('金额', 'total_price', 90),
    createTagColumn<BookingItem>('状态', 'status', BOOKING_STATUS_TAGS, 90),
    createDateTimeColumn<BookingItem>('创建时间', 'created_at'),
  ];
}
