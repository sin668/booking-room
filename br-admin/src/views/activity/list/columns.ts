import { h } from 'vue';
import { NImage, NTag } from 'naive-ui';
import type { BasicColumn } from '@/components/Table';
import type { ActivityItem } from '@/api/activity';

export const columns: BasicColumn<ActivityItem>[] = [
  {
    title: 'ID',
    key: 'id',
    width: 60,
  },
  {
    title: '标题',
    key: 'title',
    width: 180,
    ellipsis: { tooltip: true },
  },
  {
    title: '描述',
    key: 'description',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '封面图',
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
    title: '参与人数',
    key: 'participant_count',
    width: 90,
  },
  {
    title: '排序',
    key: 'sort_order',
    width: 70,
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render(record) {
      return h(
        NTag,
        { type: record.is_active ? 'success' : 'default' },
        { default: () => (record.is_active ? '已上架' : '已下架') },
      );
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 170,
  },
];
