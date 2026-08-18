import type { BusinessTagConfig } from '@/views/business/shared/options';

export const COURSE_STATUS_TAGS: Record<string, BusinessTagConfig> = {
  active: { label: '已上架', type: 'success' },
  inactive: { label: '已下架', type: 'default' },
};

// 课程分类选项（中文名称映射）
export const COURSE_CATEGORY_OPTIONS = [
  { label: '考研辅导', value: 'postgraduate' },
  { label: '公考备考', value: 'civil_service' },
  { label: '语言培训', value: 'language' },
  { label: '技能提升', value: 'skills' },
  { label: '职业资格', value: 'professional' },
  { label: '小学辅导', value: 'primaryschool' },
  { label: '中学辅导', value: 'middleschool' },
];

export const COURSE_CATEGORY_LABELS: Record<string, string> = Object.fromEntries(
  COURSE_CATEGORY_OPTIONS.map((o) => [o.value, o.label])
);
