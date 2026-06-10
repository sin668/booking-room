<template>
  <n-space vertical :size="12" class="activity-coupon-config">
    <n-space justify="space-between" align="center">
      <n-text strong>关联卡券配置</n-text>
      <n-button size="small" type="primary" @click="addCoupon">新增卡券配置</n-button>
    </n-space>

    <n-empty v-if="visibleCoupons.length === 0" description="暂无关联卡券配置" />

    <n-card
      v-for="item in visibleCoupons"
      :key="item.localKey"
      size="small"
      :bordered="true"
      class="activity-coupon-config__item"
    >
      <template #header>
        <n-space align="center">
          <n-text>卡券配置 {{ item.index + 1 }}</n-text>
          <n-tag v-if="item.coupon.id" size="small" type="info">已保存</n-tag>
        </n-space>
      </template>
      <template #header-extra>
        <n-space>
          <n-button
            size="tiny"
            :disabled="item.visibleIndex === 0"
            @click="moveCoupon(item.index, -1)"
          >
            上移
          </n-button>
          <n-button
            size="tiny"
            :disabled="item.visibleIndex === visibleCoupons.length - 1"
            @click="moveCoupon(item.index, 1)"
          >
            下移
          </n-button>
          <n-button size="tiny" type="error" ghost @click="removeCoupon(item.index)">删除</n-button>
        </n-space>
      </template>

      <n-grid :cols="2" :x-gap="16" :y-gap="12" responsive="screen">
        <n-grid-item>
          <n-form-item label="卡券模板">
            <n-select
              v-model:value="item.coupon.coupon_id"
              filterable
              remote
              clearable
              :options="couponOptions"
              :loading="couponSearchLoading"
              placeholder="搜索卡券名称"
              @focus="() => loadCouponOptions()"
              @search="handleCouponSearch"
              @update:value="handleCouponSelect(item.index, $event)"
              style="width: 100%"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="卡券类型">
            <n-input
              :value="formatCouponType(item.coupon)"
              readonly
              placeholder="保存后由卡券模板返回"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="卡券名称">
            <n-input :value="item.coupon.coupon_title || '保存后由卡券模板返回'" readonly />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="优惠规则">
            <n-input :value="item.coupon.discount_rule || '保存后由卡券模板返回'" readonly />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="卡券有效期">
            <n-input :value="formatCouponValidity(item.coupon)" readonly />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="总库存">
            <n-input-number
              v-model:value="item.coupon.total_quantity"
              :min="0"
              :precision="0"
              style="width: 100%"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="每人限领">
            <n-input-number
              v-model:value="item.coupon.per_user_limit"
              :min="1"
              :precision="0"
              style="width: 100%"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="领取开始">
            <n-date-picker
              v-model:formatted-value="item.coupon.claim_starts_at"
              value-format="yyyy-MM-dd HH:mm:ss"
              type="datetime"
              clearable
              style="width: 100%"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="领取结束">
            <n-date-picker
              v-model:formatted-value="item.coupon.claim_ends_at"
              value-format="yyyy-MM-dd HH:mm:ss"
              type="datetime"
              clearable
              style="width: 100%"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="展示标题">
            <n-input v-model:value="item.coupon.display_title" placeholder="用户端展示标题" />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="排序">
            <n-input-number
              v-model:value="item.coupon.sort_order"
              :precision="0"
              style="width: 100%"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item :span="2">
          <n-form-item label="展示说明">
            <n-input
              v-model:value="item.coupon.display_description"
              type="textarea"
              placeholder="用户端展示说明"
              :rows="2"
            />
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="启用状态">
            <n-switch v-model:value="item.coupon.is_active">
              <template #checked>启用</template>
              <template #unchecked>停用</template>
            </n-switch>
          </n-form-item>
        </n-grid-item>
        <n-grid-item>
          <n-form-item label="已领取">
            <n-input-number
              :value="item.coupon.claimed_quantity ?? 0"
              :min="0"
              :precision="0"
              readonly
              style="width: 100%"
            />
          </n-form-item>
        </n-grid-item>
      </n-grid>
    </n-card>
  </n-space>
</template>

<script lang="ts" setup>
  import { computed, onMounted, ref, watch } from 'vue';
  import type { ActivityCouponFormItem } from '@/api/activity';
  import { getCouponById, getCouponList, type AdminCouponItem } from '@/api/coupon';
  import { buildActivityCouponFormItem } from './builders';
  import {
    formatCouponRule,
    formatCouponScope,
    couponTypeLabels,
  } from '@/views/coupon/list/columns';

  const props = defineProps<{
    coupons: ActivityCouponFormItem[];
  }>();

  const emit = defineEmits<{
    (e: 'update:coupons', value: ActivityCouponFormItem[]): void;
  }>();

  const visibleCoupons = computed(() =>
    props.coupons
      .map((coupon, index) => ({
        coupon,
        index,
        localKey: coupon.id ? `saved-${coupon.id}` : `new-${index}`,
      }))
      .filter((item) => !item.coupon._destroy)
      .map((item, visibleIndex) => ({
        ...item,
        visibleIndex,
      }))
  );

  const couponOptions = ref<{ label: string; value: number }[]>([]);
  const couponSearchLoading = ref(false);
  let couponSearchTimer: ReturnType<typeof setTimeout> | null = null;

  onMounted(() => {
    loadCouponOptions();
  });

  watch(
    () => props.coupons,
    (coupons) => {
      mergeCouponOptions(
        coupons
          .filter((coupon) => !coupon._destroy && coupon.coupon_id)
          .map((coupon) => ({
            label: coupon.coupon
              ? buildCouponOptionLabel(coupon.coupon as AdminCouponItem)
              : coupon.coupon_title || `卡券 #${coupon.coupon_id}`,
            value: Number(coupon.coupon_id),
          }))
      );
    },
    { immediate: true, deep: true }
  );

  function updateCoupons(coupons: ActivityCouponFormItem[]) {
    coupons.forEach((coupon, index) => {
      coupon.sort_order = index + 1;
    });
    emit('update:coupons', coupons);
  }

  function addCoupon() {
    updateCoupons([...props.coupons, buildActivityCouponFormItem(props.coupons.length + 1)]);
  }

  function handleCouponSearch(query: string) {
    if (couponSearchTimer) {
      clearTimeout(couponSearchTimer);
    }
    couponSearchTimer = setTimeout(async () => {
      await loadCouponOptions(query);
    }, 300);
  }

  async function loadCouponOptions(keyword = '') {
    couponSearchLoading.value = true;
    try {
      const result = await getCouponList({
        keyword,
        page_size: 20,
        is_active: true,
        valid_now: true,
      });
      setCouponOptions(
        result.items.map((coupon) => ({
          label: buildCouponOptionLabel(coupon),
          value: coupon.id,
        }))
      );
    } finally {
      couponSearchLoading.value = false;
    }
  }

  async function handleCouponSelect(index: number, couponId: number | null) {
    const nextCoupons = [...props.coupons];
    const target = nextCoupons[index];
    if (!target) return;

    if (!couponId) {
      nextCoupons[index] = {
        ...target,
        coupon_id: null,
        coupon_title: '',
        coupon_type: '',
        discount_rule: '',
        valid_from: null,
        expires_at: null,
      };
      updateCoupons(nextCoupons);
      return;
    }

    const duplicate = props.coupons.some(
      (coupon, couponIndex) =>
        couponIndex !== index && !coupon._destroy && Number(coupon.coupon_id) === Number(couponId)
    );
    if (duplicate) {
      window['$message'].warning('该卡券已关联此活动');
      nextCoupons[index] = { ...target, coupon_id: null };
      updateCoupons(nextCoupons);
      return;
    }

    try {
      const coupon = await getCouponById(couponId);
      nextCoupons[index] = {
        ...target,
        coupon_id: coupon.id,
        coupon: coupon as AdminCouponItem,
        coupon_title: coupon.name,
        coupon_type: coupon.type,
        discount_rule: formatCouponRule(coupon),
        valid_from: coupon.valid_from,
        expires_at: coupon.expires_at,
      };
      const optionExists = couponOptions.value.some((option) => option.value === coupon.id);
      if (!optionExists) {
        couponOptions.value = [
          ...couponOptions.value,
          {
            label: buildCouponOptionLabel(coupon),
            value: coupon.id,
          },
        ];
      }
      updateCoupons(nextCoupons);
    } catch {
      window['$message'].error('卡券信息加载失败');
    }
  }

  function removeCoupon(index: number) {
    const nextCoupons = [...props.coupons];
    const target = nextCoupons[index];
    if (!target) return;

    if (target.id) {
      nextCoupons[index] = { ...target, _destroy: true, is_active: false };
    } else {
      nextCoupons.splice(index, 1);
    }
    updateCoupons(nextCoupons);
  }

  function moveCoupon(index: number, offset: number) {
    const visibleIndex = visibleCoupons.value.findIndex((item) => item.index === index);
    if (visibleIndex < 0) return;

    const nextVisible = visibleCoupons.value[visibleIndex + offset];
    if (!nextVisible) return;

    const nextCoupons = [...props.coupons];
    const [target] = nextCoupons.splice(index, 1);
    nextCoupons.splice(nextVisible.index, 0, target);
    updateCoupons(nextCoupons);
  }

  function formatCouponValidity(coupon: ActivityCouponFormItem) {
    if (coupon.valid_from && coupon.expires_at) {
      return `${coupon.valid_from} 至 ${coupon.expires_at}`;
    }
    return '按卡券模板配置';
  }

  function formatCouponType(coupon: ActivityCouponFormItem) {
    const labels: Record<string, string> = {
      threshold_amount_off: '满减券',
      amount_off: '立减券',
      percentage_off: '折扣券',
    };
    return coupon.coupon_type
      ? labels[coupon.coupon_type] || coupon.coupon_type
      : '保存后由卡券模板返回';
  }

  function setCouponOptions(options: { label: string; value: number }[]) {
    const selectedOptions = couponOptions.value.filter((option) =>
      props.coupons.some(
        (coupon) => !coupon._destroy && Number(coupon.coupon_id) === option.value
      )
    );
    couponOptions.value = mergeOptions(selectedOptions, options);
  }

  function mergeCouponOptions(options: { label: string; value: number }[]) {
    couponOptions.value = mergeOptions(couponOptions.value, options);
  }

  function mergeOptions(
    baseOptions: { label: string; value: number }[],
    options: { label: string; value: number }[]
  ) {
    const nextOptions = [...baseOptions];
    options.forEach((option) => {
      const index = nextOptions.findIndex((item) => item.value === option.value);
      if (index >= 0) {
        nextOptions[index] = option;
      } else {
        nextOptions.push(option);
      }
    });
    return nextOptions;
  }

  function buildCouponOptionLabel(coupon: AdminCouponItem) {
    return `${coupon.name} · ${
      couponTypeLabels[coupon.type] || coupon.type
    } · ${formatCouponRule(coupon)} · ${formatCouponScope(coupon)}`;
  }
</script>

<style scoped lang="less">
  .activity-coupon-config {
    width: 100%;
  }

  .activity-coupon-config__item {
    border-radius: 6px;
  }
</style>
