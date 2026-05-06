<template>
  <n-modal
    :show="showModal"
    :show-icon="false"
    preset="dialog"
    title="批量创建座位"
    @update:show="(val: boolean) => emit('update:show', val)"
  >
    <n-scrollbar style="max-height: 60vh">
      <n-space vertical size="large">
        <div v-for="(zone, index) in zones" :key="index">
          <n-card size="small" :bordered="true">
            <template #header-extra>
              <n-button text type="error" @click="removeZone(index)">
                <template #icon>
                  <n-icon><DeleteOutlined /></n-icon>
                </template>
                删除
              </n-button>
            </template>
            <n-space vertical>
              <n-grid :cols="3" :x-gap="12">
                <n-gi>
                  <n-form-item label="分区">
                    <n-select
                      v-model:value="zone.zone"
                      :options="zoneOptions"
                      placeholder="选择分区"
                    />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="行数">
                    <n-input-number
                      v-model:value="zone.rows"
                      :min="1"
                      style="width: 100%"
                    />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="列数">
                    <n-input-number
                      v-model:value="zone.cols"
                      :min="1"
                      style="width: 100%"
                    />
                  </n-form-item>
                </n-gi>
              </n-grid>
              <n-grid :cols="4" :x-gap="12">
                <n-gi>
                  <n-form-item label="编号前缀">
                    <n-input
                      v-model:value="zone.prefix"
                      placeholder="如: Q"
                      :maxlength="5"
                      show-count
                    />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="起始编号">
                    <n-input-number
                      v-model:value="zone.start_number"
                      :min="1"
                      style="width: 100%"
                    />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="每小时价格">
                    <n-input-number
                      v-model:value="zone.price_per_hour"
                      :min="0"
                      :precision="2"
                      style="width: 100%"
                    />
                  </n-form-item>
                </n-gi>
                <n-gi>
                  <n-form-item label="楼层">
                    <n-input-number
                      v-model:value="zone.floor"
                      :min="1"
                      style="width: 100%"
                    />
                  </n-form-item>
                </n-gi>
              </n-grid>
            </n-space>
          </n-card>
        </div>
      </n-space>
    </n-scrollbar>

    <n-space vertical size="large" style="margin-top: 16px">
      <n-button dashed block @click="addZone">
        <template #icon>
          <n-icon><PlusOutlined /></n-icon>
        </template>
        添加分区
      </n-button>

      <n-alert type="info" :bordered="false">
        共生成 {{ totalSeats }} 个座位
      </n-alert>
    </n-space>

    <template #action>
      <n-space>
        <n-button @click="() => emit('update:show', false)">取消</n-button>
        <n-button
          type="info"
          :loading="formBtnLoading"
          :disabled="!formValid || totalSeats === 0"
          @click="confirmForm"
        >
          确定
        </n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script lang="ts" setup>
  import { computed, reactive, ref, watch } from 'vue';
  import { DeleteOutlined, PlusOutlined } from '@vicons/antd';
  import {
    bulkCreateSeats,
    type SeatBulkZoneConfig,
  } from '@/api/seat';

  interface ZoneConfig {
    zone: 'quiet' | 'keyboard' | 'vip';
    rows: number;
    cols: number;
    prefix: string;
    start_number: number;
    price_per_hour: number;
    floor: number;
  }

  const props = defineProps<{
    show: boolean;
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

  const formBtnLoading = ref(false);

  const defaultZone: ZoneConfig = {
    zone: 'quiet',
    rows: 1,
    cols: 1,
    prefix: '',
    start_number: 1,
    price_per_hour: 0,
    floor: 3,
  };

  const zones = reactive<ZoneConfig[]>([{ ...defaultZone }]);

  const zoneOptions = [
    { label: '静音区', value: 'quiet' },
    { label: '键鼠区', value: 'keyboard' },
    { label: 'VIP区', value: 'vip' },
  ];

  const totalSeats = computed(() => {
    return zones.reduce((sum, zone) => sum + zone.rows * zone.cols, 0);
  });

  const formValid = computed(() => {
    return zones.every(
      (zone) =>
        zone.zone &&
        zone.rows > 0 &&
        zone.cols > 0 &&
        zone.prefix.trim() !== '' &&
        zone.price_per_hour >= 0 &&
        zone.floor >= 1
    );
  });

  watch(
    () => props.show,
    (val) => {
      if (val) {
        zones.length = 0;
        zones.push({ ...defaultZone });
      }
    },
  );

  function addZone() {
    zones.push({ ...defaultZone });
  }

  function removeZone(index: number) {
    if (zones.length > 1) {
      zones.splice(index, 1);
    } else {
      window['$message'].warning('至少需要保留一个分区');
    }
  }

  function confirmForm() {
    if (!formValid.value || totalSeats.value === 0) {
      return;
    }

    formBtnLoading.value = true;
    try {
      const seatConfigs: SeatBulkZoneConfig[] = zones.map((zone) => ({
        zone: zone.zone,
        rows: zone.rows,
        cols: zone.cols,
        prefix: zone.prefix,
        start_number: zone.start_number,
        price_per_hour: zone.price_per_hour,
        floor: zone.floor,
      }));

      bulkCreateSeats(props.roomId, { seats: seatConfigs })
        .then(() => {
          window['$message'].success(`成功创建 ${totalSeats.value} 个座位`);
          emit('update:show', false);
          emit('success');
        })
        .catch(() => {
          window['$message'].error('创建失败');
        })
        .finally(() => {
          formBtnLoading.value = false;
        });
    } catch {
      window['$message'].error('创建失败');
      formBtnLoading.value = false;
    }
  }
</script>
