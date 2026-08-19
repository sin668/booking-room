import { h } from 'vue';
import { NImage, NTag } from 'naive-ui';
import type { BasicColumn } from '../../../components/Table';
import type { FormSchema } from '../../../components/Form';
import type { RoomItem } from '../../../api/room';
import {
  ROOM_STATUS_OPTIONS,
  ROOM_TYPE_OPTIONS,
  ROOM_TYPE_TAGS,
  type BusinessOption,
} from '../../business/shared/options';
import { createKeywordSchema, createStatusSchema } from '../../business/shared/formSchemaBuilders';
import {
  createDateTimeColumn,
  createMoneyColumn,
  createTagColumn,
  createTextColumn,
} from '../../business/shared/tableBuilders';

export function buildRoomSearchSchemas(cityOptions: BusinessOption<number>[]): FormSchema[] {
  return [
    createKeywordSchema('keyword', '搜索名称或地址'),
    {
      field: 'city_id',
      component: 'NSelect',
      label: '所在城市',
      componentProps: {
        placeholder: '全部',
        options: cityOptions,
        clearable: true,
      },
    },
    {
      field: 'room_type',
      component: 'NSelect',
      label: '类型',
      componentProps: {
        placeholder: '全部',
        options: ROOM_TYPE_OPTIONS,
      },
    },
    createStatusSchema('status', ROOM_STATUS_OPTIONS),
  ];
}

// 判断当前时间是否在营业时间段内（格式如 08:00-22:00）
export function isOpenNow(businessHours: string | null | undefined): boolean {
  if (!businessHours) return true;
  const match = businessHours.match(/(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})/);
  if (!match) return true;
  const now = new Date();
  const current = now.getHours() * 60 + now.getMinutes();
  const start = Number(match[1]) * 60 + Number(match[2]);
  const end = Number(match[3]) * 60 + Number(match[4]);
  if (start <= end) {
    return current >= start && current <= end;
  }
  // 跨天营业（如 22:00-02:00）
  return current >= start || current <= end;
}

function renderRoomStatus(record: RoomItem) {
  // 先判断是否上架，再根据营业时间判断是否营业中
  if (record.status !== 'open') {
    return h(NTag, { type: 'default', size: 'small' }, { default: () => '已下架' });
  }
  return isOpenNow(record.business_hours)
    ? h(NTag, { type: 'success', size: 'small' }, { default: () => '营业中' })
    : h(NTag, { type: 'warning', size: 'small' }, { default: () => '休息中' });
}

export function buildRoomTableColumns(): BasicColumn<RoomItem>[] {
  return [
    { title: 'ID', key: 'id', width: 60 },
    {
      title: '封面缩略图',
      key: 'cover_image',
      width: 100,
      render(record) {
        return record.cover_image
          ? h(NImage, {
              src: record.cover_image,
              width: 60,
              height: 40,
              objectFit: 'cover',
              previewDisabled: true,
            })
          : '暂无';
      },
    },
    createTextColumn<RoomItem>('名称', 'name', 180),
    createTagColumn<RoomItem>('类型', 'room_type', ROOM_TYPE_TAGS, 90),
    {
      title: '所在城市',
      key: 'city_name',
      width: 100,
      render(record) {
        return record.city_name || '暂无';
      },
    },
    createTextColumn<RoomItem>('地址', 'address', 200),
    { title: '营业时间', key: 'business_hours', width: 120 },
    createMoneyColumn<RoomItem>('最低价格', 'min_price', 100),
    {
      title: '状态',
      key: 'status',
      width: 90,
      render(record) {
        return renderRoomStatus(record);
      },
    },
    createDateTimeColumn<RoomItem>('创建时间', 'created_at'),
  ];
}
