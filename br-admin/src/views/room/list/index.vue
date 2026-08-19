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
            新建学习室
          </n-button>
        </template>
      </BasicTable>
    </n-card>
  </n-flex>
</template>

<script lang="ts" setup>
  import { h, onMounted, reactive, ref } from 'vue';
  import { useRouter } from 'vue-router';
  import { PlusOutlined } from '@vicons/antd';
  import { BasicTable, TableAction } from '@/components/Table';
  import { BasicForm, useForm } from '@/components/Form/index';
  import {
    deleteRoom,
    getCityList,
    getRoomList,
    toggleRoomStatus,
    type RoomItem,
  } from '@/api/room';
  import { toBasicTableResult } from '@/api/contracts/admin';
  import type { BusinessOption } from '../../business/shared/options';
  import { buildRoomSearchSchemas, buildRoomTableColumns } from './builders';

  const router = useRouter();
  const actionRef = ref();
  const columns = buildRoomTableColumns();

  const [register, { getFieldsValue, setProps }] = useForm({
    gridProps: { cols: '1 s:1 m:2 l:3 xl:4 2xl:4' },
    labelWidth: 80,
    schemas: buildRoomSearchSchemas([]),
  });

  onMounted(async () => {
    // 加载城市选项后刷新搜索表单
    try {
      const cities = await getCityList();
      const cityOptions: BusinessOption<number>[] = cities.map((city) => ({
        label: city.name,
        value: city.id,
      }));
      await setProps({ schemas: buildRoomSearchSchemas(cityOptions) });
    } catch {
      // 城市加载失败不阻断列表展示
    }
  });

  const loadDataTable = async (res: any) => {
    const formValues = getFieldsValue();
    const queryParams: Record<string, any> = { ...formValues, ...res };

    queryParams.page_size = queryParams.pageSize;
    delete queryParams.pageSize;

    if (!queryParams.status) delete queryParams.status;
    if (!queryParams.room_type) delete queryParams.room_type;
    if (!queryParams.city_id) delete queryParams.city_id;
    if (!queryParams.keyword) delete queryParams.keyword;

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
            // 仅学习室和综合室支持管理座位
            ifShow: ['study', 'comprehensive'].includes(record.room_type),
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
    router.push({ name: 'room_edit' });
  }

  function handleEdit(record: RoomItem) {
    router.push({ name: 'room_edit', params: { id: record.id } });
  }

  function handleDelete(record: RoomItem) {
    window['$dialog'].warning({
      title: '确认删除',
      content: `确定要删除学习室「${record.name}」吗？`,
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
      content: `确定要${newStatus === 'open' ? '上架' : '下架'}学习室「${record.name}」吗？`,
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
