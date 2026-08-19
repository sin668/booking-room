import type { FormSchema } from '../../../components/Form';
import { formatAdminDate } from './formatters';
import type { BusinessOption } from './options';

export type DateRangeValue = [number, number] | null | undefined;

export function createKeywordSchema(field: string, placeholder: string): FormSchema {
  return {
    field,
    component: 'NInput',
    label: '关键词',
    componentProps: { placeholder },
  };
}

export function createStatusSchema(field: string, options: BusinessOption[]): FormSchema {
  return {
    field,
    component: 'NSelect',
    label: '状态',
    componentProps: {
      placeholder: '全部',
      options,
    },
  };
}

export function createRoomSelectSchema(options: BusinessOption<number>[]): FormSchema {
  return {
    field: 'room_id',
    component: 'NSelect',
    label: '学习室',
    componentProps: {
      placeholder: '全部',
      options,
    },
  };
}

export function createDateRangeSchema(field: string, label: string): FormSchema {
  return {
    field,
    component: 'NDatePicker',
    label,
    componentProps: {
      type: 'daterange',
      clearable: true,
      placeholder: '选择日期范围',
    },
  };
}

export function normalizeDateRange(dateRange: DateRangeValue) {
  if (!dateRange?.[0] || !dateRange?.[1]) return {};
  return {
    date_start: formatAdminDate(dateRange[0]),
    date_end: formatAdminDate(dateRange[1]),
  };
}
