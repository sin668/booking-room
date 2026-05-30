import { h } from 'vue';
import { NImage } from 'naive-ui';
import type { BasicColumn } from '../../../components/Table';
import type { RoomItem } from '../../../api/room';
import { ROOM_STATUS_OPTIONS, ROOM_STATUS_TAGS } from '../../business/shared/options';
import { createKeywordSchema, createStatusSchema } from '../../business/shared/formSchemaBuilders';
import {
  createDateTimeColumn,
  createMoneyColumn,
  createTagColumn,
  createTextColumn,
} from '../../business/shared/tableBuilders';

export function buildRoomSearchSchemas() {
  return [
    createKeywordSchema('keyword', '搜索名称或地址'),
    createStatusSchema('status', ROOM_STATUS_OPTIONS),
  ];
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
    createTextColumn<RoomItem>('地址', 'address', 200),
    { title: '营业时间', key: 'business_hours', width: 120 },
    createMoneyColumn<RoomItem>('最低价格', 'min_price', 100),
    createTagColumn<RoomItem>('状态', 'status', ROOM_STATUS_TAGS, 80),
    { title: '座位数', key: 'seat_count', width: 80 },
    createDateTimeColumn<RoomItem>('创建时间', 'created_at'),
  ];
}
