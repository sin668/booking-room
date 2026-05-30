import { h } from 'vue';
import { NImage } from 'naive-ui';
import type { BasicColumn } from '../../../components/Table';
import type { ActivityItem } from '../../../api/activity';
import { ACTIVITY_STATUS_OPTIONS, ACTIVITY_STATUS_TAGS } from '../../business/shared/options';
import { createKeywordSchema, createStatusSchema } from '../../business/shared/formSchemaBuilders';
import {
  createDateTimeColumn,
  createTagColumn,
  createTextColumn,
} from '../../business/shared/tableBuilders';

export function buildActivitySearchSchemas() {
  return [
    createKeywordSchema('keyword', '搜索标题或描述'),
    createStatusSchema('is_active', ACTIVITY_STATUS_OPTIONS),
  ];
}

export function buildActivityTableColumns(): BasicColumn<ActivityItem>[] {
  return [
    { title: 'ID', key: 'id', width: 60 },
    createTextColumn<ActivityItem>('标题', 'title', 180),
    createTextColumn<ActivityItem>('描述', 'description', 200),
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
    { title: '参与人数', key: 'participant_count', width: 90 },
    { title: '排序', key: 'sort_order', width: 70 },
    createTagColumn<ActivityItem>('状态', 'is_active', ACTIVITY_STATUS_TAGS, 80),
    createDateTimeColumn<ActivityItem>('创建时间', 'created_at'),
  ];
}
