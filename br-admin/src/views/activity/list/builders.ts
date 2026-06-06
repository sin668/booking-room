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
import type { ActivityCouponFormItem } from '../../../api/activity';

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
    {
      title: '关联卡券',
      key: 'activity_coupon_count',
      width: 90,
      render(record) {
        return record.activity_coupon_count ?? record.activity_coupons?.length ?? 0;
      },
    },
    {
      title: '已领取',
      key: 'activity_coupon_claimed_count',
      width: 90,
      render(record) {
        return (
          record.activity_coupon_claimed_count ??
          record.activity_coupons?.reduce((total, item) => total + (item.claimed_quantity ?? 0), 0) ??
          0
        );
      },
    },
    { title: '排序', key: 'sort_order', width: 70 },
    createTagColumn<ActivityItem>('状态', 'is_active', ACTIVITY_STATUS_TAGS, 80),
    createDateTimeColumn<ActivityItem>('创建时间', 'created_at'),
  ];
}

export function buildActivityCouponFormItem(sortOrder: number): ActivityCouponFormItem {
  return {
    coupon_id: null,
    total_quantity: 0,
    claimed_quantity: 0,
    per_user_limit: 1,
    claim_starts_at: null,
    claim_ends_at: null,
    is_active: true,
    sort_order: sortOrder,
    display_title: '',
    display_description: '',
    coupon_title: '',
    coupon_type: '',
    discount_rule: '',
    valid_from: null,
    expires_at: null,
  };
}

export function validateActivityCoupons(coupons: ActivityCouponFormItem[]): string[] {
  const messages: string[] = [];

  coupons.forEach((coupon, index) => {
    if (coupon._destroy) return;

    const label = `第 ${index + 1} 个卡券配置`;
    if (!coupon.coupon_id || coupon.coupon_id <= 0) {
      messages.push(`${label}请选择卡券模板`);
    }

    if (coupon.total_quantity === null || coupon.total_quantity === undefined) {
      messages.push(`${label}请填写总库存`);
    } else if (coupon.total_quantity < 0) {
      messages.push(`${label}总库存不能小于 0`);
    }

    if (!coupon.per_user_limit || coupon.per_user_limit <= 0) {
      messages.push(`${label}每人限领必须大于 0`);
    }

    if (
      coupon.claim_starts_at &&
      coupon.claim_ends_at &&
      new Date(coupon.claim_ends_at).getTime() < new Date(coupon.claim_starts_at).getTime()
    ) {
      messages.push(`${label}领取结束时间不能早于开始时间`);
    }
  });

  return messages;
}
