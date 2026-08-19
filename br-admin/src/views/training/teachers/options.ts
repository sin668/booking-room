import type { BusinessTagConfig } from '@/views/business/shared/options';

export const TEACHER_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  active: { label: '在职', type: 'success' },
  inactive: { label: '停用', type: 'default' },
};

export const EDUCATION_OPTIONS = [
  { label: '本科', value: '本科' },
  { label: '硕士', value: '硕士' },
  { label: '博士', value: '博士' },
];

export const ROOM_TYPE_LABELS: Record<string, string> = {
  training: '培训室',
  comprehensive: '综合室',
};
