import type { BusinessTagConfig } from '@/views/business/shared/options';

export const COURSE_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  active: { label: '已上架', type: 'success' },
  inactive: { label: '已下架', type: 'default' },
};
