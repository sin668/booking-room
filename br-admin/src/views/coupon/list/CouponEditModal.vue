<template>
  <n-modal
    v-model:show="showModal"
    :show-icon="false"
    preset="dialog"
    :title="editData ? '编辑卡券' : '新建卡券'"
    style="width: 640px"
  >
    <n-form
      ref="formRef"
      :model="formValues"
      :rules="rules"
      label-placement="left"
      :label-width="92"
    >
      <n-form-item label="卡券名称" path="name">
        <n-input
          v-model:value="formValues.name"
          placeholder="请输入卡券名称"
          :maxlength="100"
          show-count
        />
      </n-form-item>
      <n-form-item label="描述" path="description">
        <n-input
          v-model:value="formValues.description"
          type="textarea"
          placeholder="请输入描述"
          :rows="2"
        />
      </n-form-item>
      <n-form-item label="类型" path="type">
        <n-select
          v-model:value="formValues.type"
          :options="typeOptions"
          @update:value="handleTypeChange"
        />
      </n-form-item>
      <n-form-item v-if="needsDiscountAmount" label="优惠金额" path="discount_amount">
        <n-input-number
          v-model:value="formValues.discount_amount"
          :min="0"
          :precision="2"
          style="width: 100%"
        />
      </n-form-item>
      <n-form-item
        v-if="formValues.type === 'threshold_amount_off'"
        label="门槛金额"
        path="min_order_amount"
      >
        <n-input-number
          v-model:value="formValues.min_order_amount"
          :min="0"
          :precision="2"
          style="width: 100%"
        />
      </n-form-item>
      <n-form-item
        v-if="formValues.type === 'percentage_off'"
        label="折扣比例"
        path="discount_percent"
      >
        <n-input-number
          v-model:value="formValues.discount_percent"
          :min="1"
          :max="99"
          :precision="0"
          style="width: 100%"
        />
      </n-form-item>
      <n-form-item label="适用范围" path="scope">
        <n-select v-model:value="formValues.scope" :options="scopeOptions" />
      </n-form-item>
      <n-form-item v-if="formValues.scope === 'seat_zone'" label="座位区域" path="seat_zone">
        <n-input v-model:value="formValues.seat_zone" placeholder="请输入座位区域编码" />
      </n-form-item>
      <n-form-item label="有效期" path="date_range">
        <n-date-picker
          v-model:formatted-value="dateRange"
          type="datetimerange"
          value-format="yyyy-MM-dd HH:mm:ss"
          clearable
          style="width: 100%"
        />
      </n-form-item>
      <n-form-item label="启用状态">
        <n-switch v-model:value="formValues.is_active">
          <template #checked>启用</template>
          <template #unchecked>停用</template>
        </n-switch>
      </n-form-item>
    </n-form>

    <template #action>
      <n-space>
        <n-button @click="showModal = false">取消</n-button>
        <n-button type="primary" :loading="formBtnLoading" @click="confirmForm">确定</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
  import { computed, reactive, ref, watch } from 'vue';
  import type { FormInst, FormRules } from 'naive-ui';
  import {
    createCoupon,
    updateCoupon,
    type AdminCouponCreateParams,
    type AdminCouponItem,
  } from '@/api/coupon';
  import { isCouponExpired } from './columns';

  const props = defineProps<{
    show: boolean;
    editData: AdminCouponItem | null;
  }>();

  const emit = defineEmits<{
    (e: 'update:show', value: boolean): void;
    (e: 'success'): void;
  }>();

  const showModal = computed({
    get: () => props.show,
    set: (value: boolean) => emit('update:show', value),
  });

  const typeOptions = [
    { label: '满减券', value: 'threshold_amount_off' },
    { label: '立减券', value: 'amount_off' },
    { label: '折扣券', value: 'percentage_off' },
  ];

  const scopeOptions = [
    { label: '全场通用', value: 'all' },
    { label: '首次预约', value: 'first_booking' },
    { label: 'VIP专享', value: 'vip_only' },
    { label: '指定区域', value: 'seat_zone' },
  ];

  const defaultValues: AdminCouponCreateParams = {
    name: '',
    description: '',
    type: 'threshold_amount_off',
    discount_amount: null,
    discount_percent: null,
    min_order_amount: 0,
    scope: 'all',
    seat_zone: null,
    valid_from: '',
    expires_at: '',
    is_active: true,
  };

  const formRef = ref<FormInst | null>(null);
  const formBtnLoading = ref(false);
  const dateRange = ref<[string, string] | null>(null);
  const formValues = reactive<AdminCouponCreateParams>({ ...defaultValues });

  const needsDiscountAmount = computed(() =>
    ['threshold_amount_off', 'amount_off'].includes(formValues.type)
  );

  const rules: FormRules = {
    name: { required: true, trigger: ['blur', 'input'], message: '请输入卡券名称' },
    type: { required: true, trigger: ['change'], message: '请选择卡券类型' },
    scope: { required: true, trigger: ['change'], message: '请选择适用范围' },
    date_range: {
      validator() {
        return Boolean(dateRange.value?.[0] && dateRange.value?.[1]);
      },
      trigger: ['change'],
      message: '请选择有效期',
    },
    discount_amount: {
      validator() {
        return !needsDiscountAmount.value || Number(formValues.discount_amount) > 0;
      },
      trigger: ['blur', 'change'],
      message: '请输入大于0的优惠金额',
    },
    min_order_amount: {
      validator() {
        return (
          formValues.type !== 'threshold_amount_off' || Number(formValues.min_order_amount) > 0
        );
      },
      trigger: ['blur', 'change'],
      message: '满减券门槛金额必须大于0',
    },
    discount_percent: {
      validator() {
        return formValues.type !== 'percentage_off' || Number(formValues.discount_percent) > 0;
      },
      trigger: ['blur', 'change'],
      message: '请输入折扣比例',
    },
    seat_zone: {
      validator() {
        return formValues.scope !== 'seat_zone' || Boolean(formValues.seat_zone);
      },
      trigger: ['blur', 'input'],
      message: '请输入座位区域',
    },
  };

  watch(
    () => props.show,
    (visible) => {
      if (!visible) return;
      Object.assign(formValues, { ...defaultValues });
      dateRange.value = null;
      if (props.editData) {
        Object.assign(formValues, {
          name: props.editData.name,
          description: props.editData.description || '',
          type: props.editData.type,
          discount_amount:
            props.editData.discount_amount === null ? null : Number(props.editData.discount_amount),
          discount_percent: props.editData.discount_percent,
          min_order_amount: Number(props.editData.min_order_amount || 0),
          scope: props.editData.scope,
          seat_zone: props.editData.seat_zone,
          is_active: props.editData.is_active,
        });
        dateRange.value = [
          props.editData.valid_from.slice(0, 19).replace('T', ' '),
          props.editData.expires_at.slice(0, 19).replace('T', ' '),
        ];
      }
    }
  );

  // 编辑过期卡券时，延长有效期超过当前时间后自动恢复启用状态
  watch(dateRange, (range) => {
    if (!props.editData || !range?.[1]) return;
    const newExpiresAt = new Date(range[1]);
    if (newExpiresAt >= new Date() && isCouponExpired(props.editData)) {
      formValues.is_active = true;
    }
  });

  function handleTypeChange() {
    formValues.discount_amount = null;
    formValues.discount_percent = null;
    if (formValues.type !== 'threshold_amount_off') {
      formValues.min_order_amount = 0;
    }
  }

  function buildPayload() {
    formValues.valid_from = dateRange.value?.[0] || '';
    formValues.expires_at = dateRange.value?.[1] || '';
    return {
      ...formValues,
      seat_zone: formValues.scope === 'seat_zone' ? formValues.seat_zone : null,
      discount_amount: needsDiscountAmount.value ? formValues.discount_amount : null,
      discount_percent: formValues.type === 'percentage_off' ? formValues.discount_percent : null,
    };
  }

  function confirmForm() {
    formBtnLoading.value = true;
    formRef.value?.validate(async (errors) => {
      if (!errors) {
        try {
          const payload = buildPayload();
          if (props.editData) {
            await updateCoupon(props.editData.id, payload);
          } else {
            await createCoupon(payload);
          }
          window['$message'].success('操作成功');
          showModal.value = false;
          emit('success');
        } catch (error) {
          const message = error instanceof Error && error.message ? error.message : '操作失败';
          window['$message'].error(message);
        }
      }
      formBtnLoading.value = false;
    });
  }
</script>
