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
        :row-key="(row: RoomItem) => row.id"
        :actionColumn="actionColumn"
        :scroll-x="1200"
        :striped="true"
      >
        <template #tableTitle>
          <n-button v-permission="{ action: ['room:create'] }" type="primary" @click="addTable">
            <template #icon>
              <n-icon><PlusOutlined /></n-icon>
            </template>
            新建自习室
          </n-button>
        </template>
      </BasicTable>

      <RoomEditModal v-model:show="showModal" :editData="editData" @success="handleSuccess" />
    </n-card>
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, reactive, ref } from 'vue';
  import { useRouter } from 'vue-router';
  import { PlusOutlined } from '@vicons/antd';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, useForm } from '@/components/Form/index';
  import { deleteRoom, getRoomList, toggleRoomStatus, type RoomItem } from '@/api/room';
  import { toBasicTableResult } from '@/api/contracts/admin';
  import { buildRoomSearchSchemas, buildRoomTableColumns } from './builders';
  import RoomEditModal from './RoomEditModal.vue';

  const router = useRouter();
  const actionRef = ref();
  const showModal = ref(false);
  const editData = ref<RoomItem | null>(null);
  const columns = buildRoomTableColumns();

  const [register, { getFieldsValue }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas: buildRoomSearchSchemas(),
  });

  const loadDataTable = async (res: any) => {
    const formValues = getFieldsValue();
    const queryParams: Record<string, any> = { ...formValues, ...res };

    queryParams.page_size = queryParams.pageSize;
    delete queryParams.pageSize;

    if (!queryParams.status) delete queryParams.status;

    const result = await getRoomList(queryParams);
    return toBasicTableResult(result);
  };

  const actionColumn = reactive({
    width: 250,
    title: '操作',
    key: 'action',
    fixed: 'right',
    render(record: RoomItem) {
      return h(TableAction as any, {
        style: 'button',
        actions: [
          {
            label: '编辑',
            onClick: handleEdit.bind(null, record),
            auth: ['room:update'],
          },
          {
            label: '删除',
            onClick: handleDelete.bind(null, record),
            auth: ['room:delete'],
          },
          {
            label: '管理座位',
            onClick: handleManageSeats.bind(null, record),
            auth: ['seat:view'],
          },
        ],
        dropDownActions: [
          {
            label: record.status === 'open' ? '下架' : '上架',
            key: 'toggleStatus',
            auth: ['room:status'],
          },
        ],
        select: (key: string) => {
          if (key === 'toggleStatus') handleToggleStatus(record);
        },
      });
    },
  });

  function addTable() {
    editData.value = null;
    showModal.value = true;
  }

  function handleEdit(record: RoomItem) {
    editData.value = record;
    showModal.value = true;
  }

  function handleDelete(record: RoomItem) {
    window['$dialog'].warning({
      title: '确认删除',
      content: `确定要删除自习室「${record.name}」吗？`,
      positiveText: '确认删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteRoom(record.id);
          window['$message'].success('删除成功');
          reloadTable();
        } catch {
          window['$message'].error('删除失败');
        }
      },
    });
  }

  function handleToggleStatus(record: RoomItem) {
    const newStatus = record.status === 'open' ? 'closed' : 'open';
    window['$dialog'].warning({
      title: '确认操作',
      content: `确定要${newStatus === 'open' ? '上架' : '下架'}自习室「${record.name}」吗？`,
      positiveText: '确认',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await toggleRoomStatus(record.id, newStatus);
          window['$message'].success(newStatus === 'open' ? '已上架' : '已下架');
          reloadTable();
        } catch {
          window['$message'].error('操作失败');
        }
      },
    });
  }

  function handleManageSeats(record: RoomItem) {
    router.push(`/room/list/${record.id}/seats`);
  }

  function handleSuccess() {
    showModal.value = false;
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
