<template>
  <n-flex vertical>
    <n-card :bordered="false">
      <BasicForm @register="register" @submit="handleSubmit" @reset="handleReset" />
    </n-card>
    <n-card :bordered="false">
      <BasicTable
        :columns="columns"
        :request="loadDataTable"
        :row-key="(row: BookingItem) => row.id"
        ref="actionRef"
        :actionColumn="actionColumn"
        :scroll-x="1300"
        :striped="true"
      />
    </n-card>
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, reactive, ref, onMounted } from 'vue';
  import { NTag } from 'naive-ui';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, FormSchema, useForm } from '@/components/Form/index';
  import { getBookingList, cancelBooking, type BookingItem } from '@/api/booking';
  import { getRoomList, type RoomItem } from '@/api/room';

  const roomOptions = ref<{ label: string; value: number }[]>([]);

  const schemas: FormSchema[] = [
    {
      field: 'status',
      component: 'NSelect',
      label: '状态',
      componentProps: {
        placeholder: '全部',
        options: [
          { label: '全部', value: '' },
          { label: '已确认', value: 'confirmed' },
          { label: '已取消', value: 'cancelled' },
        ],
      },
    },
    {
      field: 'room_id',
      component: 'NSelect',
      label: '自习室',
      componentProps: {
        placeholder: '全部',
        options: roomOptions,
      },
    },
    {
      field: 'dateRange',
      component: 'NDatePicker',
      label: '预约日期',
      componentProps: {
        type: 'daterange',
        clearable: true,
        placeholder: '选择日期范围',
      },
    },
  ];

  const columns = [
    { title: 'ID', key: 'id', width: 60 },
    {
      title: '用户ID',
      key: 'user_id',
      width: 120,
      ellipsis: { tooltip: true },
      render(record: BookingItem) {
        return record.user_id.slice(0, 8) + '...';
      },
    },
    {
      title: '自习室名称',
      key: 'room_name',
      width: 140,
      render(record: BookingItem) {
        return record.room?.name || '-';
      },
    },
    {
      title: '座位编号',
      key: 'seat_number',
      width: 100,
      render(record: BookingItem) {
        return record.seat?.seat_number || '-';
      },
    },
    { title: '预约日期', key: 'date', width: 110 },
    {
      title: '时段',
      key: 'time_range',
      width: 160,
      render(record: BookingItem) {
        return `${record.start_time}~${record.end_time}`;
      },
    },
    {
      title: '金额',
      key: 'total_price',
      width: 90,
      render(record: BookingItem) {
        return `¥${record.total_price}`;
      },
    },
    {
      title: '状态',
      key: 'status',
      width: 90,
      render(record: BookingItem) {
        return h(
          NTag,
          { type: record.status === 'confirmed' ? 'success' : 'error' },
          { default: () => (record.status === 'confirmed' ? '已确认' : '已取消') }
        );
      },
    },
    { title: '创建时间', key: 'created_at', width: 170 },
  ];

  function formatTimestamp(ts: number | null): string | undefined {
    if (!ts) return undefined;
    const d = new Date(ts);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
      d.getDate()
    ).padStart(2, '0')}`;
  }

  const actionRef = ref();

  const [register, { getFieldsValue }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas,
  });

  async function fetchRoomOptions() {
    try {
      const result = await getRoomList({ page_size: 999 });
      roomOptions.value = [
        { label: '全部', value: 0 },
        ...result.items.map((room: RoomItem) => ({ label: room.name, value: room.id })),
      ];
    } catch {
      // ignore - room options will remain empty
    }
  }

  onMounted(() => {
    fetchRoomOptions();
  });

  const loadDataTable = async (res: any) => {
    const formValues = getFieldsValue();
    const queryParams: Record<string, any> = { ...formValues, ...res };

    // Convert pageSize -> page_size
    queryParams.page_size = queryParams.pageSize;
    delete queryParams.pageSize;

    // Convert dateRange -> date_start / date_end
    if (queryParams.dateRange && queryParams.dateRange[0] && queryParams.dateRange[1]) {
      queryParams.date_start = formatTimestamp(queryParams.dateRange[0]);
      queryParams.date_end = formatTimestamp(queryParams.dateRange[1]);
    }
    delete queryParams.dateRange;

    // Remove empty values
    if (!queryParams.status) delete queryParams.status;
    if (!queryParams.room_id) delete queryParams.room_id;

    const result = await getBookingList(queryParams);
    return {
      list: result.items,
      itemCount: result.total,
      pageCount: Math.ceil(result.total / queryParams.page_size) || 1,
      page: result.page,
    };
  };

  function handleCancel(record: BookingItem) {
    window['$dialog'].warning({
      title: '确认取消',
      content: '确定要取消该订单吗？取消后不可恢复',
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
          if (key === 'cancel') {
            handleCancel(record);
          }
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
