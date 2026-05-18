<template>
  <n-flex vertical>
    <n-card :bordered="false">
      <BasicForm @register="register" @submit="handleSubmit" @reset="handleReset" />
    </n-card>
    <n-card :bordered="false">
      <BasicTable
        :columns="columns"
        :request="loadDataTable"
        :row-key="(row: RoomItem) => row.id"
        ref="actionRef"
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
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, FormSchema, useForm } from '@/components/Form/index';
  import { PlusOutlined } from '@vicons/antd';
  import { getRoomList, deleteRoom, toggleRoomStatus, type RoomItem } from '@/api/room';
  import { columns } from './columns';
  import RoomEditModal from './RoomEditModal.vue';

  const router = useRouter();

  const schemas: FormSchema[] = [
    {
      field: 'keyword',
      component: 'NInput',
      label: '关键词',
      componentProps: { placeholder: '搜索名称或地址' },
    },
    {
      field: 'status',
      component: 'NSelect',
      label: '状态',
      componentProps: {
        placeholder: '全部',
        options: [
          { label: '全部', value: '' },
          { label: '营业中', value: 'open' },
          { label: '已关闭', value: 'closed' },
        ],
      },
    },
  ];

  const actionRef = ref();
  const showModal = ref(false);
  const editData = ref<RoomItem | null>(null);

  const [register, { getFieldsValue }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas,
  });

  const loadDataTable = async (res: any) => {
    const formValues = getFieldsValue();
    const queryParams: Record<string, any> = { ...formValues, ...res };

    // Convert camelCase to snake_case for API
    queryParams.page_size = queryParams.pageSize;
    delete queryParams.pageSize;

    // Remove empty status filter
    if (queryParams.status === '' || queryParams.status === undefined) {
      delete queryParams.status;
    }

    const result = await getRoomList(queryParams);
    return {
      list: result.items,
      itemCount: result.total,
      pageCount: Math.ceil(result.total / queryParams.page_size) || 1,
      page: result.page,
    };
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
        ],
        dropDownActions: [
          {
            label: record.status === 'open' ? '下架' : '上架',
            key: 'toggleStatus',
            auth: ['room:status'],
          },
          {
            label: '管理座位',
            key: 'manageSeats',
            auth: ['seat:view'],
          },
        ],
        select: (key: string) => {
          if (key === 'toggleStatus') {
            handleToggleStatus(record);
          } else if (key === 'manageSeats') {
            handleManageSeats(record);
          }
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
