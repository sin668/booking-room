<template>
  <n-modal
    :show="showModal"
    :show-icon="false"
    preset="dialog"
    :title="editData ? '编辑座位' : '新建座位'"
    @update:show="(val: boolean) => emit('update:show', val)"
  >
    <n-form
      :model="formValues"
      :rules="rules"
      ref="formRef"
      label-placement="left"
      :label-width="100"
      class="py-4"
    >
      <n-form-item label="座位编号" path="seat_number">
        <n-input
          placeholder="请输入座位编号"
          v-model:value="formValues.seat_number"
          :maxlength="10"
          show-count
        />
      </n-form-item>

      <n-form-item label="分区" path="zone">
        <n-select
          v-model:value="formValues.zone"
          :options="zoneOptions"
          placeholder="请选择分区"
        />
      </n-form-item>

      <n-form-item label="位置" path="position">
        <n-select
          v-model:value="formValues.position"
          :options="positionOptions"
          placeholder="请选择位置"
          clearable
        />
      </n-form-item>

      <n-form-item label="楼层" path="floor">
        <n-input-number
          v-model:value="formValues.floor"
          :min="1"
          style="width: 100%"
        />
      </n-form-item>

      <n-form-item label="每小时价格" path="price_per_hour">
        <n-input-number
          v-model:value="formValues.price_per_hour"
          :min="0"
          :precision="2"
          style="width: 100%"
        />
      </n-form-item>

      <n-form-item label="行号" path="row">
        <n-input-number
          v-model:value="formValues.row"
          :min="0"
          style="width: 100%"
        />
      </n-form-item>

      <n-form-item label="列号" path="col">
        <n-input-number
          v-model:value="formValues.col"
          :min="0"
          style="width: 100%"
        />
      </n-form-item>
    </n-form>

    <template #action>
      <n-space>
        <n-button @click="() => emit('update:show', false)">取消</n-button>
        <n-button type="info" :loading="formBtnLoading" @click="confirmForm">确定</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script lang="ts" setup>
  import { computed, reactive, ref, watch } from 'vue';
  import type { FormRules, FormInst } from 'naive-ui';
  import {
    createSeat,
    updateSeat,
    type SeatFormParams,
    type SeatItem,
  } from '@/api/seat';

  const props = defineProps<{
    show: boolean;
    editData: SeatItem | null;
    roomId: number;
  }>();

  const emit = defineEmits<{
    (e: 'update:show', value: boolean): void;
    (e: 'success'): void;
  }>();

  const showModal = computed({
    get: () => props.show,
    set: (val: boolean) => emit('update:show', val),
  });

  const formRef = ref<FormInst | null>(null);
  const formBtnLoading = ref(false);

  const defaultValues: SeatFormParams = {
    seat_number: '',
    zone: 'quiet',
    position: null,
    floor: 3,
    price_per_hour: 0,
    row: 1,
    col: 1,
  };

  const formValues = reactive<SeatFormParams>({ ...defaultValues });

  const zoneOptions = [
    { label: '静音区', value: 'quiet' },
    { label: '键鼠区', value: 'keyboard' },
    { label: 'VIP区', value: 'vip' },
  ];

  const positionOptions = [
    { label: '靠窗', value: '靠窗' },
    { label: '中间', value: '中间' },
    { label: '独立', value: '独立' },
  ];

  const rules: FormRules = {
    seat_number: {
      required: true,
      trigger: ['blur', 'input'],
      message: '请输入座位编号',
    },
    zone: {
      required: true,
      trigger: ['blur', 'change'],
      message: '请选择分区',
    },
    price_per_hour: {
      required: true,
      trigger: ['blur', 'change'],
      message: '请输入每小时价格',
    },
    row: {
      required: true,
      trigger: ['blur', 'change'],
      message: '请输入行号',
    },
    col: {
      required: true,
      trigger: ['blur', 'change'],
      message: '请输入列号',
    },
  };

  watch(
    () => props.show,
    (val) => {
      if (!val) return;
      if (props.editData) {
        formValues.seat_number = props.editData.seat_number;
        formValues.zone = props.editData.zone;
        formValues.position = props.editData.position;
        formValues.floor = props.editData.floor;
        formValues.price_per_hour = props.editData.price_per_hour;
        formValues.row = props.editData.row;
        formValues.col = props.editData.col;
      } else {
        Object.assign(formValues, { ...defaultValues });
      }
    },
  );

  function confirmForm() {
    formBtnLoading.value = true;
    formRef.value?.validate(async (errors) => {
      if (!errors) {
        try {
          if (props.editData) {
            await updateSeat(props.editData.id, formValues);
          } else {
            await createSeat(props.roomId, formValues);
          }
          window['$message'].success('操作成功');
          emit('update:show', false);
          emit('success');
        } catch {
          window['$message'].error('操作失败');
        }
      }
      formBtnLoading.value = false;
    });
  }
</script>
