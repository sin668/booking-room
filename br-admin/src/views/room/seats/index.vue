<template>
  <n-flex vertical>
    <n-card :bordered="false">
      <n-space align="center">
        <n-breadcrumb>
          <n-breadcrumb-item>门店列表</n-breadcrumb-item>
          <n-breadcrumb-item>座位管理</n-breadcrumb-item>
        </n-breadcrumb>
        <n-button text @click="router.back()">
          <template #icon>
            <n-icon><ArrowLeftOutlined /></n-icon>
          </template>
          返回
        </n-button>
        <n-text depth="3">|</n-text>
        <n-text strong>{{ roomName }}</n-text>
      </n-space>
    </n-card>
    <n-card :bordered="false">
      <BasicForm @register="register" @submit="handleSubmit" @reset="handleReset" />
    </n-card>
    <n-card :bordered="false">
      <BasicTable
        :columns="columns"
        :request="loadDataTable"
        :row-key="(row: SeatItem) => row.id"
        ref="actionRef"
        :actionColumn="actionColumn"
        :scroll-x="1100"
        :striped="true"
      >
        <template #tableTitle>
          <n-space>
            <n-button v-permission="{ action: ['seat:create'] }" type="primary" @click="addTable">
              <template #icon>
                <n-icon><PlusOutlined /></n-icon>
              </template>
              新建座位
            </n-button>
            <n-button
              v-permission="{ action: ['seat:bulk_create'] }"
              type="info"
              @click="handleBulkCreate"
            >
              <template #icon>
                <n-icon><PlusOutlined /></n-icon>
              </template>
              批量创建座位
            </n-button>
          </n-space>
        </template>
      </BasicTable>

      <SeatEditModal
        v-model:show="showModal"
        :editData="editData"
        :roomId="roomId"
        @success="handleSuccess"
      />

      <SeatBulkCreateModal v-model:show="showBulkModal" :roomId="roomId" @success="handleSuccess" />
    </n-card>
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, reactive, ref, computed } from 'vue';
  import { useRouter, useRoute } from 'vue-router';
  import { NTag, NButton } from 'naive-ui';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, FormSchema, useForm } from '@/components/Form/index';
  import { PlusOutlined, ArrowLeftOutlined } from '@vicons/antd';
  import { getSeatList, deleteSeat, toggleSeatStatus, type SeatItem } from '@/api/seat';
  import SeatEditModal from './components/SeatEditModal.vue';
  import SeatBulkCreateModal from './components/SeatBulkCreateModal.vue';

  const router = useRouter();
  const route = useRoute();

  const roomId = computed(() => Number(route.params.id));
  const roomName = ref('座位管理');

  const schemas: FormSchema[] = [
    {
      field: 'zone',
      component: 'NSelect',
      label: '分区',
      componentProps: {
        placeholder: '全部',
        options: [
          { label: '全部', value: '' },
          { label: '静音区', value: 'quiet' },
          { label: '键鼠区', value: 'keyboard' },
          { label: 'VIP区', value: 'vip' },
        ],
      },
    },
    {
      field: 'status',
      component: 'NSelect',
      label: '状态',
      componentProps: {
        placeholder: '全部',
        options: [
          { label: '全部', value: '' },
          { label: '可用', value: 'available' },
          { label: '维护中', value: 'maintenance' },
        ],
      },
    },
  ];

  const actionRef = ref();
  const showModal = ref(false);
  const showBulkModal = ref(false);
  const editData = ref<SeatItem | null>(null);

  const [register, { getFieldsValue }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas,
  });

  const columns = [
    {
      title: '座位编号',
      key: 'seat_number',
      width: 100,
    },
    {
      title: '分区',
      key: 'zone',
      render(row: SeatItem) {
        const zoneMap = {
          quiet: { type: 'info', text: '静音区' },
          keyboard: { type: 'warning', text: '键鼠区' },
          vip: { type: 'success', text: 'VIP区' },
        };
        const config = zoneMap[row.zone];
        return h(NTag, { type: config.type }, { default: () => config.text });
      },
    },
    {
      title: '位置',
      key: 'position',
      width: 80,
    },
    {
      title: '楼层',
      key: 'floor',
      width: 70,
    },
    {
      title: '每小时价格',
      key: 'price_per_hour',
      width: 100,
      render(row: SeatItem) {
        return `¥${row.price_per_hour}`;
      },
    },
    {
      title: '状态',
      key: 'status',
      render(row: SeatItem) {
        const statusMap = {
          available: { type: 'success', text: '可用' },
          maintenance: { type: 'error', text: '维护中' },
        };
        const config = statusMap[row.status];
        return h(NTag, { type: config.type }, { default: () => config.text });
      },
    },
    {
      title: '行列位置',
      key: 'row_col',
      width: 80,
      render(row: SeatItem) {
        return `${row.row}行${row.col}列`;
      },
    },
  ];

  const loadDataTable = async (res: any) => {
    const formValues = getFieldsValue();
    const queryParams: Record<string, any> = { ...formValues, ...res };

    // Remove empty filters
    if (queryParams.zone === '' || queryParams.zone === undefined) {
      delete queryParams.zone;
    }
    if (queryParams.status === '' || queryParams.status === undefined) {
      delete queryParams.status;
    }

    const result = await getSeatList(roomId.value, queryParams);
    return {
      list: result,
      itemCount: result.length,
      pageCount: 1,
      page: 1,
    };
  };

  const actionColumn = reactive({
    width: 250,
    title: '操作',
    key: 'action',
    fixed: 'right',
    render(record: SeatItem) {
      return h(TableAction as any, {
        style: 'button',
        actions: [
          {
            label: '编辑',
            onClick: handleEdit.bind(null, record),
            auth: ['seat:update'],
          },
        ],
        dropDownActions: [
          {
            label: '删除',
            key: 'delete',
            auth: ['seat:delete'],
          },
          {
            label: record.status === 'available' ? '设为维护中' : '设为可用',
            key: 'toggleStatus',
            auth: ['seat:status'],
          },
        ],
        select: (key: string) => {
          if (key === 'delete') {
            handleDelete(record);
          } else if (key === 'toggleStatus') {
            handleToggleStatus(record);
          }
        },
      });
    },
  });

  function addTable() {
    editData.value = null;
    showModal.value = true;
  }

  function handleBulkCreate() {
    showBulkModal.value = true;
  }

  function handleEdit(record: SeatItem) {
    editData.value = record;
    showModal.value = true;
  }

  function handleDelete(record: SeatItem) {
    window['$dialog'].warning({
      title: '确认删除',
      content: `确定要删除座位「${record.seat_number}」吗？`,
      positiveText: '确认删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteSeat(record.id);
          window['$message'].success('删除成功');
          reloadTable();
        } catch {
          window['$message'].error('删除失败');
        }
      },
    });
  }

  function handleToggleStatus(record: SeatItem) {
    const newStatus = record.status === 'available' ? 'maintenance' : 'available';
    window['$dialog'].warning({
      title: '确认操作',
      content: `确定要将座位「${record.seat_number}」状态改为${
        newStatus === 'available' ? '可用' : '维护中'
      }吗？`,
      positiveText: '确认',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await toggleSeatStatus(record.id, newStatus);
          window['$message'].success('状态更新成功');
          reloadTable();
        } catch {
          window['$message'].error('操作失败');
        }
      },
    });
  }

  function handleSuccess() {
    showModal.value = false;
    showBulkModal.value = false;
    reloadTable();
  }

  function handleSubmit() {
    reloadTable();
  }

  function handleReset() {
    reloadTable();
  }

  function reloadTable() {
    actionRef.value.reload();
  }
</script>
