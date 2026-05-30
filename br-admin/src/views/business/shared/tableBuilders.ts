import { h } from 'vue';
import { NTag } from 'naive-ui';
import type { BasicColumn } from '../../../components/Table';
import { formatAdminDateTime, formatAdminMoney, getTagConfig } from './formatters';
import type { BusinessTagConfig } from './options';

export function createTextColumn<T>(title: string, key: keyof T | string, width?: number): BasicColumn<T> {
  return {
    title,
    key: String(key),
    width,
    ellipsis: { tooltip: true },
  };
}

export function createMoneyColumn<T>(title: string, key: keyof T | string, width = 110): BasicColumn<T> {
  return {
    title,
    key: String(key),
    width,
    render(record) {
      return formatAdminMoney(record[String(key)]);
    },
  };
}

export function createDateTimeColumn<T>(title: string, key: keyof T | string, width = 170): BasicColumn<T> {
  return {
    title,
    key: String(key),
    width,
    render(record) {
      return formatAdminDateTime(record[String(key)]);
    },
  };
}

export function createTagColumn<T>(
  title: string,
  key: keyof T | string,
  configMap: Record<string, BusinessTagConfig>,
  width = 100
): BasicColumn<T> {
  return {
    title,
    key: String(key),
    width,
    render(record) {
      const config = getTagConfig(configMap, record[String(key)]);
      return h(NTag, { type: config.type, size: 'small' }, { default: () => config.label });
    },
  };
}
