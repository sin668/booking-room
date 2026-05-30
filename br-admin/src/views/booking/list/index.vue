<template>
  <n-flex vertical>
    <n-card :bordered="false">
      <BasicForm @register="register" @submit="handleSubmit" @reset="handleReset" />
    </n-card>
    <n-card :bordered="false">
      <BasicTable
        ref="actionRef"
        :columns="columns"
        :request="loadDataTable"
        :row-key="(row: BookingItem) => row.id"
        :actionColumn="actionColumn"
        :scroll-x="1300"
        :striped="true"
      />
    </n-card>
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, onMounted, reactive, ref } from 'vue';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, useForm } from '@/components/Form/index';
  import { cancelBooking, getBookingList, type BookingItem } from '@/api/booking';
  import { useAdminBusiness } from '@/store/modules/adminBusiness';
  import { toBasicTableResult } from '@/api/contracts/admin';
  import { normalizeDateRange } from '@/views/business/shared/formSchemaBuilders';
  import { buildBookingSearchSchemas, buildBookingTableColumns } from './builders';

  const actionRef = ref();
  const adminBusinessStore = useAdminBusiness();
  const columns = buildBookingTableColumns();

  const [register, { getFieldsValue, setProps }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas: buildBookingSearchSchemas([]),
  });

  onMounted(async () => {
    try {
      const roomOptions = await adminBusinessStore.loadRoomOptions();
      await setProps({ schemas: buildBookingSearchSchemas(roomOptions) });
    } catch {
      await setProps({ schemas: buildBookingSearchSchemas([]) });
    }
  });

  const loadDataTable = async (res: any) => {
    const formValues = getFieldsValue();
    const queryParams: Record<string, any> = { ...formValues, ...res };

    queryParams.page_size = queryParams.pageSize;
    delete queryParams.pageSize;

    Object.assign(queryParams, normalizeDateRange(queryParams.dateRange));
    delete queryParams.dateRange;

    if (!queryParams.status) delete queryParams.status;
    if (!queryParams.room_id) delete queryParams.room_id;

    const result = await getBookingList(queryParams);
    return toBasicTableResult(result);
  };

  function handleCancel(record: BookingItem) {
    window['$dialog'].warning({
      title: '确认取消',
      content: '确定要取消该订单吗？取消后不可恢复。',
      positiveText: '确认取消',
      negativeText: '返回',
      onPositiveClick: async () => {
        try {
          await cancelBooking(record.id);
          window['$message'].success('订单已取消');
          actionRef.value?.reload();
        } catch {
          window['$message'].error('取消失败');
        }
      },
    });
  }

  function handleView(record: BookingItem) {
    window['$dialog'].info({
      title: '订单详情',
      content: `订单 #${record.id}：${record.room?.name || '-'} / ${
        record.seat?.seat_number || '-'
      } / ${record.date} ${record.start_time}~${record.end_time}`,
      positiveText: '确定',
    });
  }

  const actionColumn = reactive({
    width: 150,
    title: '操作',
    key: 'action',
    fixed: 'right' as const,
    render(record: BookingItem) {
      const dropDownActions: any[] = [];
      if (record.status === 'confirmed') {
        dropDownActions.push({
          label: '取消',
          key: 'cancel',
          auth: ['booking:cancel'],
        });
      }
      return h(TableAction as any, {
        style: 'button',
        actions: [
          {
            label: '查看',
            onClick: handleView.bind(null, record),
            auth: ['booking:view'],
          },
        ],
        dropDownActions,
        select: (key: string) => {
          if (key === 'cancel') handleCancel(record);
        },
      });
    },
  });

  function handleSubmit() {
    actionRef.value?.reload();
  }

  function handleReset() {
    actionRef.value?.reload();
  }
</script>
