import { h } from 'vue';
import { NImage, NTag } from 'naive-ui';
import type { BasicColumn } from '@/components/Table';
import type { RoomItem } from '@/api/room';

export const columns: BasicColumn<RoomItem>[] = [
  {
    title: 'ID',
    key: 'id',
    width: 60,
  },
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
  {
    title: '名称',
    key: 'name',
    width: 180,
    ellipsis: { tooltip: true },
  },
  {
    title: '地址',
    key: 'address',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '营业时间',
    key: 'business_hours',
    width: 120,
  },
  {
    title: '最低价格',
    key: 'min_price',
    width: 100,
    render(record) {
      return `¥${record.min_price}`;
    },
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render(record) {
      return h(
        NTag,
        { type: record.status === 'open' ? 'success' : 'error' },
        { default: () => (record.status === 'open' ? '营业中' : '已关闭') },
      );
    },
  },
  {
    title: '座位数',
    key: 'seat_count',
    width: 80,
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 170,
  },
];
